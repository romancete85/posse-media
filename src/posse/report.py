"""Reporte de rendimiento: qué piezas/pilares rinden, a partir de las métricas cargadas a mano.

Las métricas se registran con `posse metrics` (la API de analytics de LinkedIn es partner-gated
para perfiles personales — ver docs/AUTO-PUBLISH.md). Este reporte solo lee lo que cargaste.
"""

from __future__ import annotations

from pathlib import Path

from posse import content_store
from posse.models import Metrica, Pieza


def _filas(content_dir: str | Path, plataforma: str) -> list[tuple[Pieza, Metrica]]:
    """(pieza, metrica) por cada pieza con métricas en `plataforma`."""
    out: list[tuple[Pieza, Metrica]] = []
    for p in sorted(Path(content_dir).glob("*.yaml")):
        try:
            pieza = content_store.load(p)
        except Exception:  # noqa: BLE001 — archivo inválido no rompe el reporte
            continue
        m = pieza.metricas.get(plataforma)
        if m is not None:
            out.append((pieza, m))
    return out


def _fmt(v: int | None) -> str:
    return "—" if v is None else str(v)


def render(content_dir: str | Path, plataforma: str = "linkedin") -> str:
    """Tabla de métricas ordenada por impresiones desc + resumen por pilar."""
    filas = _filas(content_dir, plataforma)
    if not filas:
        return (
            f"── reporte {plataforma}: sin métricas cargadas ──\n"
            "Cargá con: posse metrics <pieza> --impresiones N --reacciones N --comentarios N"
        )

    filas.sort(key=lambda fm: (fm[1].impresiones or -1), reverse=True)

    hdr = f"{'id':<40} {'pilar':<5} {'impr':>7} {'reacc':>6} {'coment':>6} {'clics':>6} {'ER%':>6}"
    lines = [f"── reporte {plataforma} ({len(filas)} pieza(s) con métricas) ──", hdr, "─" * len(hdr)]

    # Acumuladores por pilar para el resumen.
    por_pilar: dict[str, list[float]] = {}
    for pieza, m in filas:
        er = m.engagement_rate
        er_str = f"{er * 100:.1f}" if er is not None else "—"
        lines.append(
            f"{pieza.id:<40} {pieza.pilar.value:<5} {_fmt(m.impresiones):>7} "
            f"{_fmt(m.reacciones):>6} {_fmt(m.comentarios):>6} {_fmt(m.clics):>6} {er_str:>6}"
        )
        if er is not None:
            por_pilar.setdefault(pieza.pilar.value, []).append(er)

    if por_pilar:
        lines.append("")
        lines.append("Engagement rate promedio por pilar:")
        for pilar, ers in sorted(por_pilar.items(), key=lambda kv: sum(kv[1]) / len(kv[1]), reverse=True):
            prom = sum(ers) / len(ers)
            lines.append(f"  pilar {pilar}: {prom * 100:.1f}%  ({len(ers)} pieza(s))")
        lines.append("→ Doblá la apuesta en el pilar/tema que más rinde.")

    return "\n".join(lines)
