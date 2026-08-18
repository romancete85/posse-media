#!/usr/bin/env python3
"""Genera diagrama-mapa-sistema.html (arquitectura completa) data-driven.

Zonas + routing curvo + filtros de vista interactivos + logos de marca (cache simple-icons).
Editá ZONES/NODES/LINKS y re-corré:  ./.venv/bin/python scripts/gen-mapa-sistema.py
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS = json.loads((ROOT / "content/assets/_logos-cache.json").read_text())

AC, CL, GR, MU = "var(--accent)", "var(--cloud)", "var(--green)", "var(--muted)"
PX, N8, CF, PF, VW = "#e57000", "#ea4b71", "#f38020", "#c0392b", "#175ddc"


def N(**k):
    d = {"lscale": 2.0, "subs": [], "big": True, "links": [], "groups": "", "tcolor": "var(--ink)",
         "lcolor": AC, "logo": None, "cls": "node"}
    return {**d, **k}


# ── zonas (fondo + etiqueta, detrás de todo) ─────────────────────────────────
ZONES = [
    ("CONTROL · EL CEREBRO", 196, 14, 708, 300, "var(--accent)"),
]

# ── nodos ────────────────────────────────────────────────────────────────────
NODES = [
    N(id="gate", x=430, y=26, w=240, h=82, cls="node gate", title="Yo", groups="core",
      subs=[("el gate humano", MU)], links=["c1"],
      detail="Yo, el gate humano. Lo ROJO (borrar/restaurar/wipe) SIEMPRE pide mi OK + backup verificado. La IA nunca decide sola lo destructivo."),
    N(id="brain", x=225, y=150, w=650, h=150, cls="node brain", logo="anthropic", lcolor="#d97757",
      title="Claude — el cerebro", tcolor=CL, groups="core ia", subs=[("nube · planifica, decide y conecta", MU)],
      links=["c1", "c2"],
      detail="Claude (nube) es el cerebro: planifica, decide y CONECTA. Opera Proxmox por un token MCP scopeado + conectores (calendar, GitHub) + n8n."),
    N(id="gov", x=110, y=340, w=880, h=82, cls="node gov", title="Gobernanza · semáforo + ACL",
      groups="core seg", subs=[("el permiso lo da la ACL, no el prompt", MU)], links=["c2", "c3"],
      detail="La barrera dura: cada operación se clasifica con un semáforo y el permiso real lo da la ACL de Proxmox (rol+scope), NO el prompt. Un jailbreak no puede exceder la ACL."),
    N(id="proxmox", x=110, y=456, w=880, h=366, cls="node container", logo="proxmox", lcolor=PX, lscale=1.9,
      title="Proxmox · la infra", groups="core infra", subs=[("2 nodos: producción (read-only IA) / sandbox", MU)],
      links=["c3", "c4"],
      detail="Proxmox: 2 nodos standalone. Nodo 1 = producción (read-only para la IA); Nodo 2 = sandbox. El sustrato: todo corre acá arriba."),
    # guests — grid 4 columnas
    N(id="ollama", x=122, y=556, w=200, h=118, cls="node local", logo="ollama", lcolor=GR, lscale=1.4,
      title="Ollama", tcolor=GR, groups="ia infra", subs=[("IA local · privada", MU)], big=False,
      detail="Ollama: modelos de IA LOCALES en un guest, sin GPU. Para lo privado (generación, RAG, visión). Los datos no salen de casa."),
    N(id="n8n", x=336, y=556, w=200, h=118, cls="node guest", logo="n8n", lcolor=N8, lscale=1.4,
      title="n8n", groups="orq infra core", subs=[("orquesta flujos", MU)], big=False, links=["d1"],
      detail="n8n: orquesta los flujos automáticos (monitoreo, avisos, y el auto-publish de esta serie). El pegamento."),
    N(id="posse", x=550, y=556, w=200, h=118, cls="node guest", title="posse-media",
      groups="orq infra", subs=[("publica ESTA serie", AC)], big=False, links=["d1"],
      detail="El pipeline posse-media (guest): toma las piezas versionadas y publica sola esta serie. El homelab se auto-promociona."),
    N(id="vault", x=764, y=556, w=200, h=118, cls="node guest", logo="vaultwarden", lcolor=VW, lscale=1.4,
      title="Vaultwarden", groups="seg infra", subs=[("secrets", MU)], big=False,
      detail="Vaultwarden: bóveda de secrets self-hosted (tokens, deploy keys). Nada de credenciales sueltas en el repo o los hosts."),
    N(id="pfsense", x=122, y=688, w=200, h=118, cls="node guest", logo="pfsense", lcolor=PF, lscale=1.4,
      title="pfSense", groups="seg infra", subs=[("firewall · red", MU)], big=False,
      detail="pfSense: firewall del homelab. Segmentación de red y seguridad perimetral."),
    N(id="cloudflare", x=336, y=688, w=200, h=118, cls="node guest", logo="cloudflare", lcolor=CF, lscale=1.4,
      title="Cloudflare", groups="seg infra", subs=[("acceso externo", MU)], big=False, links=["d2"],
      detail="Cloudflare Tunnel: expone servicios (el sitio self-hosted de diagramas) sin abrir puertos. Acceso externo seguro."),
    N(id="ntfy", x=550, y=688, w=200, h=118, cls="node guest", logo="ntfy", lcolor=AC, lscale=1.4,
      title="ntfy", groups="orq infra", subs=[("avisos push", MU)], big=False,
      detail="ntfy: notificaciones push. n8n te avisa acá cuando publica, o si el token está por vencer."),
    N(id="backup", x=340, y=862, w=420, h=112, cls="node pbs", logo="proxmox", lcolor=GR, lscale=1.7,
      title="PBS · Backup off-box", tcolor=GR, groups="datos", subs=[("otro nodo · restore probado (3-2-1)", MU)],
      links=["c4"],
      detail="Proxmox Backup Server en OTRO nodo (off-box), con restores probados. Regla 3-2-1. La red de seguridad."),
    # roadmap (dashed)
    N(id="gpu", x=150, y=1058, w=250, h=104, cls="node future", title="GPU", tcolor=MU, groups="roadmap",
      subs=[("potencia para la IA local", MU)], big=False, links=["r1"],
      detail="Roadmap: GPU dedicada (VRAM) para modelos más grandes y rápidos en local. Hoy es CPU pura."),
    N(id="node3", x=425, y=1058, w=250, h=104, cls="node future", title="3er nodo", tcolor=MU, groups="roadmap",
      subs=[("HA real / quórum", MU)], big=False, links=["r2"],
      detail="Roadmap: un tercer nodo para HA real con quórum. Hoy son 2 standalone (a propósito)."),
    N(id="offsite", x=700, y=1058, w=250, h=104, cls="node future", logo="wireguard", lcolor=MU, lscale=1.3,
      title="Off-site", tcolor=MU, groups="roadmap datos", subs=[("3ª copia (WireGuard→AWS)", MU)], big=False, links=["r3"],
      detail="Roadmap: la 3ª copia off-site (vía túnel WireGuard a AWS). Protege contra el peor caso: incendio/robo del sitio."),
]

# ── links: (id, path, cls) — curvos donde no son verticales ──────────────────
LINKS = [
    ("c1", "M550 108 L550 148", "flow"),
    ("c2", "M550 300 L550 338", "flow"),
    ("c3", "M550 422 L550 454", "flow"),
    ("c4", "M550 822 L550 860", "flow"),
    ("d1", "M536 615 L550 615", "flow small"),                   # n8n -> posse (publica)
    ("d2", "M436 806 C 436 835, 470 845, 500 862", "flow small"),  # cloudflare -> (datos/ext)
    ("r1", "M275 1058 C 275 950, 210 820, 222 676", "flow fut"),   # gpu -> ollama
    ("r2", "M550 1058 C 550 950, 550 900, 550 822", "flow fut"),   # 3er nodo -> proxmox
    ("r3", "M760 1058 C 700 1010, 640 990, 600 976", "flow fut"),  # off-site -> backup
]
CHIPS = [("MCP · Proxmox", 250), ("conectores", 415), ("GitHub", 545), ("n8n", 655)]
FILTERS = [("todo", "Todo", ""), ("ia", "🧠 IA", "ia"), ("seg", "🔒 Seguridad", "seg"),
           ("orq", "⚙️ Orquestación", "orq"), ("datos", "🗄️ Datos", "datos")]


def logo_g(slug, x, y, scale, color):
    p = LOGOS.get(slug)
    return f'<g transform="translate({x},{y}) scale({scale})" fill="{color}"><path d="{p}"/></g>' if p else ""


def emit_zone(z):
    lbl, x, y, w, h, col = z
    return (f'<g opacity="0.5"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="none" '
            f'stroke="{col}" stroke-width="1.5" stroke-dasharray="2 8"/>'
            f'<text x="{x+16}" y="{y+26}" style="font:700 14px var(--font-mono)" fill="{col}" '
            f'letter-spacing="1.5">{lbl}</text></g>')


def emit_node(n):
    x, y, w, h, big = n["x"], n["y"], n["w"], n["h"], n["big"]
    tcls, scls = ("ntitle", "nsub") if big else ("gtitle", "gsub")
    p = [f'<g class="grp" data-id="{n["id"]}" data-links="{" ".join(n["links"])}" data-groups="{n["groups"]}" tabindex="0">']
    p.append(f'<rect class="{n["cls"]}" x="{x}" y="{y}" width="{w}" height="{h}" rx="15"/>')
    tx = x + 20
    if n["logo"]:
        lpx = 24 * n["lscale"]
        ly = y + 20 if n["cls"].endswith("container") else y + (h - lpx) / 2 - (14 if big and n["subs"] else 0)
        p.append(logo_g(n["logo"], x + 20, ly, n["lscale"], n["lcolor"]))
        tx = x + 20 + lpx + (14 if big else 11)
    if n["id"] == "gate":
        p.append(f'<circle cx="{x+42}" cy="{y+32}" r="11" fill="none" stroke="{AC}" stroke-width="3"/>')
        p.append(f'<path d="M{x+24} {y+66} a18 18 0 0 1 36 0" fill="none" stroke="{AC}" stroke-width="3"/>')
        tx = x + 76
    if n["id"] == "gov":
        for i, c in enumerate(("--green", "--amber", "--red")):
            p.append(f'<circle cx="{x+42+i*34}" cy="{y+h/2}" r="13" fill="var({c})"/>')
        tx = x + 148
    ty = y + 40 if n["cls"].endswith("container") else y + (h * 0.44 if n["subs"] else h * 0.6)
    p.append(f'<text class="{tcls}" x="{tx}" y="{ty}" fill="{n["tcolor"]}">{n["title"]}</text>')
    sy = ty + (30 if big else 25)
    for txt, col in n["subs"]:
        p.append(f'<text class="{scls}" x="{tx}" y="{sy}" fill="{col}">{txt}</text>')
        sy += 26 if big else 22
    if n["id"] == "brain":
        for txt, cx in CHIPS:
            wc = 12 + len(txt) * 9
            p.append(f'<rect class="chip" x="{cx}" y="{y+106}" width="{wc}" height="32" rx="16"/>'
                     f'<text class="chipt" x="{cx+wc/2}" y="{y+127}" text-anchor="middle">{txt}</text>')
    if n["id"] == "proxmox":
        p.append(f'<text class="zlbl" x="{x+w-16}" y="{y+34}" text-anchor="end">guests ↓</text>')
        p.append(f'<text class="zlbl" x="{x+w-16}" y="{y+h-16}" text-anchor="end" opacity=".8">+ Pi-hole · Jellyfin · Kali…</text>')
    p.append("</g>")
    return "\n      ".join(p)


ZONES_SVG = "\n      ".join(emit_zone(z) for z in ZONES)
LINKS_SVG = "\n      ".join(
    f'<path class="link" data-c="{i}" d="{d}"/><path class="{c}" data-c="{i}" d="{d}" marker-end="url(#{"am" if "fut" in c else "arw"})"/>'
    for i, d, c in LINKS)
NODES_SVG = "\n      ".join(emit_node(n) for n in NODES)
DATA_JS = ",\n    ".join(f'{n["id"]}: {json.dumps(n["detail"], ensure_ascii=False)}' for n in NODES)
FBTNS = "".join(f'<button class="fbtn{" on" if k=="todo" else ""}" data-g="{g}" data-k="{k}">{lbl}</button>' for k, lbl, g in FILTERS)

HTML = f"""<title>El mapa completo: un homelab operado por IA</title>
<style>
  :root {{--ground:#eef1f4;--surface:#fff;--surface-2:#f6f8fa;--ink:#1a2028;--muted:#5c6774;--hair:#d3dae2;
    --accent:#4f46e5;--accent-bg:#ebeafc;--green:#15803d;--green-bg:#eafaf0;--amber:#d69e2e;--red:#c0392b;
    --cloud:#2563eb;--cloud-bg:#e6effe;--font-mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace;
    --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}}
  @media (prefers-color-scheme:dark){{:root{{--ground:#0e131a;--surface:#161d26;--surface-2:#1c2530;--ink:#e7edf3;
    --muted:#97a4b2;--hair:#2b3644;--accent:#8f8bf5;--accent-bg:#1e1d38;--green:#4ade80;--green-bg:#0f2a19;
    --amber:#f0b429;--red:#f87171;--cloud:#60a5fa;--cloud-bg:#12233d;}}}}
  :root[data-theme="light"]{{--ground:#eef1f4;--surface:#fff;--surface-2:#f6f8fa;--ink:#1a2028;--muted:#5c6774;--hair:#d3dae2;--accent:#4f46e5;--accent-bg:#ebeafc;--green:#15803d;--green-bg:#eafaf0;--amber:#d69e2e;--red:#c0392b;--cloud:#2563eb;--cloud-bg:#e6effe;}}
  :root[data-theme="dark"]{{--ground:#0e131a;--surface:#161d26;--surface-2:#1c2530;--ink:#e7edf3;--muted:#97a4b2;--hair:#2b3644;--accent:#8f8bf5;--accent-bg:#1e1d38;--green:#4ade80;--green-bg:#0f2a19;--amber:#f0b429;--red:#f87171;--cloud:#60a5fa;--cloud-bg:#12233d;}}
  *{{box-sizing:border-box}} body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--font-sans);-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:1060px;margin:0 auto;padding:30px 24px 34px}}
  header{{display:flex;flex-wrap:wrap;align-items:flex-end;gap:12px 22px;justify-content:space-between}}
  .eyebrow{{font-family:var(--font-mono);font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}}
  h1{{font-family:var(--font-mono);font-size:clamp(26px,4vw,40px);font-weight:700;margin:0;letter-spacing:-.01em;line-height:1.08;text-wrap:balance}}
  h1 .chev{{color:var(--accent)}} .badge{{font-family:var(--font-mono);font-size:14px;color:var(--green);border:1.5px solid var(--green);border-radius:999px;padding:5px 12px;white-space:nowrap}}
  .bar{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 2px}}
  .fbtn{{font:600 14px var(--font-mono);color:var(--muted);background:var(--surface);border:1.5px solid var(--hair);border-radius:999px;padding:7px 14px;cursor:pointer;transition:.15s}}
  .fbtn:hover{{border-color:var(--accent);color:var(--accent)}} .fbtn.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
  .map{{margin:8px 0 4px}} .map svg{{width:100%;height:auto;display:block}}
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
  .gtitle{{font:700 19px var(--font-mono)}} .gsub{{font:400 15px var(--font-sans)}}
  .zlbl{{font:600 14px var(--font-mono);fill:var(--muted)}}
  .chip{{fill:var(--surface);stroke:var(--cloud);stroke-width:1}} .chipt{{font:600 14px var(--font-mono);fill:var(--cloud)}}
  .link{{stroke:var(--muted);stroke-width:3;fill:none;opacity:.5}}
  .flow{{stroke:var(--accent);stroke-width:3.4;fill:none;stroke-dasharray:3 13;opacity:.95}}
  .flow.small{{stroke-width:2.6}} .flow.fut{{stroke:var(--muted);opacity:.75}} .link.hot{{opacity:1}} .flow.hot{{stroke-width:5}}
  @media (prefers-reduced-motion:no-preference){{.flow{{animation:dash 1.1s linear infinite}}}} @keyframes dash{{to{{stroke-dashoffset:-16}}}}
  .grp{{cursor:pointer;transition:opacity .2s}} .grp .node{{filter:drop-shadow(0 1px 2px rgba(20,30,45,.05))}}
  .grp:hover .node,.grp:focus-visible .node{{stroke-width:3.5;filter:drop-shadow(0 4px 14px rgba(79,70,229,.20));outline:none}}
  svg.filtered .grp.dim{{opacity:.12}} svg.filtered .link,svg.filtered .flow{{opacity:.1}}
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
  <div class="bar">{FBTNS}</div>
  <div class="map">
    <svg viewBox="0 0 1100 1210" role="img" aria-label="Arquitectura completa del homelab operado por IA">
      <defs>
        <marker id="arw" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--accent)"/></marker>
        <marker id="am" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--muted)"/></marker>
      </defs>
      {ZONES_SVG}
      <text class="zlbl" x="130" y="1042" letter-spacing="1.5" style="font-weight:700">ROADMAP (proyectado)</text>
      {LINKS_SVG}
      {NODES_SVG}
    </svg>
  </div>
  <p class="foot-note">🧠 <b>Dos IAs, un sistema:</b> Claude (nube) planifica y conecta vía MCP; Ollama (local)
    hace lo privado. Todo corre sobre <b>Proxmox</b>, bajo la gobernanza (semáforo + ACL) y el gate humano.
    Usá los filtros de arriba para aislar un camino. (Tocá cada bloque para su rol.)</p>
  <div class="brand"><span class="chev">❯</span> <b>Roman Fandrich</b> · homelab</div>
  <p class="foot" id="foot">👆 Tocá (o pasá por) cada bloque · o filtrá por IA / Seguridad / Orquestación / Datos.</p>
</div>
<script>
  const DATA = {{
    {DATA_JS}
  }};
  const foot = document.getElementById('foot'); const base = foot ? foot.textContent : '';
  const links = document.querySelectorAll('[data-c]');
  const setHot = (ids,on) => links.forEach(l => {{ if (ids.includes(l.getAttribute('data-c'))) l.classList.toggle('hot',on); }});
  document.querySelectorAll('.grp[data-id]').forEach(el => {{
    const id = el.getAttribute('data-id'); const ids = (el.getAttribute('data-links')||'').split(' ').filter(Boolean);
    const on = () => {{ if (DATA[id]) foot.textContent = DATA[id]; setHot(ids,true); }};
    const off = () => {{ foot.textContent = base; setHot(ids,false); }};
    el.addEventListener('mouseenter',on); el.addEventListener('mouseleave',off);
    el.addEventListener('focus',on); el.addEventListener('blur',off);
    el.addEventListener('click',()=>{{ if(DATA[id]) foot.textContent=DATA[id]; }});
  }});
  const svg = document.querySelector('.map svg');
  document.querySelectorAll('.fbtn').forEach(b => b.addEventListener('click', () => {{
    const g = b.getAttribute('data-g');
    svg.classList.toggle('filtered', g !== '');
    document.querySelectorAll('.grp[data-groups]').forEach(el => {{
      const gs = (el.getAttribute('data-groups')||'').split(' ');
      el.classList.toggle('dim', g !== '' && !gs.includes(g));
    }});
    document.querySelectorAll('.fbtn').forEach(x => x.classList.toggle('on', x === b));
  }}));
</script>
"""

(ROOT / "content/assets/diagrama-mapa-sistema.html").write_text(HTML, encoding="utf-8")
print("OK -> content/assets/diagrama-mapa-sistema.html")
