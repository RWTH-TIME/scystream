from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
import datetime
import pytest
from services.workflow_service.models.project import Project
from services.workflow_service.models.block import Block
from main import app
# Initialize the test client
client = TestClient(app)

# Create mock UUIDs for testing
mock_project_uuid = uuid4()
mock_block_uuids = [uuid4(), uuid4()]

# Mock Project and Blocks
mock_project = Project(
    uuid=mock_project_uuid,
    name="Mock Project",
    created_at=datetime.now(),
    users=[],
    blocks=[
        Block(
            uuid=mock_block_uuids[0],
            name="Block 1",
            project_uuid=mock_project_uuid,
            priority_weight=1,
            retries=2,
            retry_delay=300,
            custom_name="Block1_Custom",
            description="Description 1",
            author="Author 1",
            docker_image="docker/image1",
            repo_url="http://repo1",
            selected_entrypoint_uuid=None,
            x_pos=0.0,
            y_pos=0.0,
            upstream_blocks=[],
            downstream_blocks=[]
        ),
        Block(
            uuid=mock_block_uuids[1],
            name="Block 2",
            project_uuid=mock_project_uuid,
            priority_weight=1,
            retries=2,
            retry_delay=300,
            custom_name="Block2_Custom",
            description="Description 2",
            author="Author 2",
            docker_image="docker/image2",
            repo_url="http://repo2",
            selected_entrypoint_uuid=None,
            x_pos=1.0,
            y_pos=1.0,
            upstream_blocks=[mock_block_uuids[0]],
            downstream_blocks=[]
        )
    ]
)


@pytest.fixture
def mock_read_project():
    with patch(
        "services.workflow_service.controllers.project_controller.read_project",  # noqa: E501
        return_value=mock_project
    ) as mock_function:
        yield mock_function


def test_translate_project_to_dag_endpoint(mock_read_project):
    # Call the /translate endpoint with the mock project UUID
    response = client.get(
        "/dag/translate",
        params={"data": str(mock_project_uuid)}
    )

    # Assert the response status and content
    assert response.status_code == 200
    assert response.json() == "Test complete"
