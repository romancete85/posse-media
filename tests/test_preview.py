"""Tests de preview.render."""

from posse import preview


def test_render_incluye_titulo_y_cuerpo(pieza_path):
    out = preview.render(pieza_path)
    assert "Titulo test" in out
    assert "Linea uno." in out
    assert "Linea dos." in out
    assert "linkedin" in out
