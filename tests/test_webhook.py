"""Tests del webhook de n8n: contrato HTTP de /publish-due (8790) y /token-status (8791)."""

import datetime as dt
import importlib.util
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import httpx

# scripts/webhook.py no es parte del paquete; se carga por ruta.
_WH = Path(__file__).resolve().parent.parent / "scripts" / "webhook.py"
_spec = importlib.util.spec_from_file_location("posse_webhook", _WH)
webhook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(webhook)


class _FakeBundle:
    access_expires_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=40)).isoformat()


class _FakeStore:
    def load(self):
        return _FakeBundle()


def _serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def test_token_status_calcula_dias(monkeypatch):
    monkeypatch.setattr(webhook, "get_token_store", lambda: _FakeStore())
    data = webhook._token_status()
    assert data["valido"] is True
    assert 38 <= data["dias_restantes"] <= 40
    assert "días" in data["mensaje"]  # el parser de n8n busca 'N días'


def test_token_status_sin_tokens(monkeypatch):
    monkeypatch.setattr(webhook, "get_token_store", lambda: type("S", (), {"load": lambda s: None})())
    data = webhook._token_status()
    assert data["valido"] is False and data["dias_restantes"] is None


def test_token_status_endpoint(monkeypatch):
    monkeypatch.setattr(webhook, "TOKEN", "SECRET")
    monkeypatch.setattr(webhook, "get_token_store", lambda: _FakeStore())
    srv, port = _serve(webhook.TokenStatusHandler)
    try:
        base = f"http://127.0.0.1:{port}/token-status"
        assert httpx.get(base).status_code == 401  # sin token
        r = httpx.get(base, headers={"X-Posse-Token": "SECRET"})
        assert r.status_code == 200 and r.json()["valido"] is True
        # el read-only no acepta POST
        assert httpx.post(base, headers={"X-Posse-Token": "SECRET"}).status_code == 405
    finally:
        srv.shutdown()


def test_publish_due_endpoint(monkeypatch):
    monkeypatch.setattr(webhook, "TOKEN", "SECRET")
    llamado = {}

    def fake_due(dry_run=False):
        llamado["dry"] = dry_run
        return ["2026-07-28-x"]

    monkeypatch.setattr(webhook.publisher, "publish_due", fake_due)
    srv, port = _serve(webhook.PublishHandler)
    try:
        base = f"http://127.0.0.1:{port}/publish-due"
        assert httpx.post(base).status_code == 401  # sin token
        r = httpx.post(base + "?dry_run=1", headers={"X-Posse-Token": "SECRET"})
        assert r.status_code == 200
        assert r.json() == {"published": ["2026-07-28-x"], "dry_run": True}
        assert llamado["dry"] is True
    finally:
        srv.shutdown()
