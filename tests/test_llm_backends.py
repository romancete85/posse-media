"""Tests del backend de texto pluggable (ollama / claude). Servicios mockeados."""

import json

import httpx
import pytest

from posse.config import Settings
from posse.generators import llm
from posse.generators.draft import DraftOut


def test_backend_ollama_structured():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"message": {"content": DraftOut(titulo="T", cuerpo="c").model_dump_json()}}
        )

    settings = Settings(
        _env_file=None,
        llm_backend="ollama",
        ollama_model="llama3.1",
        ollama_host="http://mini:11434",
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    out = llm.generate_structured("prompt", DraftOut, settings=settings, client=client)

    assert out.titulo == "T"
    assert seen["url"] == "http://mini:11434/api/chat"
    assert seen["body"]["model"] == "llama3.1"
    assert seen["body"]["stream"] is False
    assert "format" in seen["body"]  # JSON schema para structured output


def test_backend_claude_structured():
    class _Parsed:
        parsed_output = DraftOut(titulo="C", cuerpo="x")

    class _Messages:
        def parse(self, **kwargs):
            assert kwargs["model"] == "claude-opus-4-8"
            return _Parsed()

    class _FakeClient:
        messages = _Messages()

    settings = Settings(_env_file=None, llm_backend="claude", claude_model="claude-opus-4-8")
    out = llm.generate_structured("p", DraftOut, settings=settings, client=_FakeClient())
    assert out.titulo == "C"


def test_backend_desconocido_falla():
    settings = Settings(_env_file=None, llm_backend="foo")
    with pytest.raises(ValueError):
        llm.generate_structured("p", DraftOut, settings=settings)
