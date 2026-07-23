"""Genera una pieza draft a partir de un tema o nota. Upstream del gate."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from pydantic import BaseModel

from posse import content_store
from posse.config import Settings, get_settings
from posse.generators import llm
from posse.models import DestinoPublicado, Estado, Pieza, Pilar

_SYSTEM = (
    "Sos un asistente que redacta posts para el perfil personal de LinkedIn de un ingeniero "
    "de Cloud Security / DevOps. Tono profesional pero cercano, español rioplatense (voseo). "
    "Devolvé un título breve (metadata interna), el cuerpo del post (texto listo para publicar, "
    "sin el título adentro) y una lista corta de hashtags relevantes sin el '#'."
)


class DraftOut(BaseModel):
    """Lo que genera Claude (el resto de la pieza lo arma el pipeline)."""

    titulo: str
    cuerpo: str
    hashtags: list[str] = []


def _slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", texto.lower().strip())
    return re.sub(r"-+", "-", s).strip("-")[:50] or "pieza"


def build_pieza(out: DraftOut, pilar: str, *, destinos=("linkedin",), fecha: str | None = None) -> Pieza:
    """Ensambla una Pieza draft a partir de la salida del modelo."""
    fecha = fecha or dt.date.today().isoformat()
    return Pieza(
        id=f"{fecha}-{_slug(out.titulo)}",
        pilar=Pilar(pilar),
        estado=Estado.DRAFT,
        destinos=list(destinos),
        titulo=out.titulo,
        cuerpo=out.cuerpo,
        hashtags=out.hashtags,
        assets=[],
        publicado={d: DestinoPublicado() for d in destinos},
    )


def draft(
    tema: str,
    pilar: str,
    *,
    fecha: str | None = None,
    settings: Settings | None = None,
    client=None,
) -> Pieza:
    """Genera una pieza draft (no la escribe a disco)."""
    settings = settings or get_settings()
    out = llm.generate_structured(
        f"Tema o nota: {tema}\n\nRedactá un post.",
        DraftOut,
        system=_SYSTEM,
        settings=settings,
        client=client,
    )
    return build_pieza(out, pilar, fecha=fecha)


def draft_to_file(tema: str, pilar: str, *, settings: Settings | None = None, client=None) -> Path:
    """Genera y escribe la pieza draft en content/. Devuelve la ruta."""
    settings = settings or get_settings()
    pieza = draft(tema, pilar, settings=settings, client=client)
    return content_store.save_new(pieza, settings.content_dir)
