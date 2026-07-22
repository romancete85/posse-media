"""Contrato multi-plataforma (el seam de extensibilidad POSSE).

Cada red social implementa Publisher. El publisher del pipeline resuelve el destino
(`destinos:` de la pieza) contra un registry keyed by nombre de plataforma.

SCAFFOLD: contrato; implementaciones en platforms/<red>.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class PublishResult:
    """Resultado de publicar en una plataforma."""

    fecha: str
    url: str
    post_id: str


class Publisher(Protocol):
    """Contrato que implementa cada plataforma."""

    name: str  # clave del destino, ej. "linkedin"

    def publish(self, pieza: "object") -> PublishResult:
        """Publica la pieza y devuelve fecha/url/post_id. No toca el archivo (eso lo hace content_store)."""
        ...


# TODO(Fase 1): registry {name -> Publisher} + get_publisher(name) para resolver los destinos.
