"""Tests del modelo para cross-post: destinos nuevos, variantes y programado."""

import datetime as dt

import pytest
from pydantic import ValidationError

from posse.models import Pieza


def _pieza(**over):
    base = {
        "id": "2026-07-25-x", "pilar": "A", "estado": "draft",
        "destinos": ["linkedin"], "titulo": "t", "cuerpo": "cuerpo principal",
        "hashtags": ["a", "b"],
    }
    base.update(over)
    return Pieza.model_validate(base)


def test_destinos_nuevos_validos():
    p = _pieza(destinos=["linkedin", "mastodon", "twitter"])
    assert p.destinos == ["linkedin", "mastodon", "twitter"]


def test_destino_desconocido_falla():
    with pytest.raises(ValidationError):
        _pieza(destinos=["facebook"])


def test_contenido_para_usa_principal_sin_variante():
    p = _pieza()
    cuerpo, tags = p.contenido_para("mastodon")
    assert cuerpo == "cuerpo principal"
    assert tags == ["a", "b"]


def test_contenido_para_usa_variante():
    p = _pieza(variantes={"twitter": {"cuerpo": "corto", "hashtags": ["x"]}})
    assert p.contenido_para("twitter") == ("corto", ["x"])
    # otro destino sin variante -> principal
    assert p.contenido_para("mastodon") == ("cuerpo principal", ["a", "b"])


def test_variante_solo_cuerpo_hereda_hashtags():
    p = _pieza(variantes={"mastodon": {"cuerpo": "corto"}})
    assert p.contenido_para("mastodon") == ("corto", ["a", "b"])


def test_variante_destino_desconocido_falla():
    with pytest.raises(ValidationError):
        _pieza(variantes={"tiktok": {"cuerpo": "x"}})


def test_programado_valida_fecha():
    assert _pieza(programado="2026-07-28").programado == "2026-07-28"
    with pytest.raises(ValidationError):
        _pieza(programado="28/07/2026")


def test_esta_programada_para():
    p = _pieza(programado="2026-07-28")
    assert p.esta_programada_para(dt.date(2026, 7, 28)) is True
    assert p.esta_programada_para(dt.date(2026, 7, 29)) is True
    assert p.esta_programada_para(dt.date(2026, 7, 27)) is False
    assert _pieza().esta_programada_para(dt.date(2026, 7, 28)) is False  # sin programado
