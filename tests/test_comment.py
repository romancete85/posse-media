"""Tests del comentario (Comments API). HTTP mockeado — nunca la API real."""

import json

import httpx
import pytest

from posse import content_store, publisher
from posse.auth.token_store import TokenBundle
from posse.config import Settings
from posse.models import Pieza
from posse.platforms.linkedin import LinkedInPublisher

SETTINGS = Settings(_env_file=None, linkedin_version="202606")
FRESH = TokenBundle(
    access_token="AT", refresh_token="RT",
    access_expires_at="2099-01-01T00:00:00+00:00", refresh_expires_at="2099-01-01T00:00:00+00:00",
    person_urn="urn:li:person:abc",
)

PUBLISHED_YAML = """\
id: 2026-07-23-x
pilar: A
estado: published
destinos: [linkedin]
titulo: t
cuerpo: |
  hola
assets: []
hashtags: []
publicado:
  linkedin: { fecha: '2026-07-23', url: 'https://x', post_id: 'urn:li:share:99' }
"""


class FakeStore:
    def __init__(self, b):
        self._b = b

    def load(self):
        return self._b

    def save(self, b):
        self._b = b


def test_client_comment_postea_a_socialactions():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, headers={"x-restli-id": "urn:li:comment:1"})

    pub = LinkedInPublisher(
        access_token="AT", person_urn="urn:li:person:abc", version="202606",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    urn = pub.comment("urn:li:share:99", "mirá (esto) 👉 https://claude.ai/x")

    # el share urn va URL-encodeado en el path
    assert "urn%3Ali%3Ashare%3A99/comments" in seen["url"]
    assert seen["body"]["actor"] == "urn:li:person:abc"
    assert r"\(esto\)" in seen["body"]["message"]["text"]   # texto escapado
    assert "https://claude.ai/x" in seen["body"]["message"]["text"]  # URL intacta
    assert urn == "urn:li:comment:1"


def test_publisher_comment_usa_post_id(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text(PUBLISHED_YAML, encoding="utf-8")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(201, headers={"x-restli-id": "urn:li:comment:9"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    urn = publisher.comment(p, "hola", settings=SETTINGS, store=FakeStore(FRESH), client=client)
    assert urn == "urn:li:comment:9"
    assert "urn%3Ali%3Ashare%3A99/comments" in calls[0]


def test_publisher_comment_falla_si_no_publicada(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text(
        PUBLISHED_YAML.replace("estado: published", "estado: draft").replace(
            "post_id: 'urn:li:share:99'", "post_id: null"
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError):
        publisher.comment(p, "hola", settings=SETTINGS, store=FakeStore(FRESH), client=httpx.Client())
