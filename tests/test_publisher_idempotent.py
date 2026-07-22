"""Tests del publisher: gate, publicacion e idempotencia. HTTP mockeado."""

import httpx
import pytest

from posse import content_store, publisher
from posse.auth.token_store import TokenBundle
from posse.config import Settings
from posse.models import Estado

SETTINGS = Settings(_env_file=None, linkedin_version="202506")

FRESH = TokenBundle(
    access_token="AT",
    refresh_token="RT",
    access_expires_at="2099-01-01T00:00:00+00:00",  # no vencido -> no refresca
    refresh_expires_at="2099-01-01T00:00:00+00:00",
    person_urn="urn:li:person:abc",
)

APPROVED_YAML = """\
id: 2026-07-22-x
pilar: A
estado: approved
destinos: [linkedin]
titulo: t
cuerpo: |
  hola
assets: []
hashtags: []
publicado:
  linkedin: { fecha: null, url: null, post_id: null }
"""


class FakeStore:
    def __init__(self, bundle):
        self._b = bundle

    def load(self):
        return self._b

    def save(self, b):
        self._b = b


@pytest.fixture
def approved(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text(APPROVED_YAML, encoding="utf-8")
    return p


def _client(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:1"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_publica_approved_y_marca_published(approved):
    calls = []
    publisher.publish(approved, settings=SETTINGS, store=FakeStore(FRESH), client=_client(calls))
    assert len(calls) == 1
    p = content_store.load(approved)
    assert p.estado is Estado.PUBLISHED
    assert p.publicado["linkedin"].post_id == "urn:li:share:1"


def test_idempotente_no_republica(approved):
    calls = []
    publisher.publish(approved, settings=SETTINGS, store=FakeStore(FRESH), client=_client(calls))
    publisher.publish(approved, settings=SETTINGS, store=FakeStore(FRESH), client=_client(calls))
    assert len(calls) == 1  # la segunda corrida no vuelve a postear


def test_draft_no_publica_gate(tmp_path):
    d = tmp_path / "d.yaml"
    d.write_text(APPROVED_YAML.replace("estado: approved", "estado: draft"), encoding="utf-8")
    with pytest.raises(publisher.GateError):
        publisher.publish(d, settings=SETTINGS, store=FakeStore(FRESH), client=_client([]))
