"""Generación de texto estructurado — backend pluggable.

- "ollama" (default): homelab, gratis. Structured outputs vía el parámetro `format`
  (JSON schema) de /api/chat. Requiere Ollama accesible por HTTP (OLLAMA_HOST).
- "claude": API de Claude (con créditos). messages.parse con output_format.

Los tests inyectan `client` (httpx MockTransport para ollama; cliente fake para claude);
nunca se pega a un servicio real.
"""

from __future__ import annotations

import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel

from posse.config import Settings, get_settings

log = logging.getLogger("posse.llm")

T = TypeVar("T", bound=BaseModel)


def generate_structured(
    prompt: str,
    schema: type[T],
    *,
    system: str | None = None,
    max_tokens: int = 4096,
    settings: Settings | None = None,
    client=None,
) -> T:
    """Genera una respuesta validada contra `schema` usando el backend configurado."""
    settings = settings or get_settings()
    if settings.llm_backend == "ollama":
        return _ollama_structured(prompt, schema, system=system, settings=settings, client=client)
    if settings.llm_backend == "claude":
        return _claude_structured(
            prompt, schema, system=system, max_tokens=max_tokens, settings=settings, client=client
        )
    raise ValueError(f"LLM_BACKEND desconocido: {settings.llm_backend!r} (usar 'ollama' o 'claude')")


def _ollama_structured(
    prompt: str, schema: type[T], *, system: str | None, settings: Settings, client=None
) -> T:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "format": schema.model_json_schema(),  # structured outputs de Ollama
        "stream": False,
    }
    c = client or httpx.Client(timeout=httpx.Timeout(300.0))  # CPU: qwen2.5:7b puede tardar minutos
    resp = c.post(f"{settings.ollama_host.rstrip('/')}/api/chat", json=payload)
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    log.info("generación ollama OK (%s, %s)", settings.ollama_model, schema.__name__)
    return schema.model_validate_json(content)


def _claude_structured(
    prompt: str, schema: type[T], *, system: str | None, max_tokens: int, settings: Settings, client=None
) -> T:
    import anthropic

    c = client or anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    resp = c.messages.parse(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    log.info("generación claude OK (%s, %s)", settings.claude_model, schema.__name__)
    return resp.parsed_output
