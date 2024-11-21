from fastapi import HTTPException
import networkx as nx
from sqlalchemy.orm import Session
from typing import Dict, Any
from models.project import Project
#from models.block import Block


def parse_project_to_dag(project_uuid: str, db: Session) -> Dict[str, Any]:
    """
    Parses a project and its blocks into a DAG representation.

    :param project_uuid: UUID of the project to parse.
    :param db: SQLAlchemy database session.
    :return: A dictionary containing DAG tasks and dependencies.
    """
    # Query the project
    project = db.query(Project).filter_by(uuid=project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes (tasks)
    for block in project.blocks:
        task_id = str(block.uuid)
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
            graph.add_edge(str(upstream.uuid), str(block.uuid))

    # Ensure the graph is a DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise HTTPException(
            status_code=400,
            detail="The project is not acyclic."
            )

    # Convert to Airflow-compatible representation
    tasks = {}
    dependencies = []

    for node, data in graph.nodes(data=True):
        tasks[node] = data

    for from_task, to_task in graph.edges:
        dependencies.append({"from": from_task, "to": to_task})

    return {"tasks": tasks, "dependencies": dependencies}
