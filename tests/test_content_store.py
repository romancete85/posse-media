"""Tests de content_store: load/validate + reescritura preservando comentarios."""

import pytest
from pydantic import ValidationError

from posse import content_store
from posse.models import Estado


def test_load_valido(pieza_path):
    p = content_store.load(pieza_path)
    assert p.id == "2026-07-21-test"
    assert p.estado is Estado.DRAFT
    assert p.destinos == ["linkedin"]
    assert p.cuerpo.strip().endswith("Linea dos.")


def test_validate_falla_con_destino_malo(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: x\npilar: A\ndestinos: [tiktok]\ntitulo: t\ncuerpo: c\n", encoding="utf-8"
    )
    with pytest.raises(ValidationError):
        content_store.validate(bad)


def test_marcar_publicado_actualiza_estado_y_datos(pieza_path):
    content_store.marcar_publicado(
        pieza_path, "linkedin", fecha="2026-07-21", url="https://lnkd.in/abc", post_id="urn:li:share:1"
    )
    p = content_store.load(pieza_path)
    assert p.estado is Estado.PUBLISHED
    assert p.esta_publicado_en("linkedin")
    d = p.publicado["linkedin"]
    assert (d.fecha, d.url, d.post_id) == ("2026-07-21", "https://lnkd.in/abc", "urn:li:share:1")


def test_marcar_publicado_preserva_comentario(pieza_path):
    content_store.marcar_publicado(
        pieza_path, "linkedin", fecha="2026-07-21", url="https://x", post_id="123"
    )
    texto = pieza_path.read_text(encoding="utf-8")
    assert "# comentario de cabecera" in texto
