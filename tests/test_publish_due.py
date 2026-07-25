"""Tests de publish_due (auto-publish por fecha `programado`). HTTP mockeado."""

import datetime as dt

import httpx
import pytest

from posse import publisher
from posse.auth.token_store import TokenBundle
from posse.config import Settings

FRESH = TokenBundle(
    access_token="AT", refresh_token="RT",
    access_expires_at="2099-01-01T00:00:00+00:00",
    refresh_expires_at="2099-01-01T00:00:00+00:00",
    person_urn="urn:li:person:abc",
)

HOY = dt.date(2026, 7, 28)


def _yaml(idx, estado, programado):
    prog = f"programado: {programado}\n" if programado else ""
    return f"""\
id: 2026-07-28-{idx}
pilar: A
estado: {estado}
destinos: [linkedin]
titulo: t
cuerpo: |
  hola
{prog}publicado:
  linkedin: {{ fecha: null, url: null, post_id: null }}
"""


class FakeStore:
    def __init__(self, b): self._b = b
    def load(self): return self._b
    def save(self, b): self._b = b


def _client(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:1"})
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def content_dir(tmp_path):
    (tmp_path / "due.yaml").write_text(_yaml("due", "approved", "2026-07-28"), encoding="utf-8")
    (tmp_path / "past.yaml").write_text(_yaml("past", "approved", "2026-07-01"), encoding="utf-8")
    (tmp_path / "future.yaml").write_text(_yaml("future", "approved", "2026-08-15"), encoding="utf-8")
    (tmp_path / "draft.yaml").write_text(_yaml("draft", "draft", "2026-07-28"), encoding="utf-8")
    (tmp_path / "noprog.yaml").write_text(_yaml("noprog", "approved", None), encoding="utf-8")
    return tmp_path


def _settings(content_dir):
    return Settings(_env_file=None, linkedin_version="202506", content_dir=str(content_dir))


def test_publica_solo_approved_y_vencidas(content_dir):
    calls = []
    ids = publisher.publish_due(
        settings=_settings(content_dir), store=FakeStore(FRESH), client=_client(calls), today=HOY,
    )
    # due (=hoy) y past (<hoy); NO future, NO draft, NO sin-programar
    assert sorted(ids) == ["2026-07-28-due", "2026-07-28-past"]
    assert len(calls) == 2


def test_dry_run_no_publica(content_dir):
    calls = []
    ids = publisher.publish_due(
        settings=_settings(content_dir), store=FakeStore(FRESH), client=_client(calls),
        today=HOY, dry_run=True,
    )
    assert sorted(ids) == ["2026-07-28-due", "2026-07-28-past"]
    assert len(calls) == 0  # dry-run no toca la API


def test_idempotente_segunda_corrida_no_republica(content_dir):
    s = _settings(content_dir)
    publisher.publish_due(settings=s, store=FakeStore(FRESH), client=_client([]), today=HOY)
    calls = []
    ids = publisher.publish_due(settings=s, store=FakeStore(FRESH), client=_client(calls), today=HOY)
    assert ids == []  # ya publicadas
    assert len(calls) == 0
