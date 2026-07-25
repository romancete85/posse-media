"""Tests del log manual de métricas: modelo, store round-trip y reporte."""

from posse import content_store, report
from posse.models import Metrica, Pieza

PIEZA_YAML = """\
# cabecera que debe sobrevivir
id: 2026-07-23-uno
pilar: A
estado: published
destinos: [linkedin]
titulo: t
cuerpo: |
  hola
publicado:
  linkedin: { fecha: '2026-07-23', url: u, post_id: urn:li:share:1 }
"""


def test_metrica_engagement_y_rate():
    m = Metrica(impresiones=1000, reacciones=20, comentarios=5, clics=25)
    assert m.engagement == 50
    assert abs(m.engagement_rate - 0.05) < 1e-9


def test_metrica_sin_impresiones_rate_none():
    assert Metrica(reacciones=3).engagement_rate is None
    assert Metrica().engagement is None


def test_set_metricas_round_trip(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text(PIEZA_YAML, encoding="utf-8")
    content_store.set_metricas(
        p, "linkedin", fecha="2026-07-25",
        valores={"impresiones": 1200, "comentarios": 4},
    )
    assert "cabecera que debe sobrevivir" in p.read_text(encoding="utf-8")  # preserva comentario
    pieza = content_store.load(p)
    m = pieza.metricas["linkedin"]
    assert m.impresiones == 1200 and m.comentarios == 4 and m.fecha == "2026-07-25"


def test_metricas_destino_desconocido_en_modelo_ok_pero_report_filtra(tmp_path):
    # el modelo no restringe claves de métricas; el reporte filtra por plataforma pedida
    pieza = Pieza.model_validate(
        {
            "id": "x", "pilar": "A", "estado": "published", "destinos": ["linkedin"],
            "titulo": "t", "cuerpo": "c",
            "metricas": {"linkedin": {"impresiones": 500, "reacciones": 10}},
        }
    )
    assert pieza.metricas["linkedin"].impresiones == 500


def test_report_ordena_y_resume(tmp_path):
    (tmp_path / "a.yaml").write_text(
        PIEZA_YAML.replace("2026-07-23-uno", "2026-07-23-a"), encoding="utf-8"
    )
    (tmp_path / "b.yaml").write_text(
        PIEZA_YAML.replace("2026-07-23-uno", "2026-07-23-b"), encoding="utf-8"
    )
    content_store.set_metricas(tmp_path / "a.yaml", "linkedin", fecha="2026-07-25", valores={"impresiones": 100, "reacciones": 10})
    content_store.set_metricas(tmp_path / "b.yaml", "linkedin", fecha="2026-07-25", valores={"impresiones": 900, "reacciones": 9})
    out = report.render(tmp_path, "linkedin")
    # b (900 impr) va antes que a (100 impr) por orden desc
    assert out.index("2026-07-23-b") < out.index("2026-07-23-a")
    assert "Engagement rate promedio por pilar" in out
    assert "pilar A" in out


def test_report_sin_metricas(tmp_path):
    (tmp_path / "a.yaml").write_text(PIEZA_YAML, encoding="utf-8")
    out = report.render(tmp_path, "linkedin")
    assert "sin métricas cargadas" in out
