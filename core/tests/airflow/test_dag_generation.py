import ast
import os

import pytest
from services.workflow_service.controllers import workflow_controller as wc
from tests.sample_workflow import BLOCKS, PROJECT_UUID, sample_graph


def _render(graph=None):
    return wc.generate_dag_code(
        graph or sample_graph(),
        wc.init_templates(),
        wc.project_id_to_dag_id(PROJECT_UUID),
        PROJECT_UUID,
    )


def _operator_calls(dag_code: str) -> dict[str, dict]:
    """Returns the keyword arguments of every DockerOperator(...) call."""
    calls = {}
    for node in ast.walk(ast.parse(dag_code)):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "DockerOperator"
        ):
            kwargs = {
                kw.arg: ast.literal_eval(kw.value)
                for kw in node.keywords
                if kw.arg
                in ("task_id", "image", "environment", "network_mode")
            }
            calls[kwargs["task_id"]] = kwargs
    return calls


def test_id_conversions_roundtrip():
    dag_id = wc.project_id_to_dag_id(PROJECT_UUID)
    assert dag_id == "dag_0b6f3c0e_8a51_4d6c_9a57_6f1f8f0e2c11"
    assert wc.dag_id_to_project_id(dag_id) == str(PROJECT_UUID)

    block_uuid = BLOCKS[0]["uuid"]
    task_id = wc.cb_id_to_task_id(block_uuid)
    assert task_id.isidentifier()
    assert wc.task_id_to_cb_id(task_id) == str(block_uuid)


def test_generated_dag_contains_all_tasks_with_config():
    calls = _operator_calls(_render())

    assert set(calls) == {wc.cb_id_to_task_id(b["uuid"]) for b in BLOCKS}
    for block in BLOCKS:
        call = calls[wc.cb_id_to_task_id(block["uuid"])]
        assert call["image"] == block["image"]
        assert call["environment"] == block["environment"]
        assert call["network_mode"] == wc.ENV.CB_NETWORK_MODE


def test_generated_dag_contains_dependencies():
    dag_code = _render()
    for upstream, downstream in sample_graph().edges:
        assert (
            f"{wc.cb_id_to_task_id(upstream)} >> "
            f"{wc.cb_id_to_task_id(downstream)}"
        ) in dag_code


def test_special_characters_are_escaped():
    graph = sample_graph()
    node = graph.nodes[BLOCKS[0]["uuid"]]
    node["image"] = "registry/it's-an-image:latest"
    node["environment"] = {"QUOTES": "'\"\\ \n end"}

    calls = _operator_calls(_render(graph))

    call = calls[wc.cb_id_to_task_id(BLOCKS[0]["uuid"])]
    assert call["image"] == "registry/it's-an-image:latest"
    assert call["environment"] == {"QUOTES": "'\"\\ \n end"}


def test_invalid_dag_code_is_rejected():
    with pytest.raises(wc.InvalidDagCodeError):
        wc.validate_dag_code("with DAG('x') as dag:\n  task = (")


def test_save_dag_to_file_is_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(wc, "DAG_DIRECTORY", str(tmp_path))

    path = wc.save_dag_to_file("print('v1')\n", "dag_x")
    wc.save_dag_to_file("print('v2')\n", "dag_x")

    assert open(path).read() == "print('v2')\n"
    # no temporary files are left behind
    assert os.listdir(tmp_path) == ["dag_x.py"]


def test_filesystem_dag_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(wc, "DAG_DIRECTORY", str(tmp_path))
    for name in ("dag_a.py", "dag_b.py", ".dag_c.py.tmp", "other.py"):
        (tmp_path / name).write_text("")

    assert sorted(wc._get_all_dags_from_filesystem()) == ["dag_a", "dag_b"]


@pytest.mark.parametrize(
    ("image", "expected"),
    [
        ("ghcr.io/rwth-time/topic-modeling:latest",
         "registry.lan:5001/rwth-time/topic-modeling:latest"),
        ("rwthtime/block:1", "hub-cache.lan/rwthtime/block:1"),
        ("python:3.13", "hub-cache.lan/library/python:3.13"),
        ("quay.io/org/img:1", "quay.io/org/img:1"),
    ],
)
def test_images_are_pulled_via_mirrors(monkeypatch, image, expected):
    monkeypatch.setattr(wc.ENV, "CB_IMAGE_REGISTRY_MIRRORS", {
        "ghcr.io": "registry.lan:5001", "docker.io": "hub-cache.lan/",
    })
    assert wc.resolve_image(image) == expected


def test_force_pull_is_rendered(monkeypatch):
    monkeypatch.setattr(wc.ENV, "CB_IMAGE_FORCE_PULL", True)
    assert "force_pull=True" in _render()
    monkeypatch.setattr(wc.ENV, "CB_IMAGE_FORCE_PULL", False)
    assert "force_pull=False" in _render()
