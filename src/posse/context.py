"""Contexto de grounding para la generación (perfil + proyectos + otras fuentes).

Lee `context/*.md` y lo inyecta como contexto del sistema para que los posts suenen
al autor y citen sus proyectos reales. `context github` arma proyectos.md desde GitHub.

⚠️ Por default toma solo repos PÚBLICOS: los privados suelen ser trabajo de clientes
(confidencial) y no deben alimentar contenido público.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from posse.config import Settings, get_settings


def load(settings: Settings | None = None) -> str:
    """Concatena todos los context/*.md (con tope de tamaño)."""
    settings = settings or get_settings()
    d = Path(settings.context_dir)
    if not d.exists():
        return ""
    partes = []
    for p in sorted(d.glob("*.md")):
        t = p.read_text(encoding="utf-8").strip()
        if t:
            partes.append(f"## {p.stem}\n{t}")
    return "\n\n".join(partes)[: settings.context_max_chars]


def con_contexto(system_base: str, settings: Settings | None = None) -> str:
    """Agrega el contexto del autor al system prompt (si hay)."""
    ctx = load(settings)
    if not ctx:
        return system_base
    return (
        system_base
        + "\n\nCONTEXTO DEL AUTOR (para que el post suene a él y, si corresponde, mencione sus "
        "proyectos reales; NO lo copies literal, es referencia):\n"
        + ctx
    )


# --- GitHub -------------------------------------------------------------------------------------


def current_user() -> str:
    """Login de GitHub autenticado en `gh`."""
    out = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def github_repos(user: str, visibility: str = "public") -> list[dict]:
    """Lista repos del usuario vía gh (default solo públicos)."""
    cmd = [
        "gh", "repo", "list", user, "--limit", "100",
        "--json", "name,description,primaryLanguage,repositoryTopics,visibility,updatedAt",
    ]
    if visibility in ("public", "private"):
        cmd += ["--visibility", visibility]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def render_proyectos(repos: list[dict]) -> str:
    """Markdown de proyectos para el contexto (defensivo con campos nulos)."""
    lines = ["# Proyectos GitHub", ""]
    for r in repos:
        lang = (r.get("primaryLanguage") or {}).get("name")
        topics = ", ".join(t.get("name", "") for t in (r.get("repositoryTopics") or []))
        desc = r.get("description") or "(sin descripción)"
        meta = " · ".join(x for x in [lang, topics, r.get("visibility")] if x)
        entry = f"- **{r['name']}** — {desc}"
        if meta:
            entry += f"\n  ({meta})"
        lines.append(entry)
    return "\n".join(lines) + "\n"


def build_github(user: str | None = None, visibility: str = "public", settings: Settings | None = None) -> Path:
    """Escribe context/proyectos.md desde GitHub. Devuelve la ruta."""
    settings = settings or get_settings()
    user = user or current_user()
    d = Path(settings.context_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "proyectos.md"
    path.write_text(render_proyectos(github_repos(user, visibility)), encoding="utf-8")
    return path
