"""Render de 'que se va a publicar exactamente' — para revisar antes del gate.

Se usa en el CLI (local) y en el workflow (comentario del PR).
SCAFFOLD: firma y contrato; logica en Fase 1.
"""

from __future__ import annotations

from pathlib import Path


def render(path: str | Path) -> str:
    """Devuelve un texto legible con el contenido exacto que se publicaria (titulo, cuerpo,
    hashtags, destinos, assets). No publica nada."""
    raise NotImplementedError("TODO(Fase 1)")
