#!/usr/bin/env python3
"""build-handdrawn — arma un diagrama "hand-drawn" (estilo Excalidraw) autocontenido.

Inline-a los assets vendoreados (rough.js + fuente Virgil en base64) + el motor
(engine.js) + una escena data-driven en UN HTML. Ese HTML sirve doble:
  · artifact interactivo en claude.ai (CSP estricto → por eso TODO va inline)
  · fuente para render a PNG con scripts/render-diagram.py

Uso:
    python scripts/build-handdrawn.py <scene.js> <out.html> [--title "…"]
    # p.ej.
    python scripts/build-handdrawn.py scripts/handdrawn/ia-local.scene.js \
        content/assets/diagrama-ia-local-hd.html --title "IA local — hand-drawn"

Luego:
    python scripts/render-diagram.py content/assets/diagrama-ia-local-hd.html \
        content/assets/diagrama-ia-local-hd.png --preset natural --width 940
"""

from __future__ import annotations

import argparse
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENDOR = ROOT / "content" / "assets" / "vendor"
ENGINE = ROOT / "scripts" / "handdrawn" / "engine.js"


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def _font_data_uri() -> str:
    b64 = base64.b64encode((VENDOR / "Virgil.woff2").read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{b64}"


TEMPLATE = """<title>{title}</title>
<style>
  @font-face {{
    font-family: "Virgil";
    src: url("{font}") format("woff2");
    font-weight: normal; font-style: normal; font-display: block;
  }}
  :root {{ --ground: #ffffff; --ink: #1e1e1e; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --ground: #ffffff; }} }} /* diagrama siempre en claro */
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--ground); color: var(--ink);
    font-family: "Virgil", "Segoe Print", "Comic Sans MS", cursive; -webkit-font-smoothing: antialiased; }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 22px 20px 26px; background: var(--ground); }}
  svg {{ display: block; width: 100%; height: auto; }}
  text {{ font-family: "Virgil", "Segoe Print", "Comic Sans MS", cursive; }}
</style>

<div class="wrap">
  <svg id="cv" xmlns="http://www.w3.org/2000/svg"></svg>
</div>

<script>{roughjs}</script>
<script>{engine}</script>
<script>
  // Dibuja apenas la fuente Virgil está lista, para que el texto tome bien las métricas.
  // Fallback: si fonts.ready tarda, dibuja igual (el navegador re-renderiza al cargar la fuente).
  (function () {{
    function draw() {{ {scene} }}
    if (document.fonts && document.fonts.load) {{
      document.fonts.load('20px "Virgil"').then(draw).catch(draw);
      // red de seguridad para el screenshot headless:
      setTimeout(function () {{ if (!document.querySelector('#cv g')) draw(); }}, 400);
    }} else {{ draw(); }}
  }})();
</script>
"""


def build(scene_path: str, out_path: str, title: str) -> None:
    scene = _read(pathlib.Path(scene_path))
    html = TEMPLATE.format(
        title=title,
        font=_font_data_uri(),
        roughjs=_read(VENDOR / "rough.min.js"),
        engine=_read(ENGINE),
        scene=scene,
    )
    outp = pathlib.Path(out_path)
    outp.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024
    print(f"OK -> {out_path}  ({kb:.0f} KB, autocontenido)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma un diagrama hand-drawn autocontenido.")
    ap.add_argument("scene", help="ruta al .scene.js")
    ap.add_argument("output", help="ruta al .html de salida")
    ap.add_argument("--title", default="Diagrama hand-drawn")
    a = ap.parse_args()
    build(a.scene, a.output, a.title)


if __name__ == "__main__":
    main()
