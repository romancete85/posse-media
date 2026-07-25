#!/usr/bin/env python
"""Webhooks para que n8n orqueste el pipeline. Dos listeners, separados por puerto a propósito:

  8790  POST /publish-due    (MUTA: publica)         -> workflow posse-publish-due
  8791  GET  /token-status   (READ-ONLY: solo lee)   -> workflow posse-token-check

Separar el read-only en otro puerto permite que el firewall/n8n traten distinto lo que muta de lo
que solo lee. Ambos exigen el header `X-Posse-Token: <POSSE_WEBHOOK_TOKEN>` (misma credencial).
Sin dependencias extra (http.server de stdlib).

Corré:  POSSE_WEBHOOK_TOKEN=... ./.venv/bin/python scripts/webhook.py --port 8790
(en el homelab lo levanta el servicio systemd `posse-webhook`, con el token en /etc/posse/webhook.env)

Contrato de respuestas (JSON):
  POST /publish-due[?dry_run=1] -> {"published": [...ids...], "dry_run": bool}
  GET  /token-status            -> {"valido": bool, "dias_restantes": int|null,
                                    "expira": str|null, "mensaje": str}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from posse import logging_conf, publisher
from posse.auth.token_store import get_token_store

log = logging.getLogger("posse.webhook")

TOKEN = os.environ.get("POSSE_WEBHOOK_TOKEN", "")


def _token_status() -> dict:
    """Estado del token de LinkedIn como dict serializable (lo consume el workflow token-check)."""
    bundle = get_token_store().load()
    if bundle is None:
        return {"valido": False, "dias_restantes": None, "expira": None,
                "mensaje": "sin tokens guardados; correr `posse auth` en el guest"}
    expira = dt.datetime.fromisoformat(bundle.access_expires_at)
    dias = (expira - dt.datetime.now(dt.timezone.utc)).days
    estado = "válido" if dias >= 0 else "VENCIDO"
    return {"valido": dias >= 0, "dias_restantes": dias, "expira": bundle.access_expires_at,
            "mensaje": f"token {estado}, {dias} días restantes"}


class _Base(BaseHTTPRequestHandler):
    """Base común: respuesta JSON, chequeo de token, log silencioso."""

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self) -> bool:
        if not TOKEN:
            self._json(500, {"error": "POSSE_WEBHOOK_TOKEN no configurado en el server"})
            return False
        if self.headers.get("X-Posse-Token") != TOKEN:
            log.warning("webhook: token inválido desde %s", self.client_address[0])
            self._json(401, {"error": "token inválido"})
            return False
        return True

    def log_message(self, *args) -> None:  # silencia el log HTTP default (usamos el nuestro)
        pass


class PublishHandler(_Base):
    """8790 — dispara publish-due (muta)."""

    def do_POST(self) -> None:  # noqa: N802 (firma de BaseHTTPRequestHandler)
        if not self._authed():
            return
        if self.path.split("?", 1)[0].rstrip("/") != "/publish-due":
            self._json(404, {"error": "ruta desconocida (usá POST /publish-due)"})
            return
        dry = "dry_run=1" in (self.path.split("?", 1)[1] if "?" in self.path else "")
        try:
            ids = publisher.publish_due(dry_run=dry)
            log.info("webhook: publish-due -> %s", ids or "(ninguna)")
            self._json(200, {"published": ids, "dry_run": dry})
        except Exception as e:  # noqa: BLE001 — devolver el error a n8n sin tumbar el server
            log.exception("webhook: publish-due falló")
            self._json(500, {"error": str(e)})

    def do_GET(self) -> None:  # noqa: N802 — 8790 no expone GET
        self._json(405, {"error": "usá el 8791 para /token-status"})


class TokenStatusHandler(_Base):
    """8791 — reporta el estado del token (read-only, no muta nada)."""

    def do_GET(self) -> None:  # noqa: N802
        if not self._authed():
            return
        if self.path.split("?", 1)[0].rstrip("/") != "/token-status":
            self._json(404, {"error": "ruta desconocida (usá GET /token-status)"})
            return
        try:
            self._json(200, _token_status())
        except Exception as e:  # noqa: BLE001
            log.exception("webhook: token-status falló")
            self._json(500, {"error": str(e)})

    def do_POST(self) -> None:  # noqa: N802 — el read-only no muta
        self._json(405, {"error": "este puerto es read-only; publicá por el 8790"})


def main() -> None:
    ap = argparse.ArgumentParser(description="Webhooks de orquestación para n8n")
    ap.add_argument("--port", type=int, default=8790, help="puerto de publish-due (muta)")
    ap.add_argument("--readonly-port", type=int, default=8791, help="puerto de token-status (read-only)")
    ap.add_argument("--host", default="0.0.0.0")  # noqa: S104 — LAN/homelab; el firewall dropea no-RFC1918
    args = ap.parse_args()

    logging_conf.setup()
    if not TOKEN:
        log.error("POSSE_WEBHOOK_TOKEN no está seteado; los webhooks rechazarán todo. Exportalo y reiniciá.")

    pub_srv = ThreadingHTTPServer((args.host, args.port), PublishHandler)
    ro_srv = ThreadingHTTPServer((args.host, args.readonly_port), TokenStatusHandler)
    log.info("webhook publish-due  en http://%s:%d/publish-due", args.host, args.port)
    log.info("webhook token-status en http://%s:%d/token-status", args.host, args.readonly_port)

    t = threading.Thread(target=pub_srv.serve_forever, daemon=True)
    t.start()
    try:
        ro_srv.serve_forever()  # el thread principal atiende el read-only
    except KeyboardInterrupt:
        log.info("webhook detenido")
        pub_srv.shutdown()
        ro_srv.shutdown()


if __name__ == "__main__":
    main()
