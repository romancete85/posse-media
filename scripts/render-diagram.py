#!/usr/bin/env python3
"""render-diagram — convierte un HTML de diagrama en PNG de alta resolución (Playwright/Chromium).

Acepta tanto un HTML standalone como el "fragmento" de un artifact (sin <html>/<head>/<body>):
en ese caso lo envuelve y fuerza tema claro. Oculta el panel interactivo y el footer para la captura.

Uso:
    python scripts/render-diagram.py <input.html> <output.png> [--selector .wrap] [--width 1200] [--scale 2]

Requiere: pip install ".[render]"  +  python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import pathlib

from playwright.sync_api import sync_playwright

# Oculta el panel de detalle interactivo y el footer para una captura limpia.
CAPTURE_CSS = "<style>.detail,.foot{display:none!important}</style>"


def _prepare(html: str) -> str:
    if "<html" in html.lower():
        return html.replace("</head>", CAPTURE_CSS + "</head>", 1)
    return (
        '<!doctype html><html data-theme="light"><head><meta charset="utf-8">'
        "<style>*{box-sizing:border-box}body{margin:0}</style>" + CAPTURE_CSS +
        "</head><body>" + html + "</body></html>"
    )


def render(input_html: str, output_png: str, selector: str = ".wrap", width: int = 1200, scale: int = 2) -> None:
    html = _prepare(pathlib.Path(input_html).read_text(encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=scale)
        page.set_content(html, wait_until="networkidle")
        el = page.query_selector(selector) or page.query_selector("body")
        el.screenshot(path=output_png)
        browser.close()
    print(f"OK -> {output_png}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Render de un HTML de diagrama a PNG.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--selector", default=".wrap", help="elemento a capturar (default .wrap; .canvas = solo el diagrama)")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--scale", type=int, default=2, help="factor de resolución (2 = Retina)")
    a = ap.parse_args()
    render(a.input, a.output, a.selector, a.width, a.scale)


if __name__ == "__main__":
    main()
