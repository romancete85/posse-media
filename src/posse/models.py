"""Schema tipado de la pieza de contenido (fuente de verdad).

SCAFFOLD: se define el contrato de datos (declarativo). Validadores/logica en Fase 1.
"""

from __future__ import annotations

from enum import Enum

# TODO(Fase 1): from pydantic import BaseModel, Field


class Estado(str, Enum):
    """Estados de una pieza. El gate: solo 'approved' se publica."""

    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


class Pilar(str, Enum):
    """Pilares de contenido de la marca."""

    A = "A"  # cloud/devops
    B = "B"  # mentoria
    C = "C"  # musica


# --- Contrato de la pieza (referencia; se materializa como modelos pydantic en Fase 1) ---
#
# class DestinoPublicado(BaseModel):
#     fecha: str | None = None
#     url: str | None = None
#     post_id: str | None = None
#
# class Pieza(BaseModel):
#     id: str                        # <fecha>-<slug>
#     pilar: Pilar
#     estado: Estado = Estado.DRAFT
#     destinos: list[str]            # ["linkedin", ...]
#     titulo: str
#     cuerpo: str
#     assets: list[str] = []
#     hashtags: list[str] = []
#     publicado: dict[str, DestinoPublicado]   # keyed by plataforma
#
#     def esta_publicado_en(self, plataforma: str) -> bool: ...   # idempotencia
#
# TODO(Fase 1): implementar Pieza/DestinoPublicado + validadores (id-slug, destinos conocidos, etc.).


class Pieza:  # placeholder hasta Fase 1
    """Pieza de contenido. Ver contrato arriba."""

    def esta_publicado_en(self, plataforma: str) -> bool:
        """True si la pieza ya fue publicada en `plataforma` (para idempotencia)."""
        raise NotImplementedError("TODO(Fase 1)")
