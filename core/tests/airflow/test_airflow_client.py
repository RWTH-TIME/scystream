from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
import requests
from airflow_client.client.exceptions import ApiException
from services.workflow_service import airflow_client
from services.workflow_service.controllers import workflow_controller as wc
from services.workflow_service.schemas.workflow import WorkflowStatus

TOKEN_URL = "http://airflow.test/auth/token"


@pytest.fixture(autouse=True)
def airflow_env(monkeypatch):
    monkeypatch.setattr(
        airflow_client.ENV, "AIRFLOW_HOST", "http://airflow.test",
    )
    airflow_client.invalidate_airflow_token()
    yield
    airflow_client.invalidate_airflow_token()


def test_token_is_cached(requests_mock):
    requests_mock.post(TOKEN_URL, status_code=201, json={"access_token": "t1"})

    assert airflow_client.get_airflow_config().access_token == "t1"
    assert airflow_client.get_airflow_config().access_token == "t1"
    assert requests_mock.call_count == 1
    assert requests_mock.last_request.json() == {
        "username": airflow_client.ENV.AIRFLOW_USER,
        "password": airflow_client.ENV.AIRFLOW_PASS,
    }


def test_token_is_refreshed_after_ttl(requests_mock, monkeypatch):
    requests_mock.post(
        TOKEN_URL,
        [
            {"status_code": 201, "json": {"access_token": "t1"}},
            {"status_code": 201, "json": {"access_token": "t2"}},
        ],
    )
    monkeypatch.setattr(airflow_client.ENV, "AIRFLOW_TOKEN_TTL_SECONDS", 0)

    assert airflow_client.get_airflow_config().access_token == "t1"
    assert airflow_client.get_airflow_config().access_token == "t2"


def test_failed_login_raises(requests_mock):
    requests_mock.post(TOKEN_URL, status_code=401, text="nope")

    with pytest.raises(RuntimeError, match="401"):
        airflow_client.get_airflow_config()


def test_unauthorized_invalidates_token(requests_mock):
    requests_mock.post(
        TOKEN_URL,
        [
            {"status_code": 201, "json": {"access_token": "t1"}},
            {"status_code": 201, "json": {"access_token": "t2"}},
        ],
    )

    @wc._invalidate_token_on_unauthorized
    def call_airflow():
        airflow_client.get_airflow_config()
        raise ApiException(status=401)

    with pytest.raises(ApiException):
        call_airflow()

    assert airflow_client.get_airflow_config().access_token == "t2"


def test_get_all_dags_falls_back_to_filesystem(
    requests_mock, tmp_path, monkeypatch,
):
    requests_mock.post(TOKEN_URL, status_code=201, json={"access_token": "t"})
    requests_mock.get(
        "http://airflow.test/api/v2/dags",
        exc=requests.ConnectionError,
    )
    monkeypatch.setattr(wc, "DAG_DIRECTORY", str(tmp_path))
    (tmp_path / "dag_a.py").write_text("")

    assert wc.get_all_dags() == ["dag_a"]


def test_get_all_dags_from_api(requests_mock):
    requests_mock.post(TOKEN_URL, status_code=201, json={"access_token": "t"})
    requests_mock.get(
        "http://airflow.test/api/v2/dags",
        json={"dags": [{"dag_id": "dag_a"}, {"dag_id": "dag_b"}]},
    )

    assert wc.get_all_dags() == ["dag_a", "dag_b"]
    assert (
        requests_mock.last_request.headers["Authorization"] == "Bearer t"
    )


def _run(dag_id, state, start):
    return SimpleNamespace(dag_id=dag_id, state=state, start_date=start)


def test_last_dag_run_overview_queries_once(requests_mock, monkeypatch):
    requests_mock.post(TOKEN_URL, status_code=201, json={"access_token": "t"})
    calls = []
    runs = [
        _run("dag_a", "success", datetime(2026, 1, 1, tzinfo=UTC)),
        _run("dag_a", "running", datetime(2026, 1, 2, tzinfo=UTC)),
        _run("dag_b", "failed", datetime(2026, 1, 1, tzinfo=UTC)),
        _run("dag_b", "queued", None),
    ]

    class FakeDagRunApi:
        def __init__(self, _):
            pass

        def get_list_dag_runs_batch(self, dag_id, body):
            calls.append(body)
            return SimpleNamespace(dag_runs=runs)

    monkeypatch.setattr(wc, "DagRunApi", FakeDagRunApi)

    result = wc.last_dag_run_overview(["dag_a", "dag_b"])

    assert len(calls) == 1
    assert calls[0].dag_ids == ["dag_a", "dag_b"]
    assert result["dag_a"].state == "running"
    # a queued run without start date is the most recent one
    assert result["dag_b"].state == "queued"


def test_last_dag_run_overview_without_dags_skips_airflow(requests_mock):
    assert wc.last_dag_run_overview([]) == {}
    assert requests_mock.call_count == 0


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("success", WorkflowStatus.FINISHED),
        ("SUCCESS", WorkflowStatus.FINISHED),
        ("running", WorkflowStatus.RUNNING),
        ("failed", WorkflowStatus.FAILED),
        ("queued", WorkflowStatus.IDLE),
        (None, WorkflowStatus.IDLE),
    ],
)
def test_workflow_status_from_airflow_state(state, expected):
    assert WorkflowStatus.from_airflow_state(state) is expected


def test_workflow_status_values_are_strings():
    # the frontend compares against plain strings
    assert all(isinstance(s.value, str) for s in WorkflowStatus)
