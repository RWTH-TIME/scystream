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

    def list_charts_for_dashboard(
        self,
        dashboard_id: int,
    ) -> list[dict[str, Any]]:
        resp = self.session.get(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}/charts"
        )
        resp.raise_for_status()
        return resp.json().get("result", [])

    def export_dashboard(self, dashboard_id: int) -> bytes:
        """Returns the Superset export bundle (zip) of a dashboard,
        including its charts, datasets and database."""
        resp = self.session.get(
            f"{self.base_url}/api/v1/dashboard/export/",
            params={"q": f"!({int(dashboard_id)})"},
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Dashboard export failed ({resp.status_code}): {resp.text}"
            )
        return resp.content

    # owners

    @staticmethod
    def _owner_ids(resource: dict[str, Any]) -> list[int]:
        return [
            owner["id"] if isinstance(owner, dict) else owner
            for owner in resource.get("owners", []) or []
        ]

    def add_dashboard_owner(self, dashboard_id: int, owner_id: int) -> None:
        owners = self._owner_ids(self.get_dashboard(dashboard_id))
        if owner_id in owners:
            return
        resp = self.session.put(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}",
            json={"owners": [*owners, owner_id]},
        )
        resp.raise_for_status()

    def add_dataset_owner(self, dataset_id: int, owner_id: int) -> None:
        owners = self._owner_ids(self.get_dataset(dataset_id))
        if owner_id in owners:
            return
        resp = self.session.put(
            f"{self.base_url}/api/v1/dataset/{dataset_id}",
            json={"owners": [*owners, owner_id]},
        )
        resp.raise_for_status()

    def grant_dashboard_access(self, dashboard_id: int, owner_id: int) -> None:
        """Adds the user as owner of the dashboard and its datasets, owners
        see the dashboard and may query its datasets."""
        self.add_dashboard_owner(dashboard_id, owner_id)
        for dataset in self.list_datasets_for_dashboard(dashboard_id):
            dataset_id = dataset.get("id")
            if dataset_id:
                try:
                    self.add_dataset_owner(dataset_id, owner_id)
                except requests.HTTPError as exc:
                    logger.warning(
                        "Failed to add owner to dataset %s: %s",
                        dataset_id,
                        exc,
                    )

    # databases & datasets

    def _find_one(self, resource: str, filters: list[dict],
                  columns: list[str]) -> dict[str, Any] | None:
        query = {"filters": filters, "columns": columns, "page_size": 1}
        resp = self.session.get(
            f"{self.base_url}/api/v1/{resource}/",
            params={"q": json.dumps(query)},
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return results[0] if results else None

    def ensure_database(self, name: str, sqlalchemy_uri: str) -> dict:
        """Creates the database connection or updates its URI. Returns the
        connection's id and uuid."""
        existing = self._find_one(
            "database",
            [{"col": "database_name", "opr": "eq", "value": name}],
            ["id", "uuid", "database_name"],
        )
        payload = {
            "sqlalchemy_uri": sqlalchemy_uri,
            "expose_in_sqllab": True,
        }
        if existing:
            resp = self.session.put(
                f"{self.base_url}/api/v1/database/{existing['id']}",
                json=payload,
            )
            if not resp.ok:
                raise SupersetClientError(
                    f"Updating database {name} failed "
                    f"({resp.status_code}): {resp.text}"
                )
            return {"id": existing["id"], "uuid": existing["uuid"]}

        resp = self.session.post(
            f"{self.base_url}/api/v1/database/",
            json={"database_name": name, **payload},
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Creating database {name} failed "
                f"({resp.status_code}): {resp.text}"
            )
        database_id = resp.json()["id"]
        created = self._find_one(
            "database",
            [{"col": "database_name", "opr": "eq", "value": name}],
            ["id", "uuid"],
        )
        return {"id": database_id, "uuid": created["uuid"]}

    def get_dataset(self, dataset_id: int) -> dict[str, Any]:
        resp = self.session.get(
            f"{self.base_url}/api/v1/dataset/{dataset_id}"
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    def ensure_dataset(
        self,
        database_id: int,
        schema: str,
        table_name: str,
    ) -> dict[str, Any]:
        """Creates the dataset of a physical table if needed and refreshes
        its columns. Returns id, uuid, schema and table_name."""
        columns = ["id", "uuid", "schema", "table_name"]
        filters = [
            {"col": "table_name", "opr": "eq", "value": table_name},
            {"col": "schema", "opr": "eq", "value": schema},
            {"col": "database", "opr": "rel_o_m", "value": database_id},
        ]
        dataset = self._find_one("dataset", filters, columns)
        if dataset is None:
            resp = self.session.post(
                f"{self.base_url}/api/v1/dataset/",
                json={
                    "database": database_id,
                    "schema": schema,
                    "table_name": table_name,
                },
            )
            if not resp.ok:
                raise SupersetClientError(
                    f"Creating dataset {schema}.{table_name} failed "
                    f"({resp.status_code}): {resp.text}"
                )
            dataset = self._find_one("dataset", filters, columns)
        else:
            # pick up columns added by later runs
            self.session.put(
                f"{self.base_url}/api/v1/dataset/{dataset['id']}/refresh"
            )
        return dataset

    # charts & dashboards

    def create_chart(
        self,
        slice_name: str,
        dataset_id: int,
        params: dict[str, Any],
        dashboard_ids: list[int],
        viz_type: str = "table",
    ) -> int:
        resp = self.session.post(
            f"{self.base_url}/api/v1/chart/",
            json={
                "slice_name": slice_name,
                "viz_type": viz_type,
                "datasource_id": dataset_id,
                "datasource_type": "table",
                "dashboards": dashboard_ids,
                "params": json.dumps(
                    {"datasource": f"{dataset_id}__table",
                     "viz_type": viz_type, **params},
                ),
            },
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Creating chart {slice_name} failed "
                f"({resp.status_code}): {resp.text}"
            )
        return resp.json()["id"]

    def find_dashboard_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self._find_one(
            "dashboard",
            [{"col": "slug", "opr": "eq", "value": slug}],
            ["id", "uuid", "slug", "dashboard_title"],
        )

    def create_dashboard(self, title: str, slug: str) -> int:
        resp = self.session.post(
            f"{self.base_url}/api/v1/dashboard/",
            json={"dashboard_title": title, "slug": slug, "published": True},
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Creating dashboard {title} failed "
                f"({resp.status_code}): {resp.text}"
            )
        return resp.json()["id"]

    def update_dashboard(self, dashboard_id: int, **fields: Any) -> None:
        resp = self.session.put(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}",
            json=fields,
        )
        if not resp.ok:
            raise SupersetClientError(
                f"Updating dashboard {dashboard_id} failed "
                f"({resp.status_code}): {resp.text}"
            )

    def delete_dashboard(self, dashboard_id: int) -> None:
        resp = self.session.delete(
            f"{self.base_url}/api/v1/dashboard/{dashboard_id}"
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()

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
