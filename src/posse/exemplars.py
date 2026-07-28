"""Ejemplares de estilo + arco de serie para el grounding de la generación.

Toma las piezas YA PUBLICADAS como few-shot: le muestran al modelo tu voz real (hook fuerte,
estructura, CTA, framing de serie) para que los drafts salgan más cerca de lo publicable. Además
arma un resumen del arco de la serie para que el próximo post continúe coherente y no repita.

⚠️ Presupuesto: en Ollama/CPU un prompt más largo = generación más lenta. Se acota con
`exemplars_n` (cuántas piezas) y `exemplars_max_chars` (tope del bloque). Se puede apagar por pieza.
"""

from __future__ import annotations

from pathlib import Path

from posse import content_store
from posse.config import Settings, get_settings
from posse.models import Estado, Pieza


def load_publicadas(
    settings: Settings | None = None,
    *,
    pilar: str | None = None,
    limite: int = 2,
) -> list[Pieza]:
    """Piezas en estado 'published', más recientes primero (id empieza con la fecha)."""
    settings = settings or get_settings()
    piezas: list[Pieza] = []
    for p in sorted(Path(settings.content_dir).glob("*.yaml"), reverse=True):
        try:
            pieza = content_store.load(p)
        except Exception:  # noqa: BLE001 — un YAML inválido no debe romper la generación
            continue
        if pieza.estado is Estado.PUBLISHED and (pilar is None or pieza.pilar.value == pilar):
            piezas.append(pieza)
    return piezas[:limite]


def render_fewshot(piezas: list[Pieza], *, max_chars: int) -> str:
    """Bloque few-shot con el cuerpo de cada ejemplar (acotado a max_chars)."""
    if not piezas:
        return ""
    bloques = [f"### Ejemplo {i} — «{p.titulo}»\n{p.cuerpo.strip()}" for i, p in enumerate(piezas, 1)]
    return "\n\n".join(bloques)[:max_chars]


def render_serie(piezas: list[Pieza]) -> str:
    """Resumen del arco (orden cronológico) para que el nuevo post continúe sin repetir."""
    if not piezas:
        return ""
    items = "; ".join(f"«{p.titulo}»" for p in reversed(piezas))  # publicadas de la más vieja a la nueva
    return (
        f"ARCO DE LA SERIE (ya publicado, en orden): {items}. "
        "El nuevo post debe CONTINUAR el arco sin repetir lo ya dicho; puede referenciarlo brevemente."
    )


def augment_system(system: str, settings: Settings | None = None, *, pilar: str | None = None) -> str:
    """Agrega al system prompt los ejemplares de estilo + el arco de la serie (si hay publicadas)."""
    settings = settings or get_settings()
    piezas = load_publicadas(settings, pilar=pilar, limite=settings.exemplars_n)
    if not piezas:
        return system
    fewshot = render_fewshot(piezas, max_chars=settings.exemplars_max_chars)
    return (
        system
        + "\n\nEJEMPLOS DE TU ESTILO (posts YA publicados por el autor; imitá el TONO, la ESTRUCTURA "
        "—hook fuerte en la 1ª línea, desarrollo claro, CTA con pregunta al final— y el voseo "
        "rioplatense; NO copies el contenido, es referencia de FORMA):\n"
        + fewshot
        + "\n\n"
        + render_serie(piezas)
    )
