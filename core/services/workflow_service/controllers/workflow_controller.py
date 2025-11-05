from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from typing import TYPE_CHECKING

import networkx as nx
from airflow_client.client.api.dag_api import DAGApi
from airflow_client.client.api.dag_run_api import DagRunApi
from airflow_client.client.api.task_instance_api import TaskInstanceApi
from airflow_client.client.api_client import ApiClient
from airflow_client.client.configuration import Configuration
from airflow_client.client.exceptions import ApiException, NotFoundException
from airflow_client.client.models.dag_patch_body import DAGPatchBody
from airflow_client.client.models.dag_runs_batch_body import (
    DAGRunsBatchBody,
)
from airflow_client.client.models.trigger_dag_run_post_body import (
    TriggerDAGRunPostBody,
)
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
from services.workflow_service.controllers import (
    compute_block_controller,
    template_controller,
)
from services.workflow_service.controllers.project_controller import (
    read_project,
)
from services.workflow_service.models.block import (
    Block,
    block_dependencies,
)
from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
    InputOutputType,
)
from services.workflow_service.schemas.compute_block import (
    BlockStatus,
    ConfigType,
)
from services.workflow_service.schemas.workflow import (
    WorfklowValidationError,
    WorkflowEnvsWithBlockInfo,
    WorkflowTemplate,
)
from utils.config.environment import ENV
from utils.data.file_handling import bulk_presigned_urls_from_ios
from utils.database.session_injector import get_database
import requests
from pydantic import BaseModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

DAG_DIRECTORY = ENV.AIRFLOW_DAG_DIR


class AirflowAccessTokenResponse(BaseModel):
    access_token: str


def get_airflow_client_access_token(
    host: str,
    username: str,
    password: str,
) -> str:
    url = f"{host}/auth/token"
    payload = {
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        raise RuntimeError(f"Failed to get access token: \
            {response.status_code} {response.text}")
    response_success = AirflowAccessTokenResponse(**response.json())
    return response_success.access_token


def get_airflow_config() -> Configuration:
    airflow_config = Configuration(
        host=ENV.AIRFLOW_HOST,
    )

    airflow_config.access_token = get_airflow_client_access_token(
        host=airflow_config.host,
        username=ENV.AIRFLOW_USER,
        password=ENV.AIRFLOW_PASS,
    )

    return airflow_config


def _project_id_to_dag_id(pi: UUID | str) -> str:
    return f"dag_{str(pi).replace("-", "_")}"


def dag_id_to_project_id(di: str) -> str:
    return di[4:].replace("_", "-")


def _task_id_to_cb_id(ti: str) -> str:
    return ti[5:].replace("_", "-")


def _cb_id_to_task_id(ci: UUID | str) -> str:
    return f"task_{str(ci).replace('-', '_')}"


def parse_configs(configs):
    return {
        k: json.dumps(v) if isinstance(v, list) else str(v)
        for k, v in configs.items()
    }


def _group_ios_by_block(
    ios: list[InputOutput],
    block_by_entry_id: dict[UUID, Block],
) -> dict[UUID, list[InputOutput]]:
    io_map = defaultdict(list)
    for io in ios:
        block = block_by_entry_id.get(io.entrypoint_uuid)
        if block:
            io_map[block.uuid].append(io)
    return io_map


def _filter_unconfigured(config: dict | None) -> dict | None:
    return {
        k: v for k, v in (config or {}).items() if v in (None, "", [], {})
    } or None


def _get_unconfigured_envs(block: Block) -> ConfigType | None:
    return _filter_unconfigured(block.selected_entrypoint.envs)


def _get_unconfigured_ios(ios: list[InputOutput]) -> list[InputOutput]:
    """Filters the unconfigured config entrys from the passed ios and returns
    io objects."""
    result = []

    for io in ios:
        unconfigured_fields = _filter_unconfigured(io.config)
        result.append(
            InputOutput(
                uuid=io.uuid,
                type=io.type,
                name=io.name,
                data_type=io.data_type,
                description=io.description,
                config=unconfigured_fields,
                entrypoint_uuid=io.entrypoint_uuid,
            ),
        )

    return result


def get_workflow_configurations(project_id: UUID) -> tuple[
    list[WorkflowEnvsWithBlockInfo],
    list[InputOutput],  # Workflow Inputs
    list[InputOutput],  # Intermediates
    list[InputOutput],  # Workflow Outputs
    dict[UUID, Block],  # Block by Entrypoint
]:
    """Returns categorized I/O configurations and unconfigured envs for a
    workflow.

    Breakdown of returned values:

    1. Unconfigured Envs:
       - List of environment variables for each block that are required but
       not configured.

    2. Workflow Inputs:
       - All inputs of blocks that do NOT have any upstream dependencies.
       - These represent the entry points of data into the workflow.

    3. Intermediates:
       - Includes I/Os used internally between blocks.
       - Specifically:
         - Inputs that are unconnected (not wired from any upstream block).
         - Inputs that ARE connected AND:
             - Their data_type is CUSTOM, AND
             - They are not fully configured (i.e., have missing config values)
             (these are inputs that we cannot autoconfigure, therefore
              configuring the upstream output might not be enough)
         - All outputs that have a downstream connection.
            (to allow the user to download intermediate results)

    4. Workflow Outputs:
       - All outputs of blocks that do NOT have any downstream dependencies.
       - These represent the final results produced by the workflow.

    5. Block by Entrypoint:
       - A dictionary mapping the entrypoint UUID of each block to the actual
       Block instance.

    Notes:
    - An InputOutput is considered "fully configured" if the config dict is
    empty after filtering out set keys
    - Presigned URLs for FILE-type I/Os are included in the
    input/output objects.

    Args:
        project_id (UUID): The project ID for which the workflow configuration
        is retrieved.

    Returns:
        Tuple containing:
            - List of WorkflowEnvsWithBlockInfo
            - List of InputOutput for workflow inputs
            - List of InputOutput for intermediate values
            - List of InputOutput for workflow outputs
            - Dictionary mapping entrypoint UUIDs to Block instances
    """
    db: Session = next(get_database())

    # 1. Load blocks
    blocks = compute_block_controller.get_compute_blocks_by_project(project_id)
    block_by_entry_id = {b.selected_entrypoint_uuid: b for b in blocks}
    entry_ids = list(block_by_entry_id.keys())

    # 2. Load IOs
    ios = (
        db.query(InputOutput)
        .filter(
            InputOutput.entrypoint_uuid.in_(entry_ids),
        )
        .all()
    )
    presigned_urls = bulk_presigned_urls_from_ios(ios)
    io_map = _group_ios_by_block(ios, block_by_entry_id)

    # 3. Load dependencies
    deps = db.execute(block_dependencies.select()).fetchall()
    has_upstream = {dep.downstream_block_uuid for dep in deps}
    has_downstream = {dep.upstream_block_uuid for dep in deps}
    connected_input_uuids = {dep.downstream_input_uuid for dep in deps}

    # 4. Prepare result containers
    unconfigured_envs = []
    workflow_inputs = []
    workflow_outputs = []
    intermediates = []

    for block in blocks:
        # Unconfigured ENV blocks
        if (block_envs := _get_unconfigured_envs(block)) is not None:
            unconfigured_envs.append(
                WorkflowEnvsWithBlockInfo(
                    block_uuid=block.uuid,
                    block_custom_name=block.custom_name,
                    envs=block_envs,
                ),
            )

        # Determine connections
        upstream = block.uuid in has_upstream
        downstream = block.uuid in has_downstream

        # Get only unconfigured IOs for this block
        unconfigured_ios = _get_unconfigured_ios(io_map.get(block.uuid, []))

        for io in unconfigured_ios:
            if io.type == InputOutputType.INPUT:
                if not upstream:
                    workflow_inputs.append(io)
                elif io.uuid not in connected_input_uuids or (
                    io.data_type == DataType.CUSTOM and io.config
                ):
                    intermediates.append(io)
            elif io.type == InputOutputType.OUTPUT:
                if not downstream:
                    workflow_outputs.append(io)
                else:
                    intermediates.append(io)

    return (
        unconfigured_envs,
        workflow_inputs,
        intermediates,
        workflow_outputs,
        presigned_urls,
        block_by_entry_id,
    )


def get_workflow_templates() -> dict[str, list[WorkflowTemplate]]:
    templates = template_controller.get_workflow_templates_from_repo(
        ENV.WORKFLOW_TEMPLATE_REPO,
    )

    grouped = defaultdict(list)

    for tpl in templates:
        if not tpl.pipeline.tags:
            grouped["untagged"].append(tpl)
        else:
            for tag in tpl.pipeline.tags:
                grouped[tag].append(tpl)
    return dict(grouped)


def create_graph(project):
    graph = nx.DiGraph()

    for block in project.blocks:
        entrypoint = block.selected_entrypoint
        configs = [io.config for io in entrypoint.input_outputs]
        merged_configs = {
            **parse_configs(entrypoint.envs),
            **{k: v for d in configs for k, v in parse_configs(d).items()},
        }

        graph.add_node(
            block.uuid,
            uuid=block.uuid,
            name=block.name,
            image=block.docker_image,
            entry_name=block.selected_entrypoint.name,
            environment=merged_configs,
        )

    # Add edges (dependencies)
    for block in project.blocks:
        for upstream in block.upstream_blocks:
            graph.add_edge(upstream.uuid, block.uuid)

    # Ensure the graph is a valid DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise HTTPException(
            status_code=400,
            detail="The project is not acyclic.",
        )

    if not nx.is_connected(graph.to_undirected()):
        raise HTTPException(
            status_code=400,
            detail="Not all compute blocks are connected.",
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
        parts.append(
            templates["algorithm"].render(
                task_id=task_id,
                image=data["image"],
                name=data["name"],
                uuid=data["uuid"],
                entry_name=data["entry_name"],
                project=str(project_uuid),
                environment=data["environment"],
                local_storage_path_external="/tmp/scystream-data",
                network_mode=ENV.CB_NETWORK_MODE,
            ),
        )

    # Render dependencies
    parts.extend(
        [
            templates["dependency"].render(
                from_task=_cb_id_to_task_id(from_task),
                to_task=_cb_id_to_task_id(to_task),
            )
            for from_task, to_task in graph.edges
        ],
    )

    return "\n".join(parts)


def save_dag_to_file(dag_code, dag_id):
    os.makedirs(DAG_DIRECTORY, exist_ok=True)
    filename = os.path.join(DAG_DIRECTORY, f"{dag_id}.py")

    with open(filename, "w") as f:
        f.write(dag_code)

    return filename


def validate_value(value: str | list | None) -> bool:
    return value is None or value in ("", [])


def validate_workflow(project_uuid: UUID) -> None:
    """Checks:
    - Are there compute blocks?
    - Are all envs and configs set?
    """
    blocks_in_project = compute_block_controller.get_compute_blocks_by_project(
        project_uuid,
    )

    if len(blocks_in_project) == 0:
        raise HTTPException(
            status_code=422,
            detail="Project is missing blocks.",
        )

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
            status_code=422,
            detail=WorfklowValidationError(
                project_id=str(project_uuid),
                missing_configs=missing_values,
            ).model_dump(),
        )


def wait_for_dag_registration(
    dag_id: str,
    timeout: int = 10,
    wait: float = 0.5,
) -> bool:
    with ApiClient(get_airflow_config()) as api_client:
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
                    raise

    return False


def translate_project_to_dag(project_uuid: UUID) -> str:
    """Parses a project and its blocks into a DAG, validates it, and saves
    it."""
    project = read_project(project_uuid)  # Ensures project is set
    graph = create_graph(project)
    templates = init_templates()
    dag_id = _project_id_to_dag_id(project_uuid)
    dag_code = generate_dag_code(graph, templates, dag_id, project_uuid)
    save_dag_to_file(dag_code, dag_id)
    return dag_id


def unpause_dag(dag_id: str, is_paused: bool = False) -> None:
    with ApiClient(get_airflow_config()) as api_client:
        api = DAGApi(api_client)
        try:
            api.patch_dag(dag_id, DAGPatchBody(is_paused=is_paused))
        except ApiException as e:
            logging.exception(f"Exception while trying to unpause dag {e}")
            raise


def trigger_workflow_run(dag_id: str) -> None:
    with ApiClient(get_airflow_config()) as api_client:
        unpause_dag(dag_id)
        api = DagRunApi(api_client)

        try:
            api.trigger_dag_run(dag_id, TriggerDAGRunPostBody())
        except ApiException as e:
            logging.exception(
                f"Execption while trying to start the workflow {e}",
            )
            raise


def get_all_dags():
    with ApiClient(get_airflow_config()) as api_client:
        api = DAGApi(api_client)

        try:
            dags = api.get_dags()
            return [d.dag_id for d in dags.dags]
        except ApiException as e:
            logging.exception(
                f"Exception while trying to query the DAGs from airflow: {e}",
            )
            raise


def last_dag_run_overview(dag_ids: list[str]) -> dict:
    with ApiClient(get_airflow_config()) as api_client:
        api = DagRunApi(api_client)
        most_recent_runs = {}

        # TODO: refactor this method. Its way to strong querying all the dag
        # and their batch runs without sql limitations
        for dag_id in dag_ids:
            try:
                all_runs = api.get_list_dag_runs_batch(
                    "~",
                    DAGRunsBatchBody(
                        dag_ids=dag_ids,
                        page_limit=1000,
                    ),
                )

                # We only select the newest runs per DAG
                # Unfortunately airflow_client does not offer this
                # out of the box
                for run in all_runs.dag_runs:
                    dag_id = run.dag_id
                    if (
                        dag_id not in most_recent_runs
                        or run.start_date > most_recent_runs[dag_id].start_date
                    ):
                        most_recent_runs[dag_id] = run
            except ApiException as e:
                logging.exception(
                    f"Exception while trying to get DAGRuns from airflow: {e}",
                )
                raise

        return most_recent_runs


def get_latest_dag_run(project_id: UUID) -> str | None:
    dag_id = _project_id_to_dag_id(project_id)
    with ApiClient(get_airflow_config()) as api_client:
        api = DagRunApi(api_client)

        try:
            dag_runs = api.get_dag_runs(
                dag_id,
                limit=1,
                order_by="-logical_date"
            ).dag_runs

            if dag_runs:
                return dag_runs[0].dag_run_id
            logging.debug(f"No DAG runs found for DAG {dag_id}")
            return None
        except NotFoundException:
            return None
        except ApiException as e:
            logging.exception(f"Error fetching DAG runs for {dag_id}: {e}")
            raise


def delete_dag_from_airflow(project_id: UUID) -> str | None:
    dag_id = _project_id_to_dag_id(project_id)
    with ApiClient(get_airflow_config()) as api_client:
        api = DAGApi(api_client)

        try:
            os.remove(os.path.join(DAG_DIRECTORY, f"{dag_id}.py"))
            api.delete_dag(
                dag_id,
            )
        except OSError:
            # The Deleting of the file might fail, because it might not yet be
            # existant
            logging.exception("Error deleting DAG file from directory")
        except ApiException as e:
            logging.exception(f"Error deleting DAG {dag_id} from airflow: {e}")
            raise


def dag_status(project_id: UUID) -> dict:
    dag_id = _project_id_to_dag_id(project_id)
    latest_run_id = get_latest_dag_run(project_id)

    if not latest_run_id:
        return {}

    with ApiClient(get_airflow_config()) as api_client:
        api = TaskInstanceApi(api_client)

        task_statuses = {}

        try:
            tasks = api.get_task_instances(
                dag_id,
                latest_run_id,
            ).task_instances

            for task in tasks:
                cb_id = _task_id_to_cb_id(task.task_id)
                task_statuses[cb_id] = BlockStatus.from_airflow_state(
                    task.state.value if task.state else None,
                ).value

            return task_statuses
        except ApiException as e:
            logging.exception(
                f"""
            Exception while trying to get Compute Block statuses
            per project from airflow: {e}
            """,
            )
            raise
