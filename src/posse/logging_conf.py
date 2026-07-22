"""Configuracion de logging (cada intento: exito/error + codigo de respuesta)."""

from __future__ import annotations

import logging


def setup(level: int = logging.INFO) -> logging.Logger:
    """Configura el logging del pipeline (consola) y devuelve el logger raiz `posse`."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger("posse")
