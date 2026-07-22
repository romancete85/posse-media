"""Render de 'que se va a publicar exactamente' — para revisar antes del gate.

Se usa en el CLI (local) y en el workflow (comentario del PR).
"""

from __future__ import annotations

from pathlib import Path

from posse import content_store


def render(path: str | Path) -> str:
    """Devuelve un texto legible con el contenido exacto que se publicaria."""
    p = content_store.load(path)
    hashtags = " ".join(p.hashtags) if p.hashtags else "(ninguno)"
    assets = ", ".join(p.assets) if p.assets else "(ninguno)"
    return "\n".join(
        [
            "──────── se publicaria ────────",
            f"id:       {p.id}",
            f"pilar:    {p.pilar.value}",
            f"estado:   {p.estado.value}",
            f"destinos: {', '.join(p.destinos)}",
            f"titulo:   {p.titulo}",
            "cuerpo:",
            p.cuerpo.rstrip(),
            f"hashtags: {hashtags}",
            f"assets:   {assets}",
            "───────────────────────────────",
        ]
    )
