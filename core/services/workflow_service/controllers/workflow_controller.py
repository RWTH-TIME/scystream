import os
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import networkx as nx
from uuid import UUID
import json
import logging
import time

from utils.config.environment import ENV
from services.workflow_service.controllers.project_controller \
    import read_project
from services.workflow_service.controllers import compute_block_controller
from services.workflow_service.schemas.workflow import (
    WorfklowValidationError,
    BlockStatus
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


def _dag_id_to_project_id(di: str) -> str:
    return di.replace("dag_", "").replace("_", "-")


def _task_id_to_cb_id(ti: str) -> str:
    return ti.replace("task_", "").replace("_", "-")


def _cb_id_to_task_id(ci: UUID | str) -> str:
    return f"task_{str(ci).replace('-', '_')}"


def parse_configs(configs):
    return {k: json.dumps(v) if isinstance(v, list) else str(v)
            for k, v in configs.items()}


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
                order_by="execution_date"
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
        except OSError as e:
            logging.error("Error deleting DAG file from directory")
            raise e
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
