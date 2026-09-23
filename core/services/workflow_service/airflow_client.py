"""Thin wrapper around the Airflow REST API authentication.

Airflow 3 issues JWT access tokens via ``POST /auth/token``. Requesting a new
token for every API call (the websocket status loops poll every two seconds)
is wasteful, so tokens are cached for ``AIRFLOW_TOKEN_TTL_SECONDS``.
"""

import threading
import time

import requests
from airflow_client.client.api_client import ApiClient
from airflow_client.client.configuration import Configuration
from pydantic import BaseModel
from utils.config.environment import ENV

REQUEST_TIMEOUT_SECONDS = 30


class AirflowAccessTokenResponse(BaseModel):
    access_token: str


def get_airflow_client_access_token(
    host: str,
    username: str,
    password: str,
) -> str:
    url = f"{host.rstrip('/')}/auth/token"
    payload = {
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code != 201:
        raise RuntimeError(
            "Failed to get access token: "
            f"{response.status_code} {response.text}",
        )
    return AirflowAccessTokenResponse(**response.json()).access_token


class _TokenCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(self) -> str:
        with self._lock:
            now = time.monotonic()
            if self._token is None or now >= self._expires_at:
                self._token = get_airflow_client_access_token(
                    host=ENV.AIRFLOW_HOST,
                    username=ENV.AIRFLOW_USER,
                    password=ENV.AIRFLOW_PASS,
                )
                self._expires_at = now + ENV.AIRFLOW_TOKEN_TTL_SECONDS
            return self._token

    def invalidate(self) -> None:
        with self._lock:
            self._token = None
            self._expires_at = 0.0


_token_cache = _TokenCache()


def invalidate_airflow_token() -> None:
    _token_cache.invalidate()


def get_airflow_config() -> Configuration:
    airflow_config = Configuration(host=ENV.AIRFLOW_HOST.rstrip("/"))
    airflow_config.access_token = _token_cache.get()
    return airflow_config


def airflow_api_client() -> ApiClient:
    return ApiClient(get_airflow_config())
