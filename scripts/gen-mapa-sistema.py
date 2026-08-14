#!/usr/bin/env python3
"""Genera el diagrama-mapa-sistema.html (arquitectura completa + roadmap) data-driven.

Los logos de marca salen de content/assets/_logos-cache.json (bajados de simple-icons).
Editá NODES/LINKS y re-corré:  ./.venv/bin/python scripts/gen-mapa-sistema.py
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS = json.loads((ROOT / "content/assets/_logos-cache.json").read_text())

# ── nodos ────────────────────────────────────────────────────────────────────
# cada nodo: id, rect (x,y,w,h), cls, logo(slug|None), lcolor, lscale, title, tcolor,
# subs[(txt,color)], tag(txt,color)|None, big(bool), links[ids], detail
def N(**k):
    defaults = {
        "lscale": 2.0, "subs": [], "tag": None, "big": True, "links": [],
        "tcolor": "var(--ink)", "lcolor": "var(--accent)", "logo": None, "cls": "node",
    }
    return {**defaults, **k}

AC, CL, GR, MU, PX, N8, CF, PF = ("var(--accent)", "var(--cloud)", "var(--green)", "var(--muted)",
                                   "#e57000", "#ea4b71", "#f38020", "#c0392b")

NODES = [
    N(id="gate", x=430, y=24, w=240, h=82, cls="node gate", title="Vos", tcolor="var(--ink)",
      subs=[("el gate humano", "var(--muted)")], links=["c1"],
      detail="Vos, el gate humano. Lo ROJO (borrar/restaurar/wipe) SIEMPRE pide tu OK + backup verificado. La IA nunca decide sola lo destructivo."),
    N(id="brain", x=225, y=150, w=650, h=152, cls="node brain", logo="anthropic", lcolor="#d97757",
      title="Claude — el cerebro", tcolor=CL, subs=[("nube · planifica, decide y conecta", "var(--muted)")],
      links=["c1", "c2"],
      detail="Claude (nube) es el cerebro: planifica, decide y CONECTA. Opera Proxmox por un token MCP scopeado + conectores (calendar, GitHub) + n8n. El que orquesta."),
    N(id="gov", x=110, y=338, w=880, h=82, cls="node gov", title="Gobernanza · semáforo + ACL",
      subs=[("el permiso lo da la ACL, no el prompt", "var(--muted)")], links=["c2", "c3"],
      detail="La barrera dura: cada operación se clasifica con un semáforo, y el permiso real lo da la ACL de Proxmox (rol+scope), NO el prompt. Un jailbreak no puede exceder la ACL."),
    # contenedor infra
    N(id="proxmox", x=110, y=456, w=880, h=376, cls="node container", logo="proxmox", lcolor=PX, lscale=1.9,
      title="Proxmox · la infra", subs=[("2 nodos: producción (read-only IA) / sandbox", "var(--muted)")],
      links=["c3", "c4"],
      detail="Proxmox: 2 nodos standalone. Nodo 1 = producción (read-only para la IA); Nodo 2 = sandbox donde la IA crea/rompe. Es el sustrato: todo corre acá arriba."),
    # guests (dentro de proxmox)
    N(id="ollama", x=142, y=556, w=254, h=116, cls="node local", logo="ollama", lcolor=GR, lscale=1.5,
      title="Ollama", tcolor=GR, subs=[("IA local · privada", "var(--muted)")], big=False,
      detail="Ollama: modelos de IA LOCALES en un guest, sin GPU. Para lo privado (generación, RAG, visión). Los datos no salen de casa."),
    N(id="n8n", x=423, y=556, w=254, h=116, cls="node guest", logo="n8n", lcolor=N8, lscale=1.5,
      title="n8n", subs=[("orquesta · auto-publish", "var(--muted)")], big=False,
      detail="n8n: orquesta los flujos automáticos (monitoreo del cluster, avisos por ntfy, y el auto-publish de esta serie)."),
    N(id="posse", x=704, y=556, w=254, h=116, cls="node guest", title="posse-media",
      subs=[("publica ESTA serie", "var(--accent)")], big=False, links=[],
      detail="El pipeline posse-media (en un guest): toma las piezas versionadas, y publica sola esta serie de LinkedIn. El homelab se auto-promociona."),
    N(id="pfsense", x=142, y=690, w=254, h=116, cls="node guest", logo="pfsense", lcolor=PF, lscale=1.5,
      title="pfSense", subs=[("firewall · seguridad de red", "var(--muted)")], big=False,
      detail="pfSense: el firewall del homelab. Segmentación de red y seguridad perimetral — la infra no está colgada de un módem."),
    N(id="cloudflare", x=423, y=690, w=254, h=116, cls="node guest", logo="cloudflare", lcolor=CF, lscale=1.5,
      title="Cloudflare Tunnel", subs=[("acceso externo · sitio diagramas", "var(--muted)")], big=False,
      detail="Cloudflare Tunnel: expone servicios (como el sitio self-hosted de diagramas) sin abrir puertos. Acceso externo seguro."),
    # backup off-box
    N(id="backup", x=345, y=864, w=410, h=112, cls="node pbs", logo="proxmox", lcolor=GR, lscale=1.7,
      title="PBS · Backup off-box", tcolor=GR, subs=[("otro nodo · restore probado (3-2-1)", "var(--muted)")],
      links=["c4"],
      detail="Proxmox Backup Server en OTRO nodo (off-box), con restores probados. Regla 3-2-1. La red de seguridad que hace que 'la IA opera mi infra' no dé miedo."),
    # roadmap (dashed)
    N(id="gpu", x=150, y=1052, w=250, h=104, cls="node future", title="GPU", tcolor=MU,
      subs=[("potencia para la IA local", "var(--muted)")], big=False, links=["r1"],
      detail="Roadmap: sumar una GPU dedicada (VRAM) para correr modelos más grandes y rápidos en local. Hoy es CPU pura."),
    N(id="node3", x=425, y=1052, w=250, h=104, cls="node future", title="3er nodo", tcolor=MU,
      subs=[("HA real / quórum", "var(--muted)")], big=False, links=["r2"],
      detail="Roadmap: un tercer nodo para HA real con quórum. Hoy son 2 standalone (a propósito: la resiliencia va por backup, no por cluster)."),
    N(id="offsite", x=700, y=1052, w=250, h=104, cls="node future", logo="wireguard", lcolor=MU, lscale=1.4,
      title="Off-site", tcolor=MU, subs=[("3ª copia (WireGuard→cloud)", "var(--muted)")], big=False, links=["r3"],
      detail="Roadmap: la 3ª copia off-site de la regla 3-2-1 (vía túnel WireGuard a la nube). Protege contra el peor caso: incendio/robo del sitio."),
]

# ── links (from,to = puntos; cls) ────────────────────────────────────────────
LINKS = [
    ("c1", "M550 106 L550 148", "flow"),
    ("c2", "M550 302 L550 336", "flow"),
    ("c3", "M550 420 L550 454", "flow"),
    ("c4", "M550 832 L550 862", "flow"),
    ("r1", "M275 1052 L275 810", "flow fut"),   # gpu -> ollama (dashed up)
    ("r2", "M550 1052 L550 834", "flow fut"),   # 3er nodo -> proxmox
    ("r3", "M735 1052 L620 978", "flow fut"),   # off-site -> backup
]

CHIPS = [("MCP · Proxmox", 250), ("conectores", 415), ("GitHub", 545), ("n8n", 655)]


def logo_g(slug, x, y, scale, color):
    p = LOGOS.get(slug)
    return f'<g transform="translate({x},{y}) scale({scale})" fill="{color}"><path d="{p}"/></g>' if p else ""


def emit_node(n):
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    big = n["big"]
    tcls, scls = ("ntitle", "nsub") if big else ("gtitle", "gsub")
    parts = [f'<g class="grp" data-id="{n["id"]}" data-links="{" ".join(n["links"])}" tabindex="0">']
    parts.append(f'<rect class="{n["cls"]}" x="{x}" y="{y}" width="{w}" height="{h}" rx="15"/>')
    tx = x + 22
    if n["logo"]:
        lpx = 24 * n["lscale"]
        ly = y + (h - lpx) / 2 - (14 if big and n["subs"] else 0)
        if n["cls"].endswith("container"):
            ly = y + 22
        parts.append(logo_g(n["logo"], x + 22, ly, n["lscale"], n["lcolor"]))
        tx = x + 22 + lpx + 16
    # gate: person glyph
    if n["id"] == "gate":
        parts.append(f'<circle cx="{x+42}" cy="{y+32}" r="11" fill="none" stroke="var(--accent)" stroke-width="3"/>')
        parts.append(f'<path d="M{x+24} {y+66} a18 18 0 0 1 36 0" fill="none" stroke="var(--accent)" stroke-width="3"/>')
        tx = x + 76
    # gov: semaforo
    if n["id"] == "gov":
        for i, c in enumerate(("--green", "--amber", "--red")):
            parts.append(f'<circle cx="{x+42+i*34}" cy="{y+h/2}" r="13" fill="var({c})"/>')
        tx = x + 148
    ty = y + (h * 0.44 if n["subs"] else h * 0.6)
    if n["cls"].endswith("container"):
        ty = y + 40
    parts.append(f'<text class="{tcls}" x="{tx}" y="{ty}" fill="{n["tcolor"]}">{n["title"]}</text>')
    sy = ty + (30 if big else 26)
    for txt, col in n["subs"]:
        parts.append(f'<text class="{scls}" x="{tx}" y="{sy}" fill="{col}">{txt}</text>')
        sy += 26 if big else 22
    if n["id"] == "brain":
        for txt, cx in CHIPS:
            wchip = 12 + len(txt) * 9
            parts.append(f'<rect class="chip" x="{cx}" y="{y+108}" width="{wchip}" height="32" rx="16"/>'
                         f'<text class="chipt" x="{cx+wchip/2}" y="{y+129}" text-anchor="middle">{txt}</text>')
    if n["id"] == "proxmox":
        parts.append(f'<text class="zonelbl" x="{x+w-16}" y="{y+34}" text-anchor="end">guests ↓</text>')
    parts.append("</g>")
    return "\n      ".join(parts)


LINKS_SVG = "\n      ".join(
    f'<path class="link" data-c="{i}" d="{d}"/><path class="{c}" data-c="{i}" d="{d}" marker-end="url(#{"am" if "fut" in c else "arw"})"/>'
    for i, d, c in LINKS)
NODES_SVG = "\n      ".join(emit_node(n) for n in NODES)
DATA_JS = ",\n    ".join(f'{n["id"]}: {json.dumps(n["detail"], ensure_ascii=False)}' for n in NODES)

HTML = f"""<title>El mapa completo: un homelab operado por IA</title>
<style>
  :root {{
    --ground:#eef1f4;--surface:#fff;--surface-2:#f6f8fa;--ink:#1a2028;--muted:#5c6774;--hair:#d3dae2;
    --accent:#4f46e5;--accent-bg:#ebeafc;--green:#15803d;--green-bg:#eafaf0;--amber:#d69e2e;--red:#c0392b;
    --cloud:#2563eb;--cloud-bg:#e6effe;--font-mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace;
    --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  }}
  @media (prefers-color-scheme:dark){{:root{{--ground:#0e131a;--surface:#161d26;--surface-2:#1c2530;--ink:#e7edf3;
    --muted:#97a4b2;--hair:#2b3644;--accent:#8f8bf5;--accent-bg:#1e1d38;--green:#4ade80;--green-bg:#0f2a19;
    --amber:#f0b429;--red:#f87171;--cloud:#60a5fa;--cloud-bg:#12233d;}}}}
  :root[data-theme="light"]{{--ground:#eef1f4;--surface:#fff;--surface-2:#f6f8fa;--ink:#1a2028;--muted:#5c6774;--hair:#d3dae2;--accent:#4f46e5;--accent-bg:#ebeafc;--green:#15803d;--green-bg:#eafaf0;--amber:#d69e2e;--red:#c0392b;--cloud:#2563eb;--cloud-bg:#e6effe;}}
  :root[data-theme="dark"]{{--ground:#0e131a;--surface:#161d26;--surface-2:#1c2530;--ink:#e7edf3;--muted:#97a4b2;--hair:#2b3644;--accent:#8f8bf5;--accent-bg:#1e1d38;--green:#4ade80;--green-bg:#0f2a19;--amber:#f0b429;--red:#f87171;--cloud:#60a5fa;--cloud-bg:#12233d;}}
  *{{box-sizing:border-box}} body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--font-sans);-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:1040px;margin:0 auto;padding:30px 24px 34px}}
  header{{display:flex;flex-wrap:wrap;align-items:flex-end;gap:12px 22px;justify-content:space-between}}
  .eyebrow{{font-family:var(--font-mono);font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}}
  h1{{font-family:var(--font-mono);font-size:clamp(26px,4vw,40px);font-weight:700;margin:0;letter-spacing:-.01em;line-height:1.08;text-wrap:balance}}
  h1 .chev{{color:var(--accent)}} .badge{{font-family:var(--font-mono);font-size:14px;color:var(--green);border:1.5px solid var(--green);border-radius:999px;padding:5px 12px;white-space:nowrap}}
  .map{{margin:22px 0 4px}} .map svg{{width:100%;height:auto;display:block}}
  .node{{fill:var(--surface);stroke:var(--hair);stroke-width:1.5;transition:stroke .15s,filter .15s}}
  .node.brain{{fill:var(--cloud-bg);stroke:var(--cloud);stroke-width:2.5}}
  .node.gate{{fill:var(--surface-2);stroke:var(--accent);stroke-width:2;stroke-dasharray:7 5}}
  .node.gov{{fill:var(--accent-bg);stroke:var(--accent);stroke-width:2.5}}
  .node.container{{fill:var(--surface-2);stroke:var(--hair);stroke-width:2}}
  .node.local{{fill:var(--green-bg);stroke:var(--green);stroke-width:2}}
  .node.guest{{fill:var(--surface);stroke:var(--hair);stroke-width:1.5}}
  .node.pbs{{fill:var(--green-bg);stroke:var(--green);stroke-width:2.5}}
  .node.future{{fill:var(--surface-2);stroke:var(--muted);stroke-width:2;stroke-dasharray:8 6}}
  .ntitle{{font:700 25px var(--font-mono)}} .nsub{{font:400 19px var(--font-sans)}}
  .gtitle{{font:700 20px var(--font-mono)}} .gsub{{font:400 15px var(--font-sans)}}
  .zonelbl{{font:600 14px var(--font-mono);fill:var(--muted)}}
  .chip{{fill:var(--surface);stroke:var(--cloud);stroke-width:1}} .chipt{{font:600 14px var(--font-mono);fill:var(--cloud)}}
  .link{{stroke:var(--muted);stroke-width:3;fill:none;opacity:.5}}
  .flow{{stroke:var(--accent);stroke-width:3.4;fill:none;stroke-dasharray:3 13;opacity:.95}}
  .flow.fut{{stroke:var(--muted);opacity:.75}} .link.hot{{opacity:1}} .flow.hot{{stroke-width:5}}
  @media (prefers-reduced-motion:no-preference){{.flow{{animation:dash 1.1s linear infinite}}}} @keyframes dash{{to{{stroke-dashoffset:-16}}}}
  .grp{{cursor:pointer}} .grp .node{{filter:drop-shadow(0 1px 2px rgba(20,30,45,.05))}}
  .grp:hover .node,.grp:focus-visible .node{{stroke-width:3.5;filter:drop-shadow(0 4px 14px rgba(79,70,229,.20));outline:none}}
  .foot-note{{margin-top:20px;font-family:var(--font-mono);font-size:16px;line-height:1.5;color:var(--ink);background:var(--surface-2);border:1px solid var(--hair);border-radius:12px;padding:15px 17px}}
  .foot-note b{{color:var(--accent)}}
  .brand{{display:flex;align-items:center;gap:8px;justify-content:flex-end;margin-top:18px;font-family:var(--font-mono);font-size:14px;color:var(--muted)}}
  .brand .chev{{color:var(--accent);font-weight:700}} .brand b{{color:var(--ink);font-weight:600}}
  .foot{{margin-top:12px;font-family:var(--font-mono);font-size:15px;color:var(--ink);background:var(--accent-bg);border:1px solid var(--accent);border-radius:10px;padding:12px 15px;min-height:3.2em}}
</style>

<div class="wrap">
  <header>
    <div>
      <p class="eyebrow">Homelab · serie — el mapa completo</p>
      <h1><span class="chev">❯</span> Un homelab operado por IA: todo el sistema</h1>
    </div>
    <span class="badge">✓ sanitizado</span>
  </header>
  <div class="map">
    <svg viewBox="0 0 1100 1200" role="img" aria-label="Arquitectura completa del homelab operado por IA">
      <defs>
        <marker id="arw" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--accent)"/></marker>
        <marker id="am" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--muted)"/></marker>
      </defs>
      <text class="zonelbl" x="130" y="1036">ROADMAP (proyectado)</text>
      {LINKS_SVG}
      {NODES_SVG}
    </svg>
  </div>
  <p class="foot-note">🧠 <b>Dos IAs, un sistema:</b> Claude (nube) planifica y conecta vía MCP; Ollama (local)
    hace lo privado. Todo corre sobre <b>Proxmox</b>, bajo la gobernanza (semáforo + ACL) y el gate humano,
    con backup off-box. Y n8n orquesta — incluso el pipeline que publicó este post.</p>
  <div class="brand"><span class="chev">❯</span> <b>Roman Fandrich</b> · homelab</div>
  <p class="foot" id="foot">👆 Tocá (o pasá por) cada bloque: se resaltan sus conexiones y te cuento su rol.</p>
</div>
<script>
  const DATA = {{
    {DATA_JS}
  }};
  const foot = document.getElementById('foot'); const base = foot ? foot.textContent : '';
  const links = document.querySelectorAll('[data-c]');
  const setHot = (ids,on) => links.forEach(l => {{ if (ids.includes(l.getAttribute('data-c'))) l.classList.toggle('hot',on); }});
  document.querySelectorAll('.grp[data-id]').forEach(el => {{
    const id = el.getAttribute('data-id');
    const ids = (el.getAttribute('data-links')||'').split(' ').filter(Boolean);
    const on = () => {{ if (DATA[id]) foot.textContent = DATA[id]; setHot(ids,true); }};
    const off = () => {{ foot.textContent = base; setHot(ids,false); }};
    el.addEventListener('mouseenter',on); el.addEventListener('mouseleave',off);
    el.addEventListener('focus',on); el.addEventListener('blur',off);
    el.addEventListener('click',()=>{{ if(DATA[id]) foot.textContent=DATA[id]; }});
  }});
</script>
"""

(ROOT / "content/assets/diagrama-mapa-sistema.html").write_text(HTML, encoding="utf-8")
print("OK -> content/assets/diagrama-mapa-sistema.html")
