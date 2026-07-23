"""Tests del backlog (posse list)."""

from posse import backlog, content_store
from posse.generators.draft import DraftOut, build_pieza

APPROVED = """\
id: 2026-07-23-aprobada
pilar: A
estado: approved
destinos: [linkedin]
titulo: Pieza aprobada
cuerpo: |
  x
assets: []
hashtags: []
publicado:
  linkedin: { fecha: null, url: null, post_id: null }
"""


def test_backlog_cuenta_y_ordena(tmp_path):
    # draft, approved, published, e inválida
    content_store.save_new(build_pieza(DraftOut(titulo="Borrador", cuerpo="c"), "A", fecha="2026-07-23"), tmp_path)
    (tmp_path / "aprobada.yaml").write_text(APPROVED, encoding="utf-8")
    (tmp_path / "publicada.yaml").write_text(
        APPROVED.replace("estado: approved", "estado: published").replace("aprobada", "publicada"),
        encoding="utf-8",
    )
    (tmp_path / "rota.yaml").write_text("id: x\nestado: draft\n", encoding="utf-8")  # falta campos

    out = backlog.render(tmp_path)
    assert "approved:1" in out and "draft:1" in out and "published:1" in out and "INVÁLIDA:1" in out
    # approved aparece antes que published en el texto
    assert out.index("approved") < out.index("published")


def test_collect_marca_invalida(tmp_path):
    (tmp_path / "rota.yaml").write_text("id: x\n", encoding="utf-8")
    rows = backlog.collect(tmp_path)
    assert rows[0]["ok"] is False
