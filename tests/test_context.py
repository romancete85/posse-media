"""Tests del contexto de grounding."""

from posse import context
from posse.config import Settings
from posse.generators import draft as draft_mod
from posse.generators.draft import DraftOut


def test_load_concatena_y_topea(tmp_path):
    (tmp_path / "perfil.md").write_text("Soy ingeniero DevOps.", encoding="utf-8")
    (tmp_path / "proyectos.md").write_text("- repo-x — una app", encoding="utf-8")
    settings = Settings(_env_file=None, context_dir=str(tmp_path), context_max_chars=1000)
    ctx = context.load(settings)
    assert "Soy ingeniero DevOps." in ctx and "repo-x" in ctx
    assert "## perfil" in ctx  # encabezado por archivo


def test_load_vacio_si_no_hay_dir(tmp_path):
    settings = Settings(_env_file=None, context_dir=str(tmp_path / "nada"))
    assert context.load(settings) == ""


def test_render_proyectos_defensivo():
    repos = [
        {"name": "posse-media", "description": "", "primaryLanguage": {"name": "Python"},
         "repositoryTopics": None, "visibility": "PUBLIC"},
        {"name": "otro", "description": None, "primaryLanguage": None, "repositoryTopics": None},
    ]
    md = context.render_proyectos(repos)
    assert "**posse-media**" in md and "Python" in md
    assert "(sin descripción)" in md  # description None/"" -> placeholder


def test_draft_inyecta_contexto_en_system(monkeypatch, tmp_path):
    (tmp_path / "perfil.md").write_text("MARCA: Roman, Cloud Security.", encoding="utf-8")
    capturado = {}

    def fake_generate(prompt, schema, **kwargs):
        capturado["system"] = kwargs["system"]
        return DraftOut(titulo="T", cuerpo="c")

    monkeypatch.setattr("posse.generators.llm.generate_structured", fake_generate)
    settings = Settings(_env_file=None, context_dir=str(tmp_path), content_dir=str(tmp_path))
    draft_mod.draft("un tema", "A", usar_contexto=True, settings=settings)
    assert "CONTEXTO DEL AUTOR" in capturado["system"]
    assert "MARCA: Roman" in capturado["system"]


def test_draft_sin_contexto(monkeypatch, tmp_path):
    (tmp_path / "perfil.md").write_text("no debería aparecer", encoding="utf-8")
    capturado = {}

    def fake_generate(prompt, schema, **kwargs):
        capturado["system"] = kwargs["system"]
        return DraftOut(titulo="T", cuerpo="c")

    monkeypatch.setattr("posse.generators.llm.generate_structured", fake_generate)
    settings = Settings(_env_file=None, context_dir=str(tmp_path), content_dir=str(tmp_path))
    draft_mod.draft("un tema", "A", usar_contexto=False, settings=settings)
    assert "CONTEXTO DEL AUTOR" not in capturado["system"]
