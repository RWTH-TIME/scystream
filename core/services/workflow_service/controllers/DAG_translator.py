import os
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import networkx as nx
from uuid import UUID
import json

from services.workflow_service.controllers.project_controller \
    import read_project

DAG_DIRECTORY = "airflow-dags"


def translate_project_to_dag(project_uuid: UUID):
    """
    Parses a project and its blocks into a DAG and validates it.
    """
    # Query the project
    project = read_project(project_uuid)

    if not project:
        raise HTTPException(status_code=404, detail="Project is not known")

    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes (tasks)
    for block in project.blocks:

        entrypoint = block.selected_entrypoint

        envs = entrypoint.envs
        configs = [io.config for io in entrypoint.input_outputs]
        merged_configs = {}

        # First, add all envs to merged_configs with string representation
        for k, v in envs.items():
            if isinstance(v, list):  # Check if the value is a list
                # Convert the list to its string representation
                merged_configs[k] = json.dumps(v)
            else:
                merged_configs[k] = str(v)  # Convert other values to string

        # Now, add all configs to merged_configs with string representation
        for d in configs:
            for k, v in d.items():
                if isinstance(v, list):  # Check if the value is a list
                    # Convert the list to its string representation
                    merged_configs[k] = json.dumps(v)
                else:
                    merged_configs[k] = str(v)  # Convert other values to strin

        graph.add_node(block.uuid, **{
            "uuid": block.uuid,
            "name": block.name,
            "image": block.docker_image,
            "entry_name": block.selected_entrypoint.name,
            "environment": {**envs, **merged_configs},
        })

    # Add edges (dependencies)
    for block in project.blocks:
        for upstream in block.upstream_blocks:
            upstream_task_id = upstream.uuid
            current_task_id = block.uuid
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
        dag_id=f"dag_{str(project_uuid).replace('-', '_')}"
    )]

    # Convert to Airflow-compatible representation
    for node, data in graph.nodes(data=True):
        task_id = str(node).replace("-", "_")
        print(data["entry_name"])
        parts.append(
            algorithm_template.render(
                task_id=f"task_{task_id}",
                image=data["image"],
                name=data["name"],
                uuid=data["uuid"],
                entry_name=data["entry_name"],
                project=str(project_uuid),
                environment=data["environment"],
                local_storage_path_external="/tmp/scystream-data",
            )
        )

    dependencies = [
        dependency_template.render(
            from_task=f"task_{str(from_task).replace("-", "_")}",
            to_task=f"task_{str(to_task).replace("-", "_")}"
        )
        for from_task, to_task in graph.edges
    ]
    parts.extend(dependencies)

    # Write the generated DAG to a Python file
    os.makedirs(DAG_DIRECTORY, exist_ok=True)
    filename = os.path.join(DAG_DIRECTORY, f"dag_{
                            str(project_uuid).replace('-', '_')}.py")

    # Write the generated DAG to a Python file
    with open(filename, "w") as f:
        f.write("\n".join(parts))
