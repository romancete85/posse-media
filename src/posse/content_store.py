"""Load / validate / reescritura in-place de las piezas YAML (fuente de verdad).

Usa ruamel.yaml para preservar comentarios y formato al reescribir el estado publicado.
SCAFFOLD: firmas y contrato; logica en Fase 1.
"""

from __future__ import annotations

from pathlib import Path

# TODO(Fase 1): from ruamel.yaml import YAML ; from posse.models import Pieza, Estado


def load(path: str | Path) -> "object":
    """Carga y valida una pieza desde su archivo YAML. Devuelve una Pieza."""
    raise NotImplementedError("TODO(Fase 1): parsear YAML -> validar schema -> Pieza")


def validate(path: str | Path) -> None:
    """Valida el schema de una pieza. Lanza si es invalida."""
    raise NotImplementedError("TODO(Fase 1)")


def marcar_publicado(path: str | Path, plataforma: str, *, fecha: str, url: str, post_id: str) -> None:
    """Reescribe la pieza in-place: estado -> published y publicado[plataforma] con los datos.

    Preserva comentarios/formato del YAML (ruamel). Es lo que commitea de vuelta el workflow.
    """
    raise NotImplementedError("TODO(Fase 1): editar publicado[plataforma] + estado, dump preservando formato")
