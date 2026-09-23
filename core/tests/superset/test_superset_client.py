import json
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from services.superset_service.superset_client import (
    SupersetClient,
    SupersetClientError,
)

BASE = "http://superset.test"
TOKEN_URL = "http://keycloak.test/realms/r/protocol/openid-connect/token"


@pytest.fixture
def superset(requests_mock):
    requests_mock.post(TOKEN_URL, json={"access_token": "kc-token"})
    requests_mock.get(
        f"{BASE}/api/v1/security/csrf_token/",
        json={"result": "csrf-token"},
    )
    return requests_mock


def _client(**kwargs):
    return SupersetClient(
        base_url=f"{BASE}/",
        keycloak_token_url=TOKEN_URL,
        client_id="superset-service",
        client_secret="secret",
        **kwargs,
    )


def test_login_uses_keycloak_client_credentials(superset):
    client = _client()

    token_request = superset.request_history[0]
    assert token_request.url == TOKEN_URL
    assert "grant_type=client_credentials" in token_request.text
    assert "client_id=superset-service" in token_request.text

    assert client.session.headers["Authorization"] == "Bearer kc-token"
    assert client.session.headers["X-CSRFToken"] == "csrf-token"


def test_login_with_given_access_token_skips_keycloak(superset):
    client = _client(access_token="given")

    assert not any(r.url == TOKEN_URL for r in superset.request_history)
    assert client.session.headers["Authorization"] == "Bearer given"


def test_requests_have_a_timeout(superset):
    _client(timeout=12)
    assert all(r.timeout == 12 for r in superset.request_history)


def test_import_dashboard_zip(superset):
    superset.post(f"{BASE}/api/v1/dashboard/import/", json={"message": "OK"})
    client = _client()

    client.import_dashboard_zip(b"zip-bytes", {"databases/db.yaml": "pw"})

    request = superset.last_request
    assert b'name="formData"; filename="dashboard_export.zip"' in request.body
    assert b"zip-bytes" in request.body
    assert json.dumps({"databases/db.yaml": "pw"}).encode() in request.body
    assert b'name="overwrite"' in request.body
    assert request.headers["X-CSRFToken"] == "csrf-token"
    assert request.headers["Content-Type"].startswith("multipart/form-data")


def test_import_dashboard_zip_failure(superset):
    superset.post(
        f"{BASE}/api/v1/dashboard/import/",
        status_code=422,
        text="bad bundle",
    )
    with pytest.raises(SupersetClientError, match="422"):
        _client().import_dashboard_zip(b"zip", {})


def test_find_dashboard_id_by_uuid(superset):
    superset.get(
        f"{BASE}/api/v1/dashboard/",
        [{"json": {"result": []}}, {"json": {"result": [{"id": 7}]}}],
    )

    assert _client().find_dashboard_id_by_uuid(["missing", "found"]) == 7
    query = json.loads(superset.last_request.qs["q"][0])
    assert query["filters"] == [{"col": "uuid", "opr": "eq", "value": "found"}]


def test_grant_dashboard_access(superset):
    superset.get(
        f"{BASE}/api/v1/dashboard/3",
        json={"result": {
            "dashboard_title": "Overview",
            "slug": None,
            # Superset only returns the chart names here
            "charts": ["Topics"],
        }},
    )
    superset.get(
        f"{BASE}/api/v1/dashboard/3/datasets",
        json={"result": [{"id": 5}, {"id": 6}]},
    )
    superset.put(f"{BASE}/api/v1/dashboard/3", json={})
    for dataset_id in (5, 6):
        superset.get(
            f"{BASE}/api/v1/dataset/{dataset_id}",
            json={"result": {
                "id": dataset_id,
                "table_name": "topics",
                "schema": "s1",
                "database": {"id": 1},
            }},
        )
    superset.put(f"{BASE}/api/v1/dataset/5", json={})
    # a failing dataset update must not abort granting access
    superset.put(f"{BASE}/api/v1/dataset/6", status_code=403)

    _client().grant_dashboard_access(3, owner_id=42)

    puts = [r for r in superset.request_history if r.method == "PUT"]
    assert {r.path for r in puts} == {
        "/api/v1/dashboard/3", "/api/v1/dataset/5", "/api/v1/dataset/6",
    }
    assert all(r.json()["owners"] == [42] for r in puts)


def test_find_user_id_by_email(superset):
    superset.get(
        f"{BASE}/api/v1/security/users/",
        [{"json": {"result": [{"id": 9}]}}, {"json": {"result": []}}],
    )
    client = _client()
    assert client.find_user_id_by_email("a@b.de") == 9
    assert client.find_user_id_by_email("c@d.de") is None


def test_http_errors_are_raised(superset):
    superset.get(f"{BASE}/api/v1/dashboard/1", status_code=500)
    with pytest.raises(requests.HTTPError):
        _client().get_dashboard(1)


def test_ensure_user_returns_existing_user(superset):
    superset.get(
        f"{BASE}/api/v1/security/users/", json={"result": [{"id": 3}]},
    )

    assert _client().ensure_user("a@b.de") == 3
    assert not any(r.method == "POST" and "users" in r.path
                   for r in superset.request_history)


def test_ensure_user_creates_missing_user(superset):
    superset.get(f"{BASE}/api/v1/security/users/", json={"result": []})
    superset.get(
        f"{BASE}/api/v1/security/roles/", json={"result": [{"id": 4}]},
    )
    superset.post(f"{BASE}/api/v1/security/users/", json={"id": 11})

    assert _client().ensure_user("jane@b.de", role="Gamma") == 11

    role_request = [r for r in superset.request_history if "roles" in r.path]
    # requests_mock lower cases .qs, parse the raw url instead
    role_query = json.loads(
        parse_qs(urlparse(role_request[0].url).query)["q"][0],
    )
    assert role_query["filters"][0]["value"] == "Gamma"
    body = superset.last_request.json()
    assert body["username"] == body["email"] == "jane@b.de"
    assert body["roles"] == [4]
    assert body["active"] is True


def test_ensure_user_with_unknown_role(superset):
    superset.get(f"{BASE}/api/v1/security/users/", json={"result": []})
    superset.get(f"{BASE}/api/v1/security/roles/", json={"result": []})

    with pytest.raises(SupersetClientError, match="role"):
        _client().ensure_user("jane@b.de", role="Nope")
