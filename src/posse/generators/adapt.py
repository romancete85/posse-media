"""Adaptar una pieza a otra red (cross-post POSSE): reescribe el cuerpo al límite del destino.

El cuerpo de LinkedIn suele ser largo; Mastodon (500) y X (280) necesitan una versión más corta.
`adapt` genera esa variante con el LLM (Ollama por defecto) y la guarda en variantes[destino].
El gate humano sigue intacto: revisás la variante antes de publicar.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from posse import content_store
from posse.config import Settings, get_settings
from posse.generators import llm

# Margen para no pasarnos del límite duro de la red (el modelo no cuenta chars perfecto).
_MARGEN = 20


class AdaptOut(BaseModel):
    cuerpo: str
    hashtags: list[str]


def _limite(destino: str, settings: Settings) -> int:
    if destino == "mastodon":
        return settings.mastodon_max_chars
    if destino == "twitter":
        return settings.twitter_max_chars
    return 3000  # LinkedIn: sin límite práctico para el cuerpo


def _system(destino: str, limite: int) -> str:
    return (
        f"Adaptás un post ya escrito (de LinkedIn) al formato de {destino}. Reescribilo para que "
        f"el TOTAL (cuerpo + hashtags) entre en {limite - _MARGEN} caracteres, manteniendo el "
        "mensaje central y el gancho de la primera línea. Usá SIEMPRE voseo rioplatense (vos, "
        "tenés, podés); NUNCA 'tú' ni 'vosotros'. Menos es más: cortá lo accesorio, no inventes. "
        "Devolvé el cuerpo listo para publicar SIN hashtags adentro; los hashtags SOLO en su campo, "
        "sin el '#' (pocos, 2-3)."
    )


def adapt(
    path: str | Path,
    destino: str,
    *,
    settings: Settings | None = None,
    client=None,
) -> AdaptOut:
    """Genera (no guarda) la versión adaptada del cuerpo de la pieza para `destino`."""
    settings = settings or get_settings()
    pieza = content_store.load(path)
    limite = _limite(destino, settings)
    tags = ", ".join(pieza.hashtags) if pieza.hashtags else "(ninguno)"
    prompt = (
        f"Post original de LinkedIn (título interno: {pieza.titulo}):\n\n{pieza.cuerpo}\n\n"
        f"Hashtags disponibles: {tags}\n\nAdaptá este post para {destino} ({limite} chars máx)."
    )
    return llm.generate_structured(
        prompt,
        AdaptOut,
        system=_system(destino, limite),
        max_tokens=2000,
        settings=settings,
        client=client,
    )


def adapt_to_file(
    path: str | Path,
    destino: str,
    *,
    settings: Settings | None = None,
    client=None,
) -> AdaptOut:
    """Genera la variante y la guarda en variantes[destino] de la pieza. Devuelve lo generado."""
    settings = settings or get_settings()
    out = adapt(path, destino, settings=settings, client=client)
    content_store.set_variante(path, destino, cuerpo=out.cuerpo, hashtags=out.hashtags)
    return out
