#!/usr/bin/env python
"""Webhook mínimo para que n8n dispare el auto-publish (`publish-due`).

n8n: nodo Schedule (ej. diario 9:00) -> nodo HTTP Request
     POST http://<host>:8790/publish-due
     Header:  X-Posse-Token: <POSSE_WEBHOOK_TOKEN>

Responde JSON {"published": [...ids...]}. Sin dependencias extra (http.server de stdlib).
Corré:  POSSE_WEBHOOK_TOKEN=... ./.venv/bin/python scripts/webhook.py --port 8790

Alternativa sin webhook: nodo Execute Command / SSH en n8n corriendo `posse publish-due`
directamente en el host donde está instalado posse. Ver docs/AUTO-PUBLISH.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from posse import logging_conf, publisher

log = logging.getLogger("posse.webhook")

TOKEN = os.environ.get("POSSE_WEBHOOK_TOKEN", "")


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (firma de BaseHTTPRequestHandler)
        if not TOKEN:
            self._json(500, {"error": "POSSE_WEBHOOK_TOKEN no configurado en el server"})
            return
        if self.headers.get("X-Posse-Token") != TOKEN:
            log.warning("webhook: token inválido desde %s", self.client_address[0])
            self._json(401, {"error": "token inválido"})
            return
        if self.path.rstrip("/") != "/publish-due":
            self._json(404, {"error": "ruta desconocida (usá /publish-due)"})
            return
        dry = "dry_run=1" in (self.path.split("?", 1)[1] if "?" in self.path else "")
        try:
            ids = publisher.publish_due(dry_run=dry)
            log.info("webhook: publish-due -> %s", ids or "(ninguna)")
            self._json(200, {"published": ids, "dry_run": dry})
        except Exception as e:  # noqa: BLE001 — devolver el error al caller (n8n) sin tumbar el server
            log.exception("webhook: publish-due falló")
            self._json(500, {"error": str(e)})

    def log_message(self, *args) -> None:  # silenciar el log HTTP default (usamos el nuestro)
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Webhook de auto-publish para n8n")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--host", default="0.0.0.0")  # noqa: S104 — LAN/homelab; poné 127.0.0.1 si n8n es local
    args = ap.parse_args()

    logging_conf.setup()
    if not TOKEN:
        log.error("POSSE_WEBHOOK_TOKEN no está seteado; el webhook rechazará todo. Exportalo y reiniciá.")
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    log.info("webhook escuchando en http://%s:%d/publish-due", args.host, args.port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        log.info("webhook detenido")
        srv.shutdown()


if __name__ == "__main__":
    main()
