"""Tests de generación de imágenes. Imagen y Claude mockeados — nunca APIs reales."""

from posse import content_store
from posse.config import Settings
from posse.generators import images
from posse.generators.draft import DraftOut, build_pieza


def _pieza_draft(tmp_path):
    p = build_pieza(DraftOut(titulo="Post con foto", cuerpo="cuerpo"), "A", fecha="2026-07-23")
    return content_store.save_new(p, tmp_path)


def test_gen_image_agrega_asset_con_alt(tmp_path):
    pieza_path = _pieza_draft(tmp_path)
    seen = {}

    def fake_generate(prompt, settings):
        seen["prompt"] = prompt
        return b"\x89PNGfake", "image/png"

    def fake_alt(image_bytes, mime, **kwargs):
        assert image_bytes == b"\x89PNGfake"
        return "una imagen de prueba"

    settings = Settings(_env_file=None, content_dir=str(tmp_path))
    img_path = images.gen_image(
        pieza_path, settings=settings, generate_fn=fake_generate, alt_fn=fake_alt
    )

    # la imagen se escribió bajo content/assets/
    assert img_path.exists()
    assert img_path.parent.name == "assets"
    assert img_path.read_bytes() == b"\x89PNGfake"
    # el prompt derivó del título/cuerpo
    assert "Post con foto" in seen["prompt"]

    # la pieza ahora tiene el asset con path + alt (y valida el schema)
    p = content_store.load(pieza_path)
    assert len(p.assets) == 1
    assert p.assets[0].path == str(img_path)
    assert p.assets[0].alt == "una imagen de prueba"


def test_gen_image_prompt_explicito(tmp_path):
    pieza_path = _pieza_draft(tmp_path)
    seen = {}

    def fake_generate(prompt, settings):
        seen["prompt"] = prompt
        return b"JPG", "image/jpeg"

    settings = Settings(_env_file=None, content_dir=str(tmp_path))
    img_path = images.gen_image(
        pieza_path,
        prompt="un gato astronauta",
        settings=settings,
        generate_fn=fake_generate,
        alt_fn=lambda *a, **k: "alt",
    )
    assert seen["prompt"] == "un gato astronauta"
    assert img_path.suffix == ".jpg"  # mime image/jpeg -> jpg


def test_add_asset_directo(tmp_path):
    pieza_path = _pieza_draft(tmp_path)
    content_store.add_asset(pieza_path, "content/assets/x.png", "alt x")
    p = content_store.load(pieza_path)
    assert p.assets[0].path == "content/assets/x.png"
    assert p.assets[0].alt == "alt x"
