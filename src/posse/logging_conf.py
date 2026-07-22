"""Configuracion de logging estructurado (cada intento: exito/error + codigo de respuesta).

SCAFFOLD: firma; logica en Fase 1.
"""

from __future__ import annotations

import logging


def setup(level: int = logging.INFO) -> logging.Logger:
    """Configura y devuelve el logger raiz del pipeline."""
    raise NotImplementedError("TODO(Fase 1): handler + formato consistente para CLI y Actions")
