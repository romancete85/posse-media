"""Schema tipado de la pieza de contenido (fuente de verdad)."""

from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

# Plataformas soportadas hoy. Agregar una red = sumar su Publisher en platforms/ y su clave aca.
PLATAFORMAS_CONOCIDAS: frozenset[str] = frozenset({"linkedin", "mastodon", "twitter"})


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


class Variante(BaseModel):
    """Override de texto para un destino puntual (cross-post POSSE).

    Si una pieza va a varias redes, cada una puede tener su cuerpo/hashtags propios
    (ej. X con 280 chars). Si no hay variante para un destino, se usa el cuerpo principal.
    """

    model_config = ConfigDict(extra="forbid")

    cuerpo: str | None = None
    hashtags: list[str] | None = None


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
    # Auto-publicación: fecha (YYYY-MM-DD) a partir de la cual `publish-due` la publica si está approved.
    programado: str | None = None
    # Cross-post: overrides de texto por destino (ej. {"twitter": {cuerpo, hashtags}}).
    variantes: dict[str, Variante] = {}
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

    @field_validator("variantes")
    @classmethod
    def _variantes_conocidas(cls, v: dict[str, Variante]) -> dict[str, Variante]:
        desconocidos = sorted(set(v) - PLATAFORMAS_CONOCIDAS)
        if desconocidos:
            raise ValueError(f"variantes para destinos desconocidos: {desconocidos}")
        return v

    @field_validator("programado", mode="before")
    @classmethod
    def _programado_es_fecha(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, dt.date):  # el loader YAML parsea 2026-07-28 como date; datetime hereda de date
            return v.isoformat()[:10]
        try:
            dt.date.fromisoformat(v)  # type: ignore[arg-type]
        except (ValueError, TypeError) as e:
            raise ValueError(f"programado debe ser una fecha YYYY-MM-DD, no {v!r}") from e
        return v

    def esta_publicado_en(self, plataforma: str) -> bool:
        """True si la pieza ya tiene un post_id en esa plataforma (para idempotencia)."""
        destino = self.publicado.get(plataforma)
        return bool(destino and destino.post_id)

    def contenido_para(self, destino: str) -> tuple[str, list[str]]:
        """(cuerpo, hashtags) a publicar en `destino`: la variante si existe, si no el principal."""
        var = self.variantes.get(destino)
        cuerpo = var.cuerpo if (var and var.cuerpo) else self.cuerpo
        hashtags = var.hashtags if (var and var.hashtags is not None) else self.hashtags
        return cuerpo, hashtags

    def esta_programada_para(self, hoy: dt.date) -> bool:
        """True si tiene fecha `programado` y ya llegó (para publish-due)."""
        if not self.programado:
            return False
        return dt.date.fromisoformat(self.programado) <= hoy
