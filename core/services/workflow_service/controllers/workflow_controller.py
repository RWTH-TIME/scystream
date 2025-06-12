import os
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import networkx as nx
from uuid import UUID
import json
import logging
import time
import yaml
import subprocess
import tempfile
from sqlalchemy.orm import Session

from collections import defaultdict
from utils.database.session_injector import get_database
from pydantic import ValidationError
from git import Repo
from utils.config.environment import ENV
from utils.data.file_handling import bulk_presigned_urls_from_ios
from services.workflow_service.controllers.project_controller \
    import read_project
from services.workflow_service.controllers import compute_block_controller
from services.workflow_service.schemas.workflow import (
    WorfklowValidationError,
    WorkflowTemplate,
    WorkflowEnvsWithBlockInfo,
)
from services.workflow_service.models.block import (
    Block,
    block_dependencies
)
from services.workflow_service.models.input_output import (
    InputOutput,
    InputOutputType
)
from services.workflow_service.schemas.compute_block import (
    BlockStatus,
    ConfigType
)

from airflow_client.client import ApiClient, Configuration, ApiException
from airflow_client.client.api.dag_run_api import DAGRunApi
from airflow_client.client.model.list_dag_runs_form import ListDagRunsForm
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.api.dag_api import DAGApi
from airflow_client.client.api.task_instance_api import TaskInstanceApi
from airflow_client.client.model.dag import DAG

DAG_DIRECTORY = ENV.AIRFLOW_DAG_DIR
airflow_config = Configuration(
    host=ENV.AIRFLOW_HOST,
    username=ENV.AIRFLOW_USER,
    password=ENV.AIRFLOW_PASS
)


def _project_id_to_dag_id(pi: UUID | str) -> str:
    return f"dag_{str(pi).replace("-", "_")}"


def dag_id_to_project_id(di: str) -> str:
    return di[4:].replace("_", "-")


def _task_id_to_cb_id(ti: str) -> str:
    return ti[5:].replace("_", "-")


def _cb_id_to_task_id(ci: UUID | str) -> str:
    return f"task_{str(ci).replace('-', '_')}"


def parse_configs(configs):
    return {k: json.dumps(v) if isinstance(v, list) else str(v)
            for k, v in configs.items()}


def get_workflow_template_by_identifier(identifier: str) -> WorkflowTemplate:
    """
    Fetches a workflow template YAML file from the Template repo specified in
    ENV finds it by its identifier, which is the file name
    (e.g., 'template.yaml').
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            Repo.clone_from(
                ENV.WORKFLOW_TEMPLATE_REPO,
                tmpdir,
                multi_options=[
                    "--depth=1",
                    "-c",
                    "core.sshCommand=ssh -o StrictHostKeyChecking=no"
                ],
                allow_unsafe_options=True
            )

            file_path = os.path.join(tmpdir, identifier)

            if not os.path.isfile(file_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Template file '{
                        identifier}' not found in repository."
                )

            with open(file_path, "r") as f:
                data = yaml.safe_load(f) or {}
                data["file_identifier"] = identifier
                return WorkflowTemplate.model_validate(data)

        except subprocess.CalledProcessError as e:
            logging.error(f"Could not clone the repository {
                          ENV.WORKFLOW_TEMPLATE_REPO}: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Couldn't clone the repository: {
                    ENV.WORKFLOW_TEMPLATE_REPO}"
            )
        except ValidationError as ve:
            logging.warning(f"Validation failed for {identifier}: {ve}")
            raise HTTPException(
                status_code=422,
                detail=f"Template validation failed: {ve}"
            )


def _get_workflow_templates_from_repo(repo_url: str) -> list[WorkflowTemplate]:
    logging.debug(f"Cloning WorkflowTemplate Repo form: {repo_url}")
    templates: WorkflowTemplate = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            Repo.clone_from(
                repo_url,
                tmpdir,
                multi_options=[
                    "--depth=1",
                    "-c",
                    "core.sshCommand=ssh -o StrictHostKeyChecking=no"
                ],
                allow_unsafe_options=True
            )

            for file in os.listdir(tmpdir):
                if not file.endswith((".yaml", ".yml")):
                    continue

                file_path = os.path.join(tmpdir, file)
                try:
                    with open(file_path, "r") as f:
                        data = yaml.safe_load(f) or {}
                        data["file_identifier"] = file
                        template = WorkflowTemplate.model_validate(data)
                        templates.append(template)
                except ValidationError as ve:
                    logging.warning(f"Validation failed for {file_path}: {ve}")
                    raise ve
        except subprocess.CalledProcessError as e:
            logging.error(f"Could not clone the repository {repo_url}: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Couldn't clone the repository: {repo_url}"
            )
        except HTTPException as e:
            raise e

    return templates


def _group_ios_by_block(
    ios: list[InputOutput],
    block_by_entry_id: dict[UUID, Block]
) -> dict[UUID, list[InputOutput]]:
    io_map = defaultdict(list)
    for io in ios:
        block = block_by_entry_id.get(io.entrypoint_uuid)
        if block:
            io_map[block.uuid].append(io)
    return io_map


def _filter_unconfigured(config: dict | None) -> dict | None:
    return {
        k: v for k, v in (config or {}).items()
        if v in (None, "", [], {})
    } or None


def _get_unconfigured_envs(block: Block) -> ConfigType | None:
    return _filter_unconfigured(block.selected_entrypoint.envs)


def _get_unconfigured_ios(ios: list[InputOutput]) -> list[InputOutput]:
    result = []

    for io in ios:
        unconfigured_fields = _filter_unconfigured(io.config)
        result.append(InputOutput(
            uuid=io.uuid,
            type=io.type,
            name=io.name,
            data_type=io.data_type,
            description=io.description,
            config=unconfigured_fields,
            entrypoint_uuid=io.entrypoint_uuid
        ))

    return result


def get_workflow_configurations(project_id: UUID) -> tuple[
    list[WorkflowEnvsWithBlockInfo],  # Missing envs for block
    list[InputOutput],  # Workflow Inputs
    list[InputOutput],  # Intermediate IOs
    list[InputOutput],  # Workflow Outputs
    dict[UUID, Block]  # Block by Entrypoint
]:
    """
    Returns the Configurations for the Workflow.

    Returns:
        dict[UUID, ConfigType]: All ENVs WITH MISSING configs of the Blocks
        list[InputOutput]: Inputs of the Workflow with unset configs if there
            are any -> All inputs of blocks that dont have an
            Upstream Block
        list[InputOutput]: Inputs & Outputs of Blocks WITH MISSING
            configurations (set configurations are not returned)
        list[InputOutput]: Outputs of the Workflow -> All outputs of
            blocks that dont have an Downstream Block with unset configs if
            there are any.
        dict[UUID, Block]: dict mapping EntryID to Block
    """
    db: Session = next(get_database())

    blocks: list[Block] = compute_block_controller.\
        get_compute_blocks_by_project(
            project_id
    )
    block_by_entry_id = {
        b.selected_entrypoint_uuid: b for b in blocks
    }

    entry_ids = list(block_by_entry_id.keys())
    ios: list[InputOutput] = db.query(InputOutput).filter(
        InputOutput.entrypoint_uuid.in_(entry_ids)
    ).all()
    presigned_urls = bulk_presigned_urls_from_ios(ios)

    io_map = _group_ios_by_block(ios, block_by_entry_id)
    deps = db.execute(block_dependencies.select()).fetchall()
    has_upstream = {
        dep.downstream_block_uuid for dep in deps
    }
    has_downstream = {
        dep.upstream_block_uuid for dep in deps
    }

    unconfigured_envs = []
    inputs = []
    outputs = []
    intermediates = []

    for block in blocks:
        if (block_envs := _get_unconfigured_envs(block)) is not None:
            unconfigured_envs.append(WorkflowEnvsWithBlockInfo(
                block_uuid=block.uuid,
                block_custom_name=block.custom_name,
                envs=block_envs
            )
            )

        unconfigured_ios = _get_unconfigured_ios(
            io_map.get(block.uuid, [])
        )

        # Workflow Inputs
        if block.uuid not in has_upstream:
            inputs += [io for io in unconfigured_ios if io.type ==
                       InputOutputType.INPUT]

        # Workflow Outputs
        if block.uuid not in has_downstream:
            outputs += [io for io in unconfigured_ios if io.type ==
                        InputOutputType.OUTPUT]

        # Intermediates
        if block.uuid in has_upstream and block.uuid in has_downstream:
            intermediates += unconfigured_ios

    return (
        unconfigured_envs,
        inputs,
        intermediates,
        outputs,
        presigned_urls,
        block_by_entry_id
    )


def get_workflow_templates() -> list[WorkflowTemplate]:
    templates = _get_workflow_templates_from_repo(ENV.WORKFLOW_TEMPLATE_REPO)
    return templates


def create_graph(project):
    graph = nx.DiGraph()

    for block in project.blocks:
        entrypoint = block.selected_entrypoint
        configs = [io.config for io in entrypoint.input_outputs]
        merged_configs = {
            **parse_configs(entrypoint.envs),
            **{k: v for d in configs for k, v in parse_configs(d).items()}
        }

        graph.add_node(block.uuid, **{
            "uuid": block.uuid,
            "name": block.name,
            "image": block.docker_image,
            "entry_name": block.selected_entrypoint.name,
            "environment": merged_configs,
        })

    # Add edges (dependencies)
    for block in project.blocks:
        for upstream in block.upstream_blocks:
            graph.add_edge(upstream.uuid, block.uuid)

    # Ensure the graph is a valid DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise HTTPException(
            status_code=400, detail="The project is not acyclic.")

    if not nx.is_connected(graph.to_undirected()):
        raise HTTPException(
            status_code=400, detail="Not all compute blocks are connected."
        )

    return graph


def init_templates():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "..", "templates")

    env = Environment(loader=FileSystemLoader(templates_dir))
    return {
        "dag": env.get_template("dag_base.py.j2"),
        "algorithm": env.get_template("algorithm_docker.py.j2"),
        "dependency": env.get_template("dependency.py.j2"),
    }


def generate_dag_code(graph, templates, dag_id, project_uuid):
    parts = [templates["dag"].render(dag_id=dag_id)]

    # Convert to Airflow-compatible representation
    for node, data in graph.nodes(data=True):
        task_id = _cb_id_to_task_id(node)
        parts.append(templates["algorithm"].render(
            task_id=task_id,
            image=data["image"],
            name=data["name"],
            uuid=data["uuid"],
            entry_name=data["entry_name"],
            project=str(project_uuid),
            environment=data["environment"],
            local_storage_path_external="/tmp/scystream-data",
        ))

    # Render dependencies
    parts.extend([
        templates["dependency"].render(
            from_task=_cb_id_to_task_id(from_task),
            to_task=_cb_id_to_task_id(to_task)
        )
        for from_task, to_task in graph.edges
    ])

    return "\n".join(parts)


def save_dag_to_file(dag_code, dag_id):
    os.makedirs(DAG_DIRECTORY, exist_ok=True)
    filename = os.path.join(DAG_DIRECTORY, f"{dag_id}.py")

    with open(filename, "w") as f:
        f.write(dag_code)

    return filename


def validate_value(value: str | list | None) -> bool:
    return value is None or value == "" or value == []


def validate_workflow(project_uuid: UUID):
    """
    Checks:
        - Are there compute blocks?
        - Are all envs and configs set?
    """
    blocks_in_project = compute_block_controller.get_compute_blocks_by_project(
        project_uuid
    )

    if len(blocks_in_project) == 0:
        raise HTTPException(
            status_code=422, detail="Project is missing blocks.")

    # Collect all inputs & outputs
    confs = {}
    missing_values = {}

    for block in blocks_in_project:
        block_id = block.uuid

        for ek, ev in block.selected_entrypoint.envs.items():
            confs[ek] = ev
            if validate_value(ev):
                missing_values.setdefault(str(block_id), []).append(ek)

        for io in block.selected_entrypoint.input_outputs:
            for ck, cv in io.config.items():
                confs[ck] = cv
                if validate_value(cv):
                    missing_values.setdefault(str(block_id), []).append(ck)

    if missing_values:
        raise HTTPException(
            status_code=422, detail=WorfklowValidationError(
                project_id=str(project_uuid),
                missing_configs=missing_values
            ).dict()
        )


def wait_for_dag_registration(
        dag_id: str,
        timeout: int = 10,
        wait: float = 0.5
) -> bool:
    with ApiClient(airflow_config) as api_client:
        api = DAGApi(api_client)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                api.get_dag(dag_id)
                return True
            except ApiException as e:
                if e.status == 404:
                    time.sleep(wait)
                else:
                    raise e

    return False


def translate_project_to_dag(project_uuid: UUID) -> str:
    """
    Parses a project and its blocks into a DAG, validates it, and saves it.
    """
    project = read_project(project_uuid)  # Ensures project is set
    graph = create_graph(project)
    templates = init_templates()
    dag_id = _project_id_to_dag_id(project_uuid)
    dag_code = generate_dag_code(graph, templates, dag_id, project_uuid)
    save_dag_to_file(dag_code, dag_id)
    return dag_id


def unpause_dag(dag_id: str, is_paused: bool = False):
    with ApiClient(airflow_config) as api_client:
        api = DAGApi(api_client)
        try:
            api.patch_dag(dag_id, DAG(is_paused=is_paused))
        except ApiException as e:
            logging.error(f"Exception while trying to unpause dag {e}")
            raise e


def trigger_workflow_run(dag_id: str):
    with ApiClient(airflow_config) as api_client:
        unpause_dag(dag_id)
        api = DAGRunApi(api_client)

        try:
            api.post_dag_run(dag_id, DAGRun())
        except ApiException as e:
            logging.error(f"Execption while trying to start the workflow {e}")
            raise e


def get_all_dags():
    with ApiClient(airflow_config) as api_client:
        api = DAGApi(api_client)

        try:
            dags = api.get_dags()
            return [d.dag_id for d in dags.dags]
        except ApiException as e:
            logging.error(
                f"Exception while trying to query the DAGs from airflow: {e}")
            raise e


def last_dag_run_overview(dag_ids: list[str]) -> dict:
    with ApiClient(airflow_config) as api_client:
        api = DAGRunApi(api_client)
        most_recent_runs = {}

        try:
            all_runs = api.get_dag_runs_batch(ListDagRunsForm(
                dag_ids=dag_ids,
                order_by="execution_date",
                page_limit=10000,
            ))
            # We only select the newest runs per DAG
            # Unfortunately airflow_client does not offer this out of the box
            for run in all_runs["dag_runs"]:
                dag_id = run["dag_id"]
                if (
                    dag_id not in most_recent_runs or
                    run["execution_date"] >
                    most_recent_runs[dag_id]["execution_date"]
                ):
                    most_recent_runs[dag_id] = run
        except ApiException as e:
            logging.error(
                f"Exception while trying to get DAGs statuses from airflow: {
                    e}"
            )
            raise e

        return most_recent_runs


def get_latest_dag_run(project_id: UUID) -> str | None:
    dag_id = _project_id_to_dag_id(project_id)
    with ApiClient(airflow_config) as api_client:
        api = DAGRunApi(api_client)

        try:
            dag_runs = api.get_dag_runs(
                dag_id, limit=1, order_by="-execution_date").dag_runs

            if dag_runs:
                return dag_runs[0].dag_run_id
            else:
                logging.debug(f"No DAG runs found for DAG {dag_id}")
                return None
        except ApiException as e:
            logging.error(f"Error fetching DAG runs for {dag_id}: {e}")
            raise e


def delete_dag_from_airflow(project_id: UUID) -> str | None:
    dag_id = _project_id_to_dag_id(project_id)
    with ApiClient(airflow_config) as api_client:
        api = DAGApi(api_client)

        try:
            os.remove(os.path.join(DAG_DIRECTORY, f"{dag_id}.py"))
            api.delete_dag(
                dag_id
            )
        except OSError:
            # The Deleting of the file might fail, because it might not yet be
            # existant
            logging.error("Error deleting DAG file from directory")
        except ApiException as e:
            logging.error(f"Error deleting DAG {dag_id} from airflow: {e}")
            raise e


def dag_status(project_id: UUID) -> dict:
    dag_id = _project_id_to_dag_id(project_id)
    latest_run_id = get_latest_dag_run(project_id)

    if not latest_run_id:
        return {}

    with ApiClient(airflow_config) as api_client:
        api = TaskInstanceApi(api_client)

        task_statuses = {}

        try:
            tasks = api.get_task_instances(
                dag_id,
                latest_run_id
            ).task_instances

            for task in tasks:
                cb_id = _task_id_to_cb_id(task.task_id)
                task_statuses[cb_id] = BlockStatus.from_airflow_state(
                    task.state.value if task.state else None
                ).value

            return task_statuses
        except ApiException as e:
            logging.error(
                f"""
            Exception while trying to get Compute Block statuses
            per project from airflow: {e}
            """
            )
            raise e
