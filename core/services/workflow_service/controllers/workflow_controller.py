import os
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import networkx as nx
from uuid import UUID
import json
import logging

from utils.config.environment import ENV
from services.workflow_service.controllers.project_controller \
    import read_project
from services.workflow_service.controllers import compute_block_controller
from services.workflow_service.schemas.workflow import WorfklowValidationError
from airflow_client.client import ApiClient, Configuration, ApiException
from airflow_client.client.api.dag_run_api import DAGRunApi
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.api.dag_api import DAGApi
from airflow_client.client.model.dag import DAG

DAG_DIRECTORY = ENV.AIRFLOW_DAG_DIR
airflow_config = Configuration(
    host=ENV.AIRFLOW_HOST,
    username=ENV.AIRFLOW_USER,
    password=ENV.AIRFLOW_PASS
)

# TODO: Logging


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


def gen_dag_code(graph, templates, dag_id, project_uuid):
    parts = [templates["dag"].render(dag_id=dag_id)]

    # Convert to Airflow-compatible representation
    for node, data in graph.nodes(data=True):
        task_id = f"task_{str(node).replace('-', '_')}"
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
            from_task=f"task_{str(from_task).replace('-', '_')}",
            to_task=f"task_{str(to_task).replace('-', '_')}"
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


def validate_value(value: str) -> bool:
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


def translate_project_to_dag(project_uuid: UUID) -> str:
    """
    Parses a project and its blocks into a DAG, validates it, and saves it.
    """
    project = read_project(project_uuid)  # Ensures project is set
    graph = create_graph(project)
    templates = init_templates()
    dag_id = f"dag_{str(project_uuid).replace('-', '_')}"
    dag_code = gen_dag_code(graph, templates, dag_id, project_uuid)
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


# TODO: STOP workflow_run -> Abort run
# TODO: Get workflow status
# TODO: Get compute block status
