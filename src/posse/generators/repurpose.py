"""Repurposing: de una fuente larga (artículo/nota) -> N piezas draft distintas."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from posse import content_store
from posse.config import Settings, get_settings
from posse.generators import llm
from posse.generators.draft import DraftOut, build_pieza
from posse.models import Pieza

_SYSTEM = (
    "Sos un asistente que reconvierte una fuente larga (artículo, nota, transcripción) en varios "
    "posts breves y distintos para LinkedIn, cada uno con un ángulo o idea diferente (no repetir). "
    "Ingeniero de Cloud Security / DevOps; tono profesional cercano. Usá SIEMPRE voseo rioplatense "
    "(vos, tenés, podés); NUNCA 'vosotros'/'vuestro' ni 'tú'. Cada post: título breve (metadata, NO "
    "va dentro del post); cuerpo listo para publicar SIN el título y SIN hashtags adentro; y los "
    "hashtags SOLO en su campo, sin el '#'."
)


_SYSTEM_IDEAS = (
    "Sos un asistente que propone varias ideas de posts distintos para LinkedIn a partir de un tema, "
    "cada uno con un ángulo diferente (no repetir). Ingeniero de Cloud Security / DevOps; tono "
    "profesional cercano. Usá SIEMPRE voseo rioplatense (vos, tenés, podés); NUNCA 'vosotros'/'vuestro' "
    "ni 'tú'. Cada post: título breve (metadata, NO va dentro del post); cuerpo listo para publicar SIN "
    "el título y SIN hashtags adentro; y los hashtags SOLO en su campo, sin el '#'."
)


class RepurposeOut(BaseModel):
    piezas: list[DraftOut]


def ideas(
    tema: str,
    pilar: str,
    n: int,
    *,
    fecha: str | None = None,
    settings: Settings | None = None,
    client=None,
) -> list[Pieza]:
    """Genera N ideas de posts draft a partir de un tema (no las escribe a disco)."""
    settings = settings or get_settings()
    out = llm.generate_structured(
        f"Proponé {n} ideas de posts distintos (ángulos diferentes) sobre: {tema}",
        RepurposeOut,
        system=_SYSTEM_IDEAS,
        max_tokens=8000,
        settings=settings,
        client=client,
    )
    return [build_pieza(d, pilar, fecha=fecha) for d in out.piezas]


def ideas_to_files(
    tema: str, pilar: str, n: int, *, settings: Settings | None = None, client=None
) -> list[Path]:
    """Genera y escribe N ideas draft en content/. Devuelve las rutas."""
    settings = settings or get_settings()
    return [content_store.save_new(p, settings.content_dir) for p in ideas(tema, pilar, n, settings=settings, client=client)]


def repurpose(
    fuente: str,
    pilar: str,
    n: int,
    *,
    fecha: str | None = None,
    settings: Settings | None = None,
    client=None,
) -> list[Pieza]:
    """Genera N piezas draft desde la fuente (no las escribe a disco)."""
    settings = settings or get_settings()
    out = llm.generate_structured(
        f"Generá {n} posts distintos a partir de esta fuente.\n\nFUENTE:\n{fuente}",
        RepurposeOut,
        system=_SYSTEM,
        max_tokens=8000,
        settings=settings,
        client=client,
    )
    return [build_pieza(d, pilar, fecha=fecha) for d in out.piezas]


def repurpose_to_files(
    fuente: str,
    pilar: str,
    n: int,
    *,
    settings: Settings | None = None,
    client=None,
) -> list[Path]:
    """Genera y escribe N piezas draft en content/. Devuelve las rutas (ids únicos)."""
    settings = settings or get_settings()
    piezas = repurpose(fuente, pilar, n, settings=settings, client=client)
    return [content_store.save_new(p, settings.content_dir) for p in piezas]
