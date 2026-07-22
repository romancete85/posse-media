"""Fixtures compartidos de la suite."""

import pytest

# Pieza de ejemplo con un comentario de cabecera y publicado en flow-style,
# para verificar que la reescritura preserva formato.
PIEZA_YAML = """\
# comentario de cabecera (debe sobrevivir a la reescritura)
id: 2026-07-21-test
pilar: A
estado: draft
destinos: [linkedin]
titulo: Titulo test
cuerpo: |
  Linea uno.
  Linea dos.
assets: []
hashtags: [devops]
publicado:
  linkedin: { fecha: null, url: null, post_id: null }
"""


@pytest.fixture
def pieza_path(tmp_path):
    """Devuelve la ruta a una pieza YAML temporal en estado draft."""
    p = tmp_path / "pieza.yaml"
    p.write_text(PIEZA_YAML, encoding="utf-8")
    return p
