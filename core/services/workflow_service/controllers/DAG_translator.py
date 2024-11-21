import os
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from fastapi import HTTPException
import networkx as nx
from typing import Dict, Any

from models.project import Project
from config.environment import ConfigEntry


def parse_project_to_dag(project_uuid: str, db: Session) -> None:
    """
    Parses a project and its blocks into a DAG representation and writes it to a Python file.

    :param project_uuid: UUID of the project to parse.
    :param db: SQLAlchemy database session.
    """
    # Query the project
    project = db.query(Project).filter_by(uuid=project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Initialize Jinja2 environment
    env = Environment(loader=FileSystemLoader("templates"))
    dag_template = env.get_template("dag_base.py.j2")
    algorithm_template = env.get_template("algorithm_docker.py.j2")
    dependency_template = env.get_template("dependency.py.j2")

    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes (tasks)
    for block in project.blocks:
        task_id = f"task_{str(block.uuid).replace('-', '')}"
        graph.add_node(task_id, **{
            "name": block.name,
            "type": block.block_type.value,
            "parameters": block.parameters,
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

    # Generate Python DAG file
    parts = [dag_template.render(dag_id=f"dag_{project_uuid.replace('-', '_')}")]
    dependencies = []

    # Convert to Airflow-compatible representation
    for node, data in graph.nodes(data=True):
        parts.append(
            algorithm_template.render(
                task_id=node,
                image=ConfigEntry.WORKER_DOCKER_IMAGE.value,
                name=data["name"],
                uuid=node.split("_", 1)[1],
                dependency="",
                project=str(project_uuid),
                pipeline=str(project.pipeline_uuid),
                algorithm=data["type"],
                parameters=data["parameters"],
                storage_driver=ConfigEntry.STORAGE_DRIVER.value,
                aws_access_key_id=ConfigEntry.AWS_ACCESS_KEY_ID.value,
                aws_secret_access_key=ConfigEntry.AWS_SECRET_ACCESS_KEY.value,
                aws_region=ConfigEntry.AWS_REGION.value,
                local_storage_path_external=ConfigEntry.LOCAL_STORAGE_PATH_EXTERNAL.value,
                container_name=project.container_name,
            )
        )

    for from_task, to_task in graph.edges:
        dependencies.append(dependency_template.render(from_task=from_task, to_task=to_task))

    parts.extend(dependencies)

    # Write the generated DAG to a Python file
    filename = os.path.join(ConfigEntry.AIRFLOW_DAGS.value, f"dag_{project_uuid.replace('-', '_')}.py")

    with open(filename, "w") as f:
        f.write("\n".join(parts))
