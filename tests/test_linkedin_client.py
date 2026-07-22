"""Tests del cliente LinkedIn con HTTP mockeado (MockTransport). Nunca la API real."""

import datetime as dt
import json

import httpx
import pytest

from posse.models import Pieza
from posse.platforms.linkedin import (
    LinkedInAuthError,
    LinkedInError,
    LinkedInPermissionError,
    LinkedInPublisher,
    LinkedInRateLimitError,
)

PIEZA = Pieza.model_validate(
    {
        "id": "2026-07-22-x",
        "pilar": "A",
        "estado": "approved",
        "destinos": ["linkedin"],
        "titulo": "t",
        "cuerpo": "Hola mundo",
        "hashtags": ["devops", "#cloud"],
    }
)

CLOCK = lambda: dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)  # noqa: E731


def _pub(handler, clock=CLOCK):
    return LinkedInPublisher(
        access_token="AT",
        person_urn="urn:li:person:abc",
        version="202506",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        clock=clock,
    )


def test_publish_envia_headers_body_y_devuelve_resultado():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"] = request.headers
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:99"})

    result = _pub(handler).publish(PIEZA)

    assert seen["headers"]["linkedin-version"] == "202506"
    assert seen["headers"]["x-restli-protocol-version"] == "2.0.0"
    assert seen["headers"]["authorization"] == "Bearer AT"
    assert seen["body"]["author"] == "urn:li:person:abc"
    assert seen["body"]["lifecycleState"] == "PUBLISHED"
    # hashtags: normaliza 'devops' -> '#devops' y respeta '#cloud'
    assert "#devops" in seen["body"]["commentary"] and "#cloud" in seen["body"]["commentary"]
    assert result.post_id == "urn:li:share:99"
    assert result.url.endswith("urn:li:share:99")
    assert result.fecha == "2026-07-22T00:00:00+00:00"


def test_401_auth():
    with pytest.raises(LinkedInAuthError):
        _pub(lambda r: httpx.Response(401, json={"m": "x"})).publish(PIEZA)


def test_403_permiso():
    with pytest.raises(LinkedInPermissionError):
        _pub(lambda r: httpx.Response(403, json={"m": "x"})).publish(PIEZA)


def test_429_rate_limit():
    with pytest.raises(LinkedInRateLimitError):
        _pub(lambda r: httpx.Response(429, text="rate")).publish(PIEZA)


def test_ok_sin_id_falla():
    with pytest.raises(LinkedInError):
        _pub(lambda r: httpx.Response(201)).publish(PIEZA)  # sin x-restli-id ni body
