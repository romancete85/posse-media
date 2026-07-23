"""Tests de generación (draft + repurpose). Claude mockeado — nunca la API real."""

from posse import content_store
from posse.config import Settings
from posse.generators import draft as draft_mod
from posse.generators import repurpose as rep
from posse.generators.draft import DraftOut
from posse.generators.repurpose import RepurposeOut
from posse.models import Estado, Pilar


def test_build_pieza_arma_draft():
    out = DraftOut(titulo="Mi Post de Prueba!", cuerpo="hola", hashtags=["devops"])
    p = draft_mod.build_pieza(out, "B", fecha="2026-07-23")
    assert p.id == "2026-07-23-mi-post-de-prueba"  # slug del titulo
    assert p.estado is Estado.DRAFT
    assert p.pilar is Pilar.B
    assert p.destinos == ["linkedin"]
    assert p.hashtags == ["devops"]
    assert "linkedin" in p.publicado and not p.esta_publicado_en("linkedin")


def test_draft_usa_llm_mockeado(monkeypatch, tmp_path):
    def fake_generate(prompt, schema, **kwargs):
        assert schema is DraftOut
        return DraftOut(titulo="Título X", cuerpo="cuerpo del post", hashtags=["cloud"])

    monkeypatch.setattr("posse.generators.llm.generate_structured", fake_generate)
    settings = Settings(_env_file=None, content_dir=str(tmp_path))
    path = draft_mod.draft_to_file("un tema", "A", settings=settings)

    assert path.exists()
    p = content_store.load(path)
    assert p.estado is Estado.DRAFT
    assert p.titulo == "Título X"
    assert p.cuerpo.strip() == "cuerpo del post"


def test_repurpose_genera_n_piezas(monkeypatch, tmp_path):
    def fake_generate(prompt, schema, **kwargs):
        assert schema is RepurposeOut
        return RepurposeOut(
            piezas=[
                DraftOut(titulo="Idea uno", cuerpo="a", hashtags=[]),
                DraftOut(titulo="Idea dos", cuerpo="b", hashtags=[]),
            ]
        )

    monkeypatch.setattr("posse.generators.llm.generate_structured", fake_generate)
    settings = Settings(_env_file=None, content_dir=str(tmp_path))
    paths = rep.repurpose_to_files("fuente larga...", "C", 2, settings=settings)

    assert len(paths) == 2
    ids = {content_store.load(p).id for p in paths}
    assert ids == {"2026-07-23-idea-uno", "2026-07-23-idea-dos"} or len(ids) == 2


def test_save_new_no_pisa_ids_duplicados(tmp_path):
    out = DraftOut(titulo="Repetido", cuerpo="x")
    p = draft_mod.build_pieza(out, "A", fecha="2026-07-23")
    a = content_store.save_new(p, tmp_path)
    b = content_store.save_new(p, tmp_path)
    assert a != b  # el segundo agrega sufijo -2
    assert a.name == "2026-07-23-repetido.yaml"
    assert b.name == "2026-07-23-repetido-2.yaml"
