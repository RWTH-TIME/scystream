"""Unit tests for pythonpath/keycloak_token.py, run with
    pytest superset/tests
(requires PyJWT[crypto], which core/requirements-dev.txt provides)."""

import json
import sys
import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).parents[1] / "pythonpath"))

from keycloak_token import KeycloakTokenValidator, bearer_token  # noqa: E402

SERVICE_CLIENTS = {"superset-service": {"username": "scystream-core"}}


def _key(kid: str):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key()))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return private, jwk


REALM_KEY, REALM_JWK = _key("realm-key")
OTHER_KEY, _ = _key("realm-key")


@pytest.fixture
def validator(monkeypatch):
    validator = KeycloakTokenValidator("http://kc/certs", SERVICE_CLIENTS)
    monkeypatch.setattr(
        validator._jwks_client,
        "fetch_data",
        lambda: {"keys": [REALM_JWK]},
    )
    return validator


def _token(key=REALM_KEY, kid="realm-key", **claims):
    payload = {"azp": "superset-service", "exp": int(time.time()) + 60}
    payload.update(claims)
    payload = {k: v for k, v in payload.items() if v is not None}
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


def test_service_client_token_is_accepted(validator):
    assert validator.service_client_for(_token()) == {
        "username": "scystream-core",
    }


def test_other_client_is_rejected(validator):
    assert validator.service_client_for(_token(azp="scystream")) is None


def test_token_without_azp_is_rejected(validator):
    assert validator.service_client_for(_token(azp=None)) is None


def test_expired_token_is_rejected(validator):
    token = _token(exp=int(time.time()) - 10)
    assert validator.service_client_for(token) is None


def test_token_signed_by_other_key_is_rejected(validator):
    assert validator.service_client_for(_token(key=OTHER_KEY)) is None


def test_unknown_key_id_is_rejected(validator):
    assert validator.service_client_for(_token(kid="unknown")) is None


def test_hs256_token_is_rejected(validator):
    token = jwt.encode(
        {"azp": "superset-service", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
        headers={"kid": "realm-key"},
    )
    assert validator.service_client_for(token) is None


def test_garbage_is_rejected(validator):
    assert validator.service_client_for("not-a-jwt") is None


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Bearer abc", "abc"),
        ("bearer abc", "abc"),
        ("Basic abc", None),
        ("Bearer", None),
        ("", None),
        (None, None),
    ],
)
def test_bearer_token(header, expected):
    assert bearer_token(header) == expected
