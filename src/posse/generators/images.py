"""Genera una imagen con Google Imagen y la agrega a una pieza (con alt text de Claude).

Upstream del gate: solo agrega un asset a una pieza draft; no aprueba ni publica.
El proveedor (Google Imagen) es una dependencia externa (cuenta Google AI + GEMINI_API_KEY);
la llamada está aislada en `_default_generate` para que los tests la mockeen (nunca la API real).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from posse import content_store
from posse.config import Settings, get_settings

log = logging.getLogger("posse.images")

_ALT_PROMPT = (
    "Escribí un alt text conciso (una frase, español rioplatense) que describa esta imagen "
    "para accesibilidad. Devolvé solo el texto, sin comillas."
)

# Firma del generador de imágenes: (prompt, settings) -> (bytes, mime_type)
GenerateFn = Callable[[str, Settings], tuple[bytes, str]]


def _default_generate(prompt: str, settings: Settings) -> tuple[bytes, str]:
    """Genera una imagen con Google Imagen (SDK google-genai). Import lazy."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key or None)
    resp = client.models.generate_images(
        model=settings.imagen_model,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1),
    )
    img = resp.generated_images[0].image
    return img.image_bytes, getattr(img, "mime_type", None) or "image/png"


def _default_alt(image_bytes: bytes, mime: str, *, settings: Settings) -> str:
    """Alt text de la imagen con Gemini visión (misma key que Imagen). Import lazy."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key or None)
    resp = client.models.generate_content(
        model=settings.gemini_vision_model,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), _ALT_PROMPT],
    )
    return (resp.text or "").strip()


def _prompt_from_pieza(pieza) -> str:
    return (
        f"Imagen para un post de LinkedIn sobre: {pieza.titulo}. "
        f"{pieza.cuerpo.strip()[:200]} Estilo profesional, limpio, sin texto."
    )


def _ext_for(mime: str) -> str:
    return "png" if "png" in mime else "jpg" if "jpeg" in mime or "jpg" in mime else "img"


def gen_image(
    pieza_path: str | Path,
    *,
    prompt: str | None = None,
    settings: Settings | None = None,
    generate_fn: GenerateFn | None = None,
    alt_fn=None,
) -> Path:
    """Genera una imagen para la pieza, la guarda en content/assets/ y la agrega a `assets`.

    Devuelve la ruta de la imagen. Escribe el alt text (Claude visión) para accesibilidad.
    """
    settings = settings or get_settings()
    pieza = content_store.load(pieza_path)
    prompt = prompt or _prompt_from_pieza(pieza)

    generate_fn = generate_fn or _default_generate
    image_bytes, mime = generate_fn(prompt, settings)

    assets_dir = Path(settings.content_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img_path = assets_dir / f"{pieza.id}.{_ext_for(mime)}"
    i = 2
    while img_path.exists():
        img_path = assets_dir / f"{pieza.id}-{i}.{_ext_for(mime)}"
        i += 1
    img_path.write_bytes(image_bytes)
    log.info("imagen generada: %s", img_path)

    alt_fn = alt_fn or _default_alt
    alt = alt_fn(image_bytes, mime, settings=settings)

    content_store.add_asset(pieza_path, str(img_path), alt)
    return img_path
