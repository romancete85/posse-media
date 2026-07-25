"""Tests del cliente X/Twitter con HTTP mockeado. La firma OAuth1 se testea en su forma, no contra la API."""

import datetime as dt

import httpx
import pytest

from posse.models import Pieza
from posse.platforms.twitter import TwitterConfigError, TwitterError, TwitterPublisher, _oauth1_header

CLOCK = lambda: dt.datetime(2026, 7, 25, tzinfo=dt.timezone.utc)  # noqa: E731

CREDS = dict(api_key="k", api_secret="ks", access_token="at", access_secret="ats")


def _pieza(**over):
    base = {
        "id": "2026-07-25-x", "pilar": "A", "estado": "approved",
        "destinos": ["twitter"], "titulo": "t", "cuerpo": "Hola X", "hashtags": ["devops"],
    }
    base.update(over)
    return Pieza.model_validate(base)


def _pub(handler, **over):
    kw = dict(CREDS, max_chars=280, clock=CLOCK, nonce_fn=lambda: "NONCE")
    kw.update(over)
    return TwitterPublisher(client=httpx.Client(transport=httpx.MockTransport(handler)), **kw)


def test_config_error_sin_credenciales():
    with pytest.raises(TwitterConfigError):
        TwitterPublisher(api_key="", api_secret="", access_token="", access_secret="")


def test_oauth1_header_deterministico_y_firmado():
    h = _oauth1_header(
        "POST", "https://api.twitter.com/2/tweets",
        api_key="k", api_secret="ks", access_token="at", access_secret="ats",
        nonce="NONCE", timestamp="1700000000",
    )
    assert h.startswith("OAuth ")
    assert 'oauth_consumer_key="k"' in h
    assert 'oauth_signature="' in h
    assert 'oauth_signature_method="HMAC-SHA1"' in h


def test_publish_manda_texto_y_authorization():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json
        seen["auth"] = req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return httpx.Response(201, json={"data": {"id": "999", "text": "Hola X"}})

    result = _pub(handler).publish(_pieza())
    assert seen["auth"].startswith("OAuth ")
    assert seen["body"]["text"].startswith("Hola X")
    assert "#devops" in seen["body"]["text"]
    assert result.post_id == "999"
    assert result.url.endswith("999")


def test_excede_280():
    with pytest.raises(TwitterError, match="excede el límite"):
        _pub(lambda r: httpx.Response(201)).publish(_pieza(cuerpo="x" * 300))


def test_assets_no_soportado_todavia():
    with pytest.raises(TwitterError, match="no está implementado"):
        _pub(lambda r: httpx.Response(201)).publish(_pieza(assets=[{"path": "x.png", "alt": "a"}]))


def test_usa_variante_twitter():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json
        seen["body"] = json.loads(req.content)
        return httpx.Response(201, json={"data": {"id": "1"}})

    p = _pieza(variantes={"twitter": {"cuerpo": "corto para X", "hashtags": []}})
    _pub(handler).publish(p)
    assert seen["body"]["text"] == "corto para X"
