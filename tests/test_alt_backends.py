"""Tests del backend de alt text (dispatcher gemini/ollama). Visión local mockeada."""

import base64
import json

import httpx

from posse.config import Settings
from posse.generators import images


def test_ollama_alt_manda_imagen_base64():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": "una imagen de prueba"}})

    settings = Settings(
        _env_file=None, alt_backend="ollama", ollama_vision_model="llava:7b",
        ollama_host="http://mini:11434", ollama_keep_alive="30m",
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    alt = images._ollama_alt(b"\x89PNGfake", "image/png", settings=settings, client=client)

    assert alt == "una imagen de prueba"
    assert seen["url"] == "http://mini:11434/api/chat"
    assert seen["body"]["model"] == "llava:7b"
    assert seen["body"]["keep_alive"] == "30m"
    # la imagen va en images[] como base64 (sin prefijo data:)
    assert seen["body"]["messages"][0]["images"] == [base64.standard_b64encode(b"\x89PNGfake").decode()]


def test_dispatcher_elige_backend():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["hit"] = "ollama"
        return httpx.Response(200, json={"message": {"content": "alt local"}})

    settings = Settings(_env_file=None, alt_backend="ollama", ollama_host="http://mini:11434")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    alt = images._alt(b"x", "image/png", settings=settings, client=client)
    assert alt == "alt local" and seen["hit"] == "ollama"
