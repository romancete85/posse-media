"""Cliente Claude (SDK anthropic) — helpers compartidos de generación.

- generate_structured: prompt -> objeto pydantic validado (structured outputs).
- alt_text: imagen -> texto alternativo (Claude visión), para accesibilidad.

Modelo por defecto: claude-opus-4-8. La API key sale de settings.anthropic_api_key
(o del entorno si está vacía). Los tests inyectan un `client` fake (nunca la API real).
"""

from __future__ import annotations

import base64
import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from posse.config import Settings, get_settings

log = logging.getLogger("posse.llm")

T = TypeVar("T", bound=BaseModel)


def _client(settings: Settings) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key or None)


def generate_structured(
    prompt: str,
    schema: type[T],
    *,
    system: str | None = None,
    max_tokens: int = 4096,
    settings: Settings | None = None,
    client: anthropic.Anthropic | None = None,
) -> T:
    """Genera una respuesta validada contra `schema` (structured outputs)."""
    settings = settings or get_settings()
    c = client or _client(settings)
    resp = c.messages.parse(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    log.info("generación estructurada OK (%s)", schema.__name__)
    return resp.parsed_output


def alt_text(
    image_bytes: bytes,
    media_type: str,
    *,
    settings: Settings | None = None,
    client: anthropic.Anthropic | None = None,
) -> str:
    """Devuelve un alt text conciso de la imagen (Claude visión)."""
    settings = settings or get_settings()
    c = client or _client(settings)
    data = base64.standard_b64encode(image_bytes).decode("utf-8")
    resp = c.messages.create(
        model=settings.claude_model,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                    {
                        "type": "text",
                        "text": (
                            "Escribí un alt text conciso (una frase, español rioplatense) que describa "
                            "esta imagen para accesibilidad. Devolvé solo el texto, sin comillas."
                        ),
                    },
                ],
            }
        ],
    )
    return next((b.text for b in resp.content if b.type == "text"), "").strip()
