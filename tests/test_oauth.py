"""Tests de oauth: funciones puras con httpx mockeado (MockTransport). Nunca la API real."""

import datetime as dt
import urllib.parse

import httpx
import pytest

from posse.auth import oauth


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_build_authorize_url():
    url = oauth.build_authorize_url("cid", "http://localhost:8765/callback", "st8")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert url.startswith(oauth.AUTHORIZE_URL)
    assert qs["response_type"] == ["code"]
    assert qs["client_id"] == ["cid"]
    assert qs["state"] == ["st8"]
    assert qs["scope"] == [oauth.SCOPES]


def test_exchange_code_for_tokens_postea_grant_correcto():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "AT", "expires_in": 5184000, "refresh_token": "RT"})

    payload = oauth.exchange_code_for_tokens(
        "the-code", client_id="cid", client_secret="sec", redirect_uri="http://cb", client=_client(handler)
    )
    assert payload["access_token"] == "AT"
    assert seen["url"] == oauth.TOKEN_URL
    assert "grant_type=authorization_code" in seen["body"]
    assert "code=the-code" in seen["body"]


def test_refresh_access_token_usa_grant_refresh():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "AT2", "expires_in": 5184000})

    oauth.refresh_access_token("RT", client_id="cid", client_secret="sec", client=_client(handler))
    assert "grant_type=refresh_token" in seen["body"]
    assert "refresh_token=RT" in seen["body"]


def test_fetch_person_urn():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer AT"
        return httpx.Response(200, json={"sub": "XyZ", "name": "Roman"})

    assert oauth.fetch_person_urn("AT", client=_client(handler)) == "urn:li:person:XyZ"


def test_bundle_calcula_expiraciones_y_conserva_refresh():
    now = dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc)
    # refresh sin refresh_token nuevo -> usa el fallback
    payload = {"access_token": "AT2", "expires_in": 5184000}
    bundle = oauth.bundle_from_token_response(
        payload, person_urn="urn:li:person:abc", refresh_token_fallback="RT_OLD", now=now
    )
    assert bundle.refresh_token == "RT_OLD"
    assert bundle.access_expires_at == "2026-08-30T00:00:00+00:00"  # +60 dias


def test_bundle_falla_sin_refresh_ni_fallback():
    with pytest.raises(ValueError):
        oauth.bundle_from_token_response({"access_token": "AT", "expires_in": 10}, person_urn="u")


def test_raise_for_status_propaga_error_http():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    with pytest.raises(httpx.HTTPStatusError):
        oauth.exchange_code_for_tokens(
            "c", client_id="x", client_secret="y", redirect_uri="z", client=_client(handler)
        )
