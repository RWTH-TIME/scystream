"""Loads generated DAGs with a real Airflow installation and verifies them.

This script runs *inside* the Airflow image that is used in
docker-compose.yml, it must therefore only depend on Airflow itself.

Usage:
    python check_dagbag.py <dag-dir>
"""

import json
import sys
from pathlib import Path

from airflow.models.dagbag import DagBag
from airflow.providers.docker.operators.docker import DockerOperator


def main(dag_dir: Path) -> int:
    expectations = json.loads((dag_dir / "expectations.json").read_text())
    dagbag = DagBag(dag_folder=str(dag_dir), include_examples=False)

    errors = []
    for path, error in dagbag.import_errors.items():
        errors.append(f"Import error in {path}:\n{error}")

    for dag_id, expected in expectations.items():
        dag = dagbag.dags.get(dag_id)
        if dag is None:
            errors.append(f"DAG {dag_id} was not loaded")
            continue

        if dag.schedule is not None and str(dag.schedule) != "None":
            errors.append(f"{dag_id}: unexpected schedule {dag.schedule}")
        if not dag.is_paused_upon_creation:
            errors.append(f"{dag_id}: must be paused upon creation")

        task_ids = set(dag.task_dict)
        if task_ids != set(expected["tasks"]):
            errors.append(
                f"{dag_id}: tasks {sorted(task_ids)} != "
                f"{sorted(expected['tasks'])}"
            )

        for task_id, task_expectation in expected["tasks"].items():
            task = dag.task_dict.get(task_id)
            if task is None:
                continue
            if not isinstance(task, DockerOperator):
                errors.append(f"{task_id}: is not a DockerOperator")
                continue
            if task.image != task_expectation["image"]:
                errors.append(f"{task_id}: unexpected image {task.image}")
            if task.environment != task_expectation["environment"]:
                errors.append(
                    f"{task_id}: unexpected environment {task.environment}"
                )

        edges = sorted(
            [upstream, task.task_id]
            for task in dag.tasks
            for upstream in sorted(task.upstream_task_ids)
        )
        if edges != expected["edges"]:
            errors.append(f"{dag_id}: edges {edges} != {expected['edges']}")

    if errors:
        print("\n\n".join(errors), file=sys.stderr)
        return 1

    print(f"OK: {len(expectations)} generated DAG(s) loaded by Airflow")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1])))
