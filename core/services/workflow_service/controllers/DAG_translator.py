import os
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import networkx as nx
from typing import Dict, Any

from project_controller import read_project
# from models.block import Block

# from enum import Enum
# from json import loads
# from typing import NoReturn, List, Optional

# from airflow_client.client import ApiClient, Configuration
# from airflow_client.client.api.dag_api import DAGApi
# from airflow_client.client.api.dag_run_api import DAGRunApi
# from airflow_client.client.exceptions import NotFoundException
# from airflow_client.client.model.dag import DAG
# from airflow_client.client.model.dag_run import DAGRun
# from airflow_client.client.model.dag_state import DagState


def translate_project_to_dag(project_uuid: str) -> Dict[str, Any]:
    """
    Parses a project and its blocks into a DAG and validates it.

    :param project_uuid: UUID of the project to parse.
    :param db: SQLAlchemy database session.
    """
    # Query the project
    project = read_project(project_uuid)

    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes (tasks)
    for block in project.blocks:
        graph.add_node(block.uuid, **{
            "name": block.name,
            "type": block.block_type.value,
            "parameters": block.parameters,
            "priority": block.priority_weight,
            "retries": block.retries,
            "retry_delay": block.retry_delay,
            "environment": block.environment,
            "schedule_interval": block.schedule_interval,
        })

    # Add edges (dependencies)
    for block in project.blocks:
        for upstream in block.upstream_blocks:
            upstream_task_id = f"task_{str(upstream.uuid).replace('-', '')}"
            current_task_id = f"task_{str(block.uuid).replace('-', '')}"
            graph.add_edge(upstream_task_id, current_task_id)

    # Ensure the graph is a DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise HTTPException(
            status_code=400,
            detail="The project is not acyclic."
            )

    # Initialize Jinja2 environment
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    templates_dir = os.path.join(  # Path to the templates
        base_dir, "..", "templates"
        )

    env = Environment(loader=FileSystemLoader(templates_dir))
    dag_template = env.get_template("dag_base.py.j2")
    algorithm_template = env.get_template("algorithm_docker.py.j2")
    dependency_template = env.get_template("dependency.py.j2")

    # Generate Python DAG file
    parts = []
    parts = [dag_template.render(
        dag_id=f"dag_{project_uuid.replace('-', '_')}"
        )]
    dependencies = []

    # Convert to Airflow-compatible representation
    for node, data in graph.nodes(data=True):
        parts.append(
            algorithm_template.render(
                task_id=node,
                image="scystreamworker",
                name=data["name"],
                uuid=node.split("_", 1)[1],
                dependency="",
                project=str(project_uuid),
                # pipeline=str(project.pipeline_uuid),
                algorithm=data["type"],
                parameters=data["parameters"],
                local_storage_path_external="/tmp/scystream-data",
                container_name=project.container_name,
            )
        )

    for from_task, to_task in graph.edges:
        dependencies.append(dependency_template.render(
            from_task=from_task, to_task=to_task)
            )

    parts.extend(dependencies)

    # Write the generated DAG to a Python file
    filename = os.path.join(
        "~/airflow/dags/", f"dag_{project_uuid.replace('-', '_')}.py"
        )

    with open(filename, "w") as f:
        f.write("\n".join(parts))
