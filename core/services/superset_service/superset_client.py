import json
import logging
import secrets
from typing import Any

import requests
from utils.config.environment import ENV

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60


class SupersetClientError(Exception):
    pass


class _TimeoutSession(requests.Session):
    """requests.Session that applies a default timeout to every request, so a
    hanging Superset can never block the core indefinitely."""

    def __init__(self, timeout: float):
        super().__init__()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, url, **kwargs)


class SupersetClient:
    def __init__(
        self,
        base_url: str | None = None,
        keycloak_token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ):
        """
        By default the client authenticates against Keycloak using the
        client credentials grant. An already issued ``access_token`` (e.g. one
        obtained via Superset's own ``/api/v1/security/login``) can be passed
        instead.
        """
        self.base_url = (base_url or ENV.SUPERSET_HOST).rstrip("/")
        self.keycloak_token_url = keycloak_token_url or ENV.keycloak_token_url
        self.client_id = client_id or ENV.SUPERSET_KEYCLOAK_CLIENT_ID
        self.client_secret = (
            client_secret or ENV.SUPERSET_KEYCLOAK_CLIENT_SECRET
        )
        self.session = _TimeoutSession(timeout)
        self._login(access_token)

    def _fetch_keycloak_token(self) -> str:
        token_resp = self.session.post(
            self.keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        return token_resp.json()["access_token"]

    def _login(self, access_token: str | None = None) -> None:
        access_token = access_token or self._fetch_keycloak_token()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Referer": f"{self.base_url}/",
            }
        )

        csrf_resp = self.session.get(
            f"{self.base_url}/api/v1/security/csrf_token/"
        )
        csrf_resp.raise_for_status()
        self.session.headers.update(
            {"X-CSRFToken": csrf_resp.json()["result"]}
        )

    def find_user_id_by_email(self, email: str) -> int | None:
        query = {"filters": [{"col": "email", "opr": "eq", "value": email}]}
        resp = self.session.get(
            f"{self.base_url}/api/v1/security/users/",
            params={"q": json.dumps(query)},
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return results[0]["id"] if results else None

    def find_role_id(self, name: str) -> int | None:
        query = {"filters": [{"col": "name", "opr": "eq", "value": name}]}
        resp = self.session.get(
            f"{self.base_url}/api/v1/security/roles/",
            params={"q": json.dumps(query)},
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return results[0]["id"] if results else None

    def ensure_user(self, email: str, role: str | None = None) -> int:
        """Returns the id of the Superset user with the given email and
        creates the user if it does not exist yet.

        The username is the email, which is also what the Keycloak login of
        Superset uses (see superset/pythonpath/scystream_security.py), so the
        user is matched on their first login.
        """
        user_id = self.find_user_id_by_email(email)
        if user_id:
            return user_id

        role = role or ENV.SUPERSET_USER_ROLE
        role_id = self.find_role_id(role)
        if not role_id:
            raise SupersetClientError(f"Superset role {role} does not exist")

        local_part = email.split("@", 1)[0]
        resp = self.session.post(
            f"{self.base_url}/api/v1/security/users/",
            json={
                "username": email,
                "email": email,
                "first_name": local_part,
                "last_name": "-",
                "active": True,
                "roles": [role_id],
                # never used, users log in via Keycloak
                "password": secrets.token_urlsafe(32),
            },
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Creating Superset user {email} failed "
                f"({resp.status_code}): {resp.text}"
            )
        logger.info("Created Superset user %s", email)
        return resp.json()["id"]

    def find_dashboard_id_by_uuid(
        self,
        dashboard_uuids: list[str],
    ) -> int | None:
        """Returns the id of the first dashboard that exists in Superset."""
        for dashboard_uuid in dashboard_uuids:
            query = {
                "filters": [
                    {"col": "uuid", "opr": "eq", "value": dashboard_uuid},
                ],
                "page_size": 1,
            }
            resp = self.session.get(
                f"{self.base_url}/api/v1/dashboard/",
                params={"q": json.dumps(query)},
            )
            if resp.ok:
                results = resp.json().get("result", [])
                if results:
                    return results[0]["id"]
        return None

    def import_dashboard_zip(
        self,
        zip_bytes: bytes,
        passwords: dict[str, str],
        overwrite: bool = True,
    ) -> list[dict[str, Any]]:
        headers = {k: v for k, v in self.session.headers.items()}
        headers.pop("Content-Type", None)

        resp = self.session.post(
            f"{self.base_url}/api/v1/dashboard/import/",
            files={
                "formData": (
                    "dashboard_export.zip",
                    zip_bytes,
                    "application/zip",
                )
            },
            data={
                "passwords": json.dumps(passwords),
                "overwrite": str(overwrite).lower(),
            },
            headers=headers,
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Dashboard import failed ({resp.status_code}): {resp.text}"
            )

        payload = resp.json()
        return payload.get("result", [])

    def get_dashboard(self, dashboard_id: int) -> dict[str, Any]:
        resp = self.session.get(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}"
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    def set_dashboard_owners(
        self,
        dashboard_id: int,
        owner_ids: list[int],
    ) -> None:
        dashboard = self.get_dashboard(dashboard_id)
        resp = self.session.put(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}",
            json={
                "dashboard_title": dashboard.get("dashboard_title"),
                "slug": dashboard.get("slug"),
                "owners": owner_ids,
            },
        )
        resp.raise_for_status()

    def list_datasets_for_dashboard(
        self,
        dashboard_id: int,
    ) -> list[dict[str, Any]]:
        # Note: the "charts" of GET /dashboard/<id> only contain chart names
        resp = self.session.get(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}/datasets"
        )
        resp.raise_for_status()
        return resp.json().get("result", [])

    def set_dataset_owners(
        self,
        dataset_id: int,
        owner_ids: list[int],
    ) -> None:
        resp = self.session.get(f"{self.base_url}/api/v1/dataset/{dataset_id}")
        resp.raise_for_status()
        dataset = resp.json().get("result", {})
        resp = self.session.put(
            f"{self.base_url}/api/v1/dataset/{dataset_id}",
            json={
                "table_name": dataset.get("table_name"),
                "schema": dataset.get("schema"),
                "database_id": dataset.get("database", {}).get("id")
                or dataset.get("database_id"),
                "owners": owner_ids,
            },
        )
        resp.raise_for_status()

    def grant_dashboard_access(self, dashboard_id: int, owner_id: int) -> None:
        self.set_dashboard_owners(dashboard_id, [owner_id])
        for dataset in self.list_datasets_for_dashboard(dashboard_id):
            dataset_id = dataset.get("id")
            if dataset_id:
                try:
                    self.set_dataset_owners(dataset_id, [owner_id])
                except requests.HTTPError as exc:
                    logger.warning(
                        "Failed to set dataset %s owners: %s",
                        dataset_id,
                        exc,
                    )

    def get_dashboards_for_user(self, email: str) -> list[dict[str, Any]]:
        user_id = self.find_user_id_by_email(email)
        if not user_id:
            return []

        query = {
            "filters": [{"col": "owners", "opr": "rel_m_m", "value": user_id}],
            "page_size": 100,
        }
        resp = self.session.get(
            f"{self.base_url}/api/v1/dashboard/",
            params={"q": json.dumps(query)},
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
