"""Renders DAG files with the core DAG generator so they can be loaded by a
real Airflow installation (see check_dagbag.py and the `airflow` CI workflow).

Usage (from the core directory):
    python -m tests.airflow.render_sample_dags <output-dir>
"""

import json
import sys
from pathlib import Path

from services.workflow_service.controllers import workflow_controller as wc
from tests.sample_workflow import BLOCKS, EDGES, PROJECT_UUID, sample_graph


def render(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    dag_id = wc.project_id_to_dag_id(PROJECT_UUID)
    dag_code = wc.generate_dag_code(
        sample_graph(),
        wc.init_templates(),
        dag_id,
        PROJECT_UUID,
    )
    (output_dir / f"{dag_id}.py").write_text(dag_code)

    expectations = {
        dag_id: {
            "tasks": {
                wc.cb_id_to_task_id(b["uuid"]): {
                    "image": b["image"],
                    "environment": {
                        k: str(v) for k, v in b["environment"].items()
                    },
                }
                for b in BLOCKS
            },
            "edges": sorted(
                [wc.cb_id_to_task_id(u), wc.cb_id_to_task_id(d)]
                for u, d in EDGES
            ),
        }
    }
    (output_dir / "expectations.json").write_text(
        json.dumps(expectations, indent=2),
    )
    return expectations


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render(Path(sys.argv[1]))
