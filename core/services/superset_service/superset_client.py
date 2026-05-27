import json
import logging
from typing import Any

import requests
from utils.config.environment import ENV

logger = logging.getLogger(__name__)


class SupersetClientError(Exception):
    pass


class SupersetClient:
    def __init__(
        self,
        base_url: str | None = None,
        keycloak_token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.base_url = (base_url or ENV.SUPERSET_HOST).rstrip("/")
        self.keycloak_token_url = keycloak_token_url or ENV.keycloak_token_url
        self.client_id = client_id or ENV.SUPERSET_KEYCLOAK_CLIENT_ID
        self.client_secret = client_secret or ENV.SUPERSET_KEYCLOAK_CLIENT_SECRET
        self.session = requests.Session()
        self._login()

    def _login(self) -> None:
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
        access_token = token_resp.json()["access_token"]

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
            f"{self.base_url}/api/v1/security/users",
            params={"q": json.dumps(query)},
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return results[0]["id"] if results else None

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
            files={"formData": ("dashboard_export.zip", zip_bytes, "application/zip")},
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

    def list_datasets_for_dashboard(self, dashboard_id: int) -> list[dict[str, Any]]:
        dashboard = self.get_dashboard(dashboard_id)
        dataset_ids = {
            chart.get("datasource_id")
            for chart in dashboard.get("charts", [])
            if chart.get("datasource_id")
        }
        datasets: list[dict[str, Any]] = []
        for dataset_id in dataset_ids:
            resp = self.session.get(
                f"{self.base_url}/api/v1/dataset/{dataset_id}"
            )
            if resp.ok:
                datasets.append(resp.json().get("result", {}))
        return datasets

    def set_dataset_owners(self, dataset_id: int, owner_ids: list[int]) -> None:
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
