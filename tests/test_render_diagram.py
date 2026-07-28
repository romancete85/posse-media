"""Tests de las funciones puras del renderer (geometría del lienzo + parse de color)."""

import importlib.util
from pathlib import Path

_R = Path(__file__).resolve().parent.parent / "scripts" / "render-diagram.py"
_spec = importlib.util.spec_from_file_location("render_diagram", _R)
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)


def test_parse_rgb():
    assert rd._parse_rgb("rgb(238, 241, 244)") == (238, 241, 244)
    assert rd._parse_rgb("rgba(20, 30, 40, 1)") == (20, 30, 40)
    assert rd._parse_rgb("rgba(0, 0, 0, 0)") == rd._BG_FALLBACK  # transparente -> fallback
    assert rd._parse_rgb("") == rd._BG_FALLBACK
    assert rd._parse_rgb(None) == rd._BG_FALLBACK


def test_frame_size_agrega_barras_al_eje_corto():
    fw, fh = rd._frame_size(1000, 800, 0, (4, 5))   # ancho -> agrega alto
    assert (fw, fh) == (1000, 1250) and abs(fw / fh - 0.8) < 1e-9
    fw, fh = rd._frame_size(800, 2000, 0, (4, 5))    # alto -> agrega ancho
    assert (fw, fh) == (1600, 2000)


def test_frame_size_nunca_encoge():
    fw, fh = rd._frame_size(1000, 1000, 50, (1, 1))
    assert fw >= 1100 and fh >= 1100  # >= contenido + 2*pad


def test_frame_size_square():
    assert rd._frame_size(1200, 800, 0, (1, 1)) == (1200, 1200)


def test_ratio_from_args():
    assert rd._ratio_from_args("natural", None) is None
    assert rd._ratio_from_args("linkedin", None) == (4, 5)
    assert rd._ratio_from_args("square", None) == (1, 1)
    assert rd._ratio_from_args("loquesea", "4:5") == (4.0, 5.0)  # --ratio pisa --preset
