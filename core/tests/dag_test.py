from unittest.mock import MagicMock
from services.workflow_service.controllers.DAG_translator \
   import translate_project_to_dag
# from ...controllers.DAG_translator
# import translate_project_to_dag # type: ignore

from services.workflow_service.models.project import Project
from services.workflow_service.models.block import Block


def test_translate_project_to_dag():
    mock_project = MagicMock(Project)
    mock_project.blocks = [
        MagicMock(Block,
                  uuid="1",
                  name="Block1",
                  block_type=MagicMock(value="algorithm"),
                  priority_weight=1,
                  retries=2,
                  retry_delay=300,
                  selected_entrypoint=MagicMock(
                      envs={"VAR": "VALUE"}, inputoutputs=[]
                      )),
        MagicMock(Block,
                  uuid="2",
                  name="Block2",
                  block_type=MagicMock(value="algorithm"),
                  priority_weight=1,
                  retries=2,
                  retry_delay=300,
                  selected_entrypoint=MagicMock(envs={}, inputoutputs=[]),
                  upstream_blocks=[MagicMock(uuid="1")]),
    ]

    mock_read_project = MagicMock(return_value=mock_project)
    translate_project_to_dag.read_project = mock_read_project

    dag_content = translate_project_to_dag(
        "project_uuid",
        return_as_string=True
        )

    assert "task_Block1" in dag_content
    assert "task_Block2" in dag_content
    assert "Block1 -> Block2" in dag_content
