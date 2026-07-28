#!/usr/bin/env python3
"""render-diagram — convierte un HTML de diagrama en PNG de alta resolución (Playwright/Chromium).

Acepta un HTML standalone o el "fragmento" de un artifact (sin <html>/<head>/<body>): lo envuelve
y fuerza tema claro. Oculta el panel interactivo y el footer para la captura.

Para el feed de LinkedIn conviene un ratio vertical/cuadrado (ocupa más pantalla en mobile = más
atención) sin achicar el diagrama: se renderiza a tamaño natural y se compone sobre un lienzo del
ratio target (mismo color de fondo, diagrama centrado). Nunca encoge el diagrama, solo agrega barras.

Uso:
    python scripts/render-diagram.py <in.html> <out.png> [--preset linkedin] [--ratio 4:5] [--pad 48]
    presets: natural (default, sin lienzo) · linkedin/portrait (4:5) · square (1:1) · wide (1.91:1)

Requiere: pip install ".[render]"  +  python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import pathlib
import re

from playwright.sync_api import sync_playwright

# Oculta el panel de detalle interactivo y el footer para una captura limpia.
CAPTURE_CSS = "<style>.detail,.foot{display:none!important}</style>"

# Ratios (ancho:alto). natural = sin lienzo (captura directa del elemento).
PRESETS: dict[str, tuple[float, float] | None] = {
    "natural": None,
    "linkedin": (4, 5),   # portrait 4:5 — el que más rinde en el feed
    "portrait": (4, 5),
    "square": (1, 1),
    "wide": (191, 100),   # 1.91:1
}

_BG_FALLBACK = (238, 241, 244)  # #eef1f4, el --ground claro de los diagramas


def _prepare(html: str) -> str:
    if "<html" in html.lower():
        return html.replace("</head>", CAPTURE_CSS + "</head>", 1)
    return (
        '<!doctype html><html data-theme="light"><head><meta charset="utf-8">'
        "<style>*{box-sizing:border-box}body{margin:0}</style>" + CAPTURE_CSS +
        "</head><body>" + html + "</body></html>"
    )


def _parse_rgb(css: str | None, fallback: tuple[int, int, int] = _BG_FALLBACK) -> tuple[int, int, int]:
    """'rgb(238, 241, 244)' / 'rgba(...)' -> (r,g,b). Transparente o inválido -> fallback."""
    nums = re.findall(r"[\d.]+", css or "")
    if len(nums) < 3:
        return fallback
    if len(nums) >= 4 and float(nums[3]) == 0:  # alpha 0 = transparente
        return fallback
    return tuple(int(float(nums[i])) for i in range(3))  # type: ignore[return-value]


def _frame_size(w: int, h: int, pad: int, ratio: tuple[float, float]) -> tuple[int, int]:
    """Lienzo mínimo que contiene (w+2pad, h+2pad) y cumple el ratio. Solo agrega barras."""
    cw, ch = w + 2 * pad, h + 2 * pad
    target = ratio[0] / ratio[1]
    if cw / ch >= target:
        return cw, round(cw / target)   # muy ancho -> agrega alto
    return round(ch * target), ch        # muy alto -> agrega ancho


def _compose(png_bytes: bytes, output_png: str, *, ratio: tuple[float, float], pad: int, bg: tuple[int, int, int]) -> None:
    from io import BytesIO

    from PIL import Image

    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    w, h = img.size
    fw, fh = _frame_size(w, h, pad, ratio)
    canvas = Image.new("RGB", (fw, fh), bg)
    canvas.paste(img, ((fw - w) // 2, (fh - h) // 2))
    canvas.save(output_png)


def render(
    input_html: str,
    output_png: str,
    selector: str = ".wrap",
    width: int = 1200,
    scale: int = 2,
    ratio: tuple[float, float] | None = None,
    pad: int = 48,
) -> None:
    html = _prepare(pathlib.Path(input_html).read_text(encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=scale)
        page.set_content(html, wait_until="networkidle")
        el = page.query_selector(selector) or page.query_selector("body")
        if ratio is None:
            el.screenshot(path=output_png)   # captura directa (tamaño natural)
            browser.close()
            print(f"OK -> {output_png}")
            return
        png = el.screenshot()  # bytes, ya a *scale
        page_bg = _parse_rgb(page.evaluate("() => getComputedStyle(document.body).backgroundColor"))
        browser.close()
    _compose(png, output_png, ratio=ratio, pad=pad * scale, bg=page_bg)
    print(f"OK -> {output_png}  ({ratio[0]:g}:{ratio[1]:g}, fondo rgb{page_bg})")


def _ratio_from_args(preset: str, ratio: str | None) -> tuple[float, float] | None:
    if ratio:
        a, b = ratio.split(":")
        return (float(a), float(b))
    if preset not in PRESETS:
        raise SystemExit(f"preset desconocido: {preset} (opciones: {', '.join(PRESETS)})")
    return PRESETS[preset]


def main() -> None:
    ap = argparse.ArgumentParser(description="Render de un HTML de diagrama a PNG (con ratio para LinkedIn).")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--selector", default=".wrap", help="elemento a capturar (default .wrap)")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--scale", type=int, default=2, help="factor de resolución (2 = Retina)")
    ap.add_argument("--preset", default="natural", help=f"ratio del lienzo: {', '.join(PRESETS)}")
    ap.add_argument("--ratio", default=None, help="ratio custom ancho:alto (ej. 4:5), pisa --preset")
    ap.add_argument("--pad", type=int, default=48, help="padding mínimo alrededor del diagrama (px lógicos)")
    a = ap.parse_args()
    render(a.input, a.output, a.selector, a.width, a.scale, _ratio_from_args(a.preset, a.ratio), a.pad)


if __name__ == "__main__":
    main()
