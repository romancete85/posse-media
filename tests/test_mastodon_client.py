"""Tests del cliente Mastodon con HTTP mockeado (MockTransport). Nunca la API real."""

import datetime as dt

import httpx
import pytest

from posse.models import Pieza
from posse.platforms.mastodon import MastodonConfigError, MastodonError, MastodonPublisher

CLOCK = lambda: dt.datetime(2026, 7, 25, tzinfo=dt.timezone.utc)  # noqa: E731


def _pieza(**over):
    base = {
        "id": "2026-07-25-x", "pilar": "A", "estado": "approved",
        "destinos": ["mastodon"], "titulo": "t", "cuerpo": "Hola fediverso",
        "hashtags": ["devops", "#cloud"],
    }
    base.update(over)
    return Pieza.model_validate(base)


def _pub(handler, *, max_chars=500):
    return MastodonPublisher(
        instance="https://mastodon.social/",
        access_token="TOK",
        max_chars=max_chars,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        clock=CLOCK,
        sleep=lambda _s: None,
    )


def test_config_error_sin_credenciales():
    with pytest.raises(MastodonConfigError):
        MastodonPublisher(instance="", access_token="")


def test_publish_status_hashtags_e_idempotencia():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["path"] = req.url.path
        seen["idem"] = req.headers.get("idempotency-key")
        seen["auth"] = req.headers.get("authorization")
        import json
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"id": "12345", "url": "https://mastodon.social/@r/12345"})

    result = _pub(handler).publish(_pieza())

    assert seen["path"] == "/api/v1/statuses"
    assert seen["auth"] == "Bearer TOK"
    assert seen["idem"] == "2026-07-25-x"  # idempotencia = id de la pieza
    assert seen["body"]["visibility"] == "public"
    assert "#devops" in seen["body"]["status"] and "#cloud" in seen["body"]["status"]
    assert result.post_id == "12345"
    assert result.url == "https://mastodon.social/@r/12345"
    assert result.fecha == "2026-07-25T00:00:00+00:00"


def test_excede_limite_de_chars():
    with pytest.raises(MastodonError, match="excede el límite"):
        _pub(lambda r: httpx.Response(200), max_chars=10).publish(_pieza(cuerpo="x" * 40))


def test_usa_variante_si_existe():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"id": "1", "url": "u"})

    p = _pieza(variantes={"mastodon": {"cuerpo": "version corta para masto", "hashtags": ["fedi"]}})
    _pub(handler).publish(p)
    assert seen["body"]["status"].startswith("version corta para masto")
    assert "#fedi" in seen["body"]["status"]
    assert "#devops" not in seen["body"]["status"]  # usa los hashtags de la variante


def test_sube_media_con_alt_y_la_referencia():
    llamadas = []

    def handler(req: httpx.Request) -> httpx.Response:
        llamadas.append(req.url.path)
        if req.url.path == "/api/v2/media":
            return httpx.Response(200, json={"id": "media99"})
        import json
        body = json.loads(req.content)
        assert body["media_ids"] == ["media99"]
        return httpx.Response(200, json={"id": "1", "url": "u"})

    p = _pieza(assets=[{"path": __file__, "alt": "una imagen"}])  # __file__ existe como bytes
    _pub(handler).publish(p)
    assert "/api/v2/media" in llamadas


def test_401_da_error():
    with pytest.raises(MastodonError):
        _pub(lambda r: httpx.Response(401, text="unauth")).publish(_pieza())
