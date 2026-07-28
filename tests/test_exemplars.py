"""Tests del few-shot de estilo + arco de serie (exemplars)."""

from posse import exemplars
from posse.config import Settings
from posse.models import Pieza


def _pieza_yaml(idx, estado, pilar="A", titulo="t", cuerpo="hola"):
    return f"""\
id: 2026-07-{idx}-x
pilar: {pilar}
estado: {estado}
destinos: [linkedin]
titulo: '{titulo}'
cuerpo: |
  {cuerpo}
publicado:
  linkedin: {{ fecha: null, url: null, post_id: null }}
"""


def _settings(content_dir, **kw):
    return Settings(_env_file=None, content_dir=str(content_dir), **kw)


def test_load_publicadas_filtra_y_ordena_desc(tmp_path):
    (tmp_path / "a.yaml").write_text(_pieza_yaml(20, "published", titulo="vieja"), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(_pieza_yaml(25, "published", titulo="nueva"), encoding="utf-8")
    (tmp_path / "c.yaml").write_text(_pieza_yaml(26, "draft", titulo="draft"), encoding="utf-8")
    (tmp_path / "d.yaml").write_text(_pieza_yaml(27, "approved", titulo="approved"), encoding="utf-8")

    pub = exemplars.load_publicadas(_settings(tmp_path), limite=5)
    titulos = [p.titulo for p in pub]
    assert titulos == ["nueva", "vieja"]  # solo published, más reciente primero


def test_load_publicadas_filtra_por_pilar(tmp_path):
    (tmp_path / "a.yaml").write_text(_pieza_yaml(20, "published", pilar="A", titulo="a"), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(_pieza_yaml(21, "published", pilar="B", titulo="b"), encoding="utf-8")
    pub = exemplars.load_publicadas(_settings(tmp_path), pilar="A")
    assert [p.titulo for p in pub] == ["a"]


def test_load_publicadas_respeta_limite(tmp_path):
    for i in range(20, 25):
        (tmp_path / f"{i}.yaml").write_text(_pieza_yaml(i, "published", titulo=f"p{i}"), encoding="utf-8")
    assert len(exemplars.load_publicadas(_settings(tmp_path), limite=2)) == 2


def test_render_fewshot_incluye_cuerpo_y_acota():
    p = Pieza.model_validate(
        {"id": "x", "pilar": "A", "estado": "published", "destinos": ["linkedin"],
         "titulo": "Mi título", "cuerpo": "linea uno del cuerpo"}
    )
    out = exemplars.render_fewshot([p], max_chars=10_000)
    assert "Mi título" in out and "linea uno del cuerpo" in out
    # acotado
    assert len(exemplars.render_fewshot([p], max_chars=15)) == 15


def test_render_serie_orden_cronologico():
    nueva = Pieza.model_validate({"id": "x", "pilar": "A", "estado": "published", "destinos": ["linkedin"], "titulo": "nueva", "cuerpo": "c"})
    vieja = Pieza.model_validate({"id": "y", "pilar": "A", "estado": "published", "destinos": ["linkedin"], "titulo": "vieja", "cuerpo": "c"})
    # load_publicadas devuelve más nueva primero; render_serie las muestra cronológico (vieja -> nueva)
    serie = exemplars.render_serie([nueva, vieja])
    assert serie.index("vieja") < serie.index("nueva")


def test_augment_system_agrega_ejemplos_y_serie(tmp_path):
    (tmp_path / "a.yaml").write_text(
        _pieza_yaml(23, "published", titulo="Homelab con IA", cuerpo="Un post real."), encoding="utf-8"
    )
    system = exemplars.augment_system("BASE", _settings(tmp_path), pilar="A")
    assert "BASE" in system
    assert "EJEMPLOS DE TU ESTILO" in system
    assert "Homelab con IA" in system
    assert "ARCO DE LA SERIE" in system


def test_augment_system_sin_publicadas_no_cambia(tmp_path):
    (tmp_path / "d.yaml").write_text(_pieza_yaml(23, "draft"), encoding="utf-8")
    assert exemplars.augment_system("BASE", _settings(tmp_path)) == "BASE"
