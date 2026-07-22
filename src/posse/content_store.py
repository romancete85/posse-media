"""Load / validate / reescritura in-place de las piezas YAML (fuente de verdad).

Dos loaders:
  - safe  : tipos plano (dict/list/str/None) para validar contra el schema.
  - rt    : round-trip de ruamel, preserva comentarios/formato al reescribir.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from posse.models import Estado, Pieza

_yaml_safe = YAML(typ="safe")  # lectura/validacion -> tipos plano
_yaml_rt = YAML()  # round-trip -> preserva comentarios al escribir
_yaml_rt.preserve_quotes = True


def load(path: str | Path) -> Pieza:
    """Carga y valida una pieza desde su archivo YAML."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = _yaml_safe.load(f)
    return Pieza.model_validate(data)


def validate(path: str | Path) -> None:
    """Valida el schema de una pieza. Lanza ValidationError si es invalida."""
    load(path)


def marcar_publicado(
    path: str | Path,
    plataforma: str,
    *,
    fecha: str,
    url: str,
    post_id: str,
) -> None:
    """Reescribe la pieza in-place: estado -> published y publicado[plataforma] con los datos.

    Preserva comentarios/formato (ruamel round-trip). Es lo que commitea de vuelta el workflow.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = _yaml_rt.load(f)

    data["estado"] = Estado.PUBLISHED.value
    publicado = data.setdefault("publicado", {})
    destino = publicado.setdefault(plataforma, {})
    destino["fecha"] = fecha
    destino["url"] = url
    destino["post_id"] = post_id

    with p.open("w", encoding="utf-8") as f:
        _yaml_rt.dump(data, f)
