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
    "Ingeniero de Cloud Security / DevOps; tono profesional cercano, español rioplatense. Cada post: "
    "título breve (metadata), cuerpo listo para publicar, y hashtags sin el '#'."
)


class RepurposeOut(BaseModel):
    piezas: list[DraftOut]


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
