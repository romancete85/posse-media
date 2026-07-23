"""Tests del schema de la pieza (models.Pieza)."""

import pytest
from pydantic import ValidationError

from posse.models import Estado, Pieza, Pilar

BASE = {
    "id": "2026-07-21-test",
    "pilar": "A",
    "estado": "draft",
    "destinos": ["linkedin"],
    "titulo": "Titulo test",
    "cuerpo": "Cuerpo test",
    "publicado": {"linkedin": {"fecha": None, "url": None, "post_id": None}},
}


def test_schema_valido():
    p = Pieza.model_validate(BASE)
    assert p.estado is Estado.DRAFT
    assert p.pilar is Pilar.A
    assert p.assets == [] and p.hashtags == []
    assert not p.esta_publicado_en("linkedin")


def test_destino_desconocido_falla():
    with pytest.raises(ValidationError):
        Pieza.model_validate({**BASE, "destinos": ["tiktok"]})


def test_destinos_vacio_falla():
    with pytest.raises(ValidationError):
        Pieza.model_validate({**BASE, "destinos": []})


def test_campo_vacio_falla():
    with pytest.raises(ValidationError):
        Pieza.model_validate({**BASE, "titulo": "   "})


def test_campo_extra_falla():
    with pytest.raises(ValidationError):
        Pieza.model_validate({**BASE, "desconocido": 1})


def test_assets_como_objetos():
    p = Pieza.model_validate({**BASE, "assets": [{"path": "content/assets/x.png", "alt": "foto"}]})
    assert p.assets[0].path == "content/assets/x.png"
    assert p.assets[0].alt == "foto"


def test_asset_sin_path_falla():
    with pytest.raises(ValidationError):
        Pieza.model_validate({**BASE, "assets": [{"alt": "sin path"}]})


def test_esta_publicado_en_con_post_id():
    p = Pieza.model_validate(
        {**BASE, "estado": "published", "publicado": {"linkedin": {"post_id": "urn:123"}}}
    )
    assert p.esta_publicado_en("linkedin")
    assert not p.esta_publicado_en("x")
