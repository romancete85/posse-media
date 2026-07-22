"""Tests de token_store: backend local (round-trip + perms) y SSM (boto3 stubbed)."""

import boto3
import pytest
from botocore.stub import Stubber

from posse.config import Settings
from posse.auth.token_store import (
    LocalTokenStore,
    SsmTokenStore,
    TokenBundle,
    get_token_store,
)

BUNDLE = TokenBundle(
    access_token="at",
    refresh_token="rt",
    access_expires_at="2026-09-01T00:00:00+00:00",
    refresh_expires_at="2027-07-01T00:00:00+00:00",
    person_urn="urn:li:person:abc",
    scope="openid profile w_member_social",
)


def test_local_store_round_trip(tmp_path):
    store = LocalTokenStore(tmp_path / "tokens.json")
    assert store.load() is None
    store.save(BUNDLE)
    cargado = store.load()
    assert cargado == BUNDLE


def test_local_store_permisos_600(tmp_path):
    path = tmp_path / "tokens.json"
    LocalTokenStore(path).save(BUNDLE)
    assert (path.stat().st_mode & 0o777) == 0o600


def _ssm_client():
    return boto3.client(
        "ssm", region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y"
    )


def test_ssm_store_save_y_load():
    client = _ssm_client()
    store = SsmTokenStore("/p/tokens", "us-east-1", client=client)
    with Stubber(client) as stub:
        stub.add_response("put_parameter", {"Version": 1})
        store.save(BUNDLE)
        stub.add_response(
            "get_parameter",
            {"Parameter": {"Value": BUNDLE.model_dump_json()}},
            {"Name": "/p/tokens", "WithDecryption": True},
        )
        assert store.load() == BUNDLE


def test_ssm_store_load_none_si_no_existe():
    client = _ssm_client()
    store = SsmTokenStore("/p/tokens", "us-east-1", client=client)
    with Stubber(client) as stub:
        stub.add_client_error("get_parameter", "ParameterNotFound")
        assert store.load() is None


def test_factory_elige_backend():
    local = get_token_store(Settings(_env_file=None, token_store_backend="local"))
    ssm = get_token_store(Settings(_env_file=None, token_store_backend="ssm"))
    assert isinstance(local, LocalTokenStore)
    assert isinstance(ssm, SsmTokenStore)
