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


def save_new(pieza: Pieza, content_dir: str | Path) -> Path:
    """Escribe una pieza nueva en content_dir como <id>.yaml. Si el id ya existe,
    agrega un sufijo -2, -3, ... para no pisar. Devuelve la ruta escrita."""
    d = Path(content_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{pieza.id}.yaml"
    i = 2
    while path.exists():
        path = d / f"{pieza.id}-{i}.yaml"
        i += 1
    with path.open("w", encoding="utf-8") as f:
        _yaml_rt.dump(pieza.model_dump(mode="json"), f)
    return path


def add_asset(path: str | Path, asset_path: str, alt: str | None = None) -> None:
    """Agrega un asset {path, alt} a la lista `assets` de la pieza, preservando formato."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = _yaml_rt.load(f)
    assets = data.get("assets")
    if not assets:
        assets = []
        data["assets"] = assets
    assets.append({"path": asset_path, "alt": alt})
    with p.open("w", encoding="utf-8") as f:
        _yaml_rt.dump(data, f)


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
