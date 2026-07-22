"""Orquestacion: pieza approved -> publish -> published. Idempotente.

Contrato:
  - Solo publica piezas en estado 'approved' (gate).
  - Si la pieza ya esta publicada en la plataforma (estado 'published' o publicado[p].post_id),
    NO republica (idempotencia).
  - Tras publicar OK, marca la pieza como 'published' con url/post_id/fecha (content_store).
  - Loguea cada intento (exito/error + codigo HTTP). No hace retry silencioso.

SCAFFOLD: firma y contrato; logica en Fase 1.
"""

from __future__ import annotations

from pathlib import Path


def publish(path: str | Path) -> None:
    """Publica una pieza approved en sus destinos y persiste el resultado. Idempotente."""
    raise NotImplementedError(
        "TODO(Fase 1): validar estado==approved -> por cada destino: skip si ya publicado, "
        "si no publicar via platforms + marcar_publicado"
    )
