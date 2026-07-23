"""Schema tipado de la pieza de contenido (fuente de verdad)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

# Plataformas soportadas hoy. Agregar una red = sumar su Publisher en platforms/ y su clave aca.
PLATAFORMAS_CONOCIDAS: frozenset[str] = frozenset({"linkedin"})


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


class DestinoPublicado(BaseModel):
    """Resultado de una publicacion en una plataforma (o nulls si aun no se publico)."""

    model_config = ConfigDict(extra="forbid")

    fecha: str | None = None
    url: str | None = None
    post_id: str | None = None


class Asset(BaseModel):
    """Un archivo adjunto (imagen). path = ruta relativa al repo; alt = texto alternativo."""

    model_config = ConfigDict(extra="forbid")

    path: str
    alt: str | None = None

    @field_validator("path")
    @classmethod
    def _path_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("path no puede estar vacio")
        return v


class Pieza(BaseModel):
    """Una pieza de contenido versionada. Es la unidad de la fuente de verdad."""

    model_config = ConfigDict(extra="forbid")

    id: str  # <fecha>-<slug>
    pilar: Pilar
    estado: Estado = Estado.DRAFT
    destinos: list[str]
    titulo: str
    cuerpo: str
    assets: list[Asset] = []
    hashtags: list[str] = []
    publicado: dict[str, DestinoPublicado] = {}

    @field_validator("id", "titulo", "cuerpo")
    @classmethod
    def _no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("no puede estar vacio")
        return v

    @field_validator("destinos")
    @classmethod
    def _destinos_conocidos(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("destinos no puede estar vacio")
        desconocidos = sorted(set(v) - PLATAFORMAS_CONOCIDAS)
        if desconocidos:
            raise ValueError(f"destinos desconocidos: {desconocidos}")
        return v

    def esta_publicado_en(self, plataforma: str) -> bool:
        """True si la pieza ya tiene un post_id en esa plataforma (para idempotencia)."""
        destino = self.publicado.get(plataforma)
        return bool(destino and destino.post_id)
