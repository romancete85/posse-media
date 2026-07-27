#!/usr/bin/env python3
"""posse-setenv — actualiza claves permitidas de /opt/posse/.env desde stdin (guest CT 116).

Uso (en el guest):  printf 'LINKEDIN_CLIENT_ID=xxx\\nLINKEDIN_CLIENT_SECRET=yyy\\n' | posse-setenv

- Solo toca un allowlist de claves (nunca el resto del .env ni claves fuera de la lista).
- Preserva owner/modo del .env (posse:posse 0640) y escribe atomico.

Se instala como /usr/local/sbin/posse-setenv en el CT 116. Versionado acá para no perderlo en un rebuild.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

ENV_PATH = "/opt/posse/.env"
ALLOWED = {
    "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_VERSION",
    "MASTODON_INSTANCE", "MASTODON_ACCESS_TOKEN",
    "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
}


def main() -> int:
    updates: dict[str, str] = {}
    for raw in sys.stdin:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            print("posse-setenv: linea sin '=' ignorada", file=sys.stderr)
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key not in ALLOWED:
            print(f"posse-setenv: clave no permitida: {key}", file=sys.stderr)
            return 2
        updates[key] = val.strip()

    if not updates:
        print("posse-setenv: nada que hacer (stdin vacio)", file=sys.stderr)
        return 1

    with open(ENV_PATH, encoding="utf-8") as fh:
        lines = fh.readlines()

    pendientes = set(updates)
    for i, line in enumerate(lines):
        m = re.match(r"^([A-Z0-9_]+)=", line)
        if m and m.group(1) in updates:
            key = m.group(1)
            lines[i] = f"{key}={updates[key]}\n"
            pendientes.discard(key)

    if pendientes:
        print(f"posse-setenv: claves ausentes en {ENV_PATH}: {sorted(pendientes)}", file=sys.stderr)
        return 3

    st = os.stat(ENV_PATH)
    d = os.path.dirname(ENV_PATH)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".env.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
        shutil.copystat(ENV_PATH, tmp)
        os.chown(tmp, st.st_uid, st.st_gid)
        os.replace(tmp, ENV_PATH)
    except Exception:
        os.unlink(tmp)
        raise

    for key, val in sorted(updates.items()):
        print(f"posse-setenv: {key} actualizado (len={len(val)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
