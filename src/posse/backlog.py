"""Backlog: vista de todas las piezas de content/ por estado."""

from __future__ import annotations

from pathlib import Path

from posse import content_store
from posse.models import Estado

_ORDER = {Estado.APPROVED: 0, Estado.DRAFT: 1, Estado.PUBLISHED: 2}
_MARK = {"approved": "●", "draft": "○", "published": "✓", "INVÁLIDA": "✗"}


def collect(content_dir: str | Path) -> list[dict]:
    """Devuelve una fila por pieza (o error) en content_dir."""
    rows: list[dict] = []
    for p in sorted(Path(content_dir).glob("*.yaml")):
        try:
            pieza = content_store.load(p)
            rows.append(
                {"ok": True, "path": p, "id": pieza.id, "estado": pieza.estado,
                 "pilar": pieza.pilar.value, "titulo": pieza.titulo}
            )
        except Exception as ex:  # noqa: BLE001 — archivo inválido no debe romper el listado
            rows.append({"ok": False, "path": p, "id": p.stem, "estado": None, "error": str(ex)})
    return rows


def render(content_dir: str | Path) -> str:
    """Texto del backlog, ordenado approved → draft → published (inválidas al final)."""
    rows = collect(content_dir)
    rows.sort(key=lambda r: (_ORDER.get(r["estado"], 9) if r["ok"] else 8, r["id"]))

    counts: dict[str, int] = {}
    lines: list[str] = []
    for r in rows:
        est = r["estado"].value if r["ok"] and r["estado"] else "INVÁLIDA"
        counts[est] = counts.get(est, 0) + 1
        titulo = (r.get("titulo") or r.get("error", ""))[:55]
        lines.append(f"{_MARK.get(est, '?')} {est:<9} {r['id']:<45} {titulo}")

    resumen = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items())) or "(sin piezas)"
    return "\n".join([f"── backlog ({resumen}) ──", *lines])
