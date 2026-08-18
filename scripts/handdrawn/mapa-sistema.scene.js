/* mapa-sistema.scene.js — "el mapa completo" en estilo hand-drawn (Excalidraw), íconos sketchy.
 * Misma info que gen-mapa-sistema.py, sanitizada. INTERACTIVO: filtros (IA/Seguridad/Orquestación/
 * Datos) + hover con detalle. Los controles van en un <div class="detail"> que el render OCULTA
 * (así el PNG del feed queda limpio) pero el artifact de claude.ai muestra.
 */
(function () {
  const W = 1020, H = 1490;
  const svg = document.getElementById("cv");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const hd = HD(svg);
  const cx = W / 2;
  const light = (x, y, col) => hd.add(hd.rc.circle(x, y, 26, { stroke: col, strokeWidth: 2, fill: col, fillStyle: "solid", roughness: 1, seed: hd.seedFor(x, y) }));

  // ── Título (no agrupado) ───────────────────────────────────────────────────
  hd.title(cx, 66, "Un homelab operado por IA", { size: 40, underline: 258, gap: 16 });
  hd.text(cx, 104, "el sistema completo · una IA opera la infra, con gobernanza", { size: 18, anchor: "middle", fill: "#495057" });
  hd.pill(852, 34, 150, 34, "✓ sanitizado", { color: "green", fillColor: "#ffffff", textColor: "#2f9e44", size: 15 });

  // ── Zona CONTROL ────────────────────────────────────────────────────────────
  hd.box(36, 132, 948, 320, { color: "violet", dashed: true, fill: false, r: 22 });
  hd.text(58, 160, "CONTROL · EL CEREBRO", { size: 14, fill: "#7048e8", weight: "700", letterSpacing: "1.5" });

  hd.node("gate", "core", [], () => {
    hd.box(380, 154, 260, 80, { color: "violet", dashed: true, r: 16, hachureGap: 9 });
    hd.person(420, 182, 24, "violet");
    hd.text(456, 190, "Yo", { size: 23, fill: "#1e1e1e" });
    hd.text(456, 216, "el gate humano", { size: 15, fill: "#5c6774" });
  });
  hd.arrow(cx, 234, cx, 262, { color: "violet" });

  hd.node("brain", "core ia", [], () => {
    hd.box(140, 266, 740, 168, { color: "blue", r: 16, hachureGap: 9 });
    hd.cloud(210, 322, 96, "blue");
    hd.text(288, 312, "Claude — el cerebro", { size: 27, fill: "#1971c2" });
    hd.text(288, 344, "nube · planifica, decide y conecta", { size: 17, fill: "#495057" });
    let cxp = 288;
    [["MCP · Proxmox", 13], ["conectores", 10], ["GitHub", 6], ["n8n", 3]].forEach(([t, n]) => {
      const w = 22 + n * 8.5;
      hd.pill(cxp, 388, w, 30, t, { color: "blue", fillColor: "#ffffff", size: 13 });
      cxp += w + 12;
    });
  });
  hd.arrow(cx, 434, cx, 462, { color: "violet" });

  hd.node("gov", "core seg", [], () => {
    hd.box(90, 466, 840, 86, { color: "violet", r: 14, hachureGap: 9 });
    light(132, 509, "#2f9e44"); light(170, 509, "#f08c00"); light(208, 509, "#e03131");
    hd.text(244, 503, "Gobernanza · semáforo + ACL", { size: 22, fill: "#1e1e1e" });
    hd.text(244, 530, "el permiso lo da la ACL, no el prompt", { size: 15, fill: "#5c6774" });
  });
  hd.arrow(cx, 552, cx, 584, { color: "violet" });

  // ── Proxmox (contenedor) + guests ──────────────────────────────────────────
  hd.node("proxmox", "core infra", [], () => {
    hd.box(70, 588, 880, 474, { color: "gray", fill: false, r: 18, strokeWidth: 2.6 });
    hd.cube(92, 606, 30, "gray");
    hd.text(156, 630, "Proxmox · la infra", { size: 24, fill: "#1e1e1e" });
    hd.text(156, 656, "2 nodos: producción (read-only IA) / sandbox", { size: 15, fill: "#5c6774" });
    hd.text(926, 632, "guests ↓", { size: 15, anchor: "end", fill: "#5c6774" });
  });

  const GX = [92, 306, 520, 734], GY = [688, 832], GW = 196, GH = 130;
  function guest(id, groups, col, row, color, drawIcon, title, sub) {
    const x = GX[col], y = GY[row];
    hd.node(id, groups, [], () => {
      hd.box(x, y, GW, GH, { color, r: 14, hachureGap: 8, fillWeight: 1.8 });
      drawIcon(x + GW / 2, y);
      hd.text(x + GW / 2, y + 92, title, { size: 19, anchor: "middle", fill: "#1e1e1e" });
      hd.text(x + GW / 2, y + 114, sub, { size: 13, anchor: "middle", fill: "#495057" });
    });
    return { x, y };
  }
  guest("ollama", "ia infra", 0, 0, "green",  (c, y) => hd.aihead(c, y + 24, 30, "green"),        "Ollama",      "IA local · privada");
  const n8n = guest("n8n", "orq infra core", 1, 0, "grape", (c, y) => hd.gear(c, y + 42, 20, "grape"), "n8n",  "orquesta flujos");
  const posse = guest("posse", "orq infra", 2, 0, "blue",   (c, y) => hd.doc(c - 19, y + 20, 38, 44, "blue"), "posse-media", "publica ESTA serie");
  guest("vault", "seg infra", 3, 0, "violet", (c, y) => hd.lock(c, y + 22, 34, "violet"),         "Vaultwarden", "secrets");
  guest("pfsense", "seg infra", 0, 1, "red",  (c, y) => hd.shield(c, y + 22, 34, "red"),          "pfSense",     "firewall · red");
  guest("cloudflare", "seg infra", 1, 1, "yellow", (c, y) => hd.cloud(c, y + 44, 66, "yellow"),   "Cloudflare",  "acceso externo");
  guest("ntfy", "orq infra", 2, 1, "teal",    (c, y) => hd.bell(c, y + 22, 34, "teal"),           "ntfy",        "avisos push");
  // slot 8 = "+ más" (no es nodo)
  hd.box(GX[3], GY[1], GW, GH, { color: "gray", dashed: true, fill: false, r: 14 });
  hd.text(GX[3] + GW / 2, GY[1] + 54, "+ más", { size: 18, anchor: "middle", fill: "#5c6774" });
  hd.text(GX[3] + GW / 2, GY[1] + 80, "Pi-hole · Jellyfin", { size: 13, anchor: "middle", fill: "#5c6774" });
  hd.text(GX[3] + GW / 2, GY[1] + 100, "Kali · …", { size: 13, anchor: "middle", fill: "#5c6774" });
  hd.arrow(n8n.x + GW, n8n.y + GH / 2, posse.x, posse.y + GH / 2, { color: "blue", head: 11 });

  hd.arrow(cx, 1062, cx, 1092, { color: "violet" });

  // ── Backup off-box ─────────────────────────────────────────────────────────
  hd.node("backup", "datos", [], () => {
    hd.box(300, 1096, 420, 106, { color: "green", r: 14, hachureGap: 8 });
    hd.cylinder(352, 1114, 54, 74, "green");
    hd.text(400, 1140, "PBS · Backup off-box", { size: 21, fill: "#2f9e44" });
    hd.text(400, 1166, "otro nodo · restore probado (3-2-1)", { size: 14, fill: "#495057" });
  });

  // ── Roadmap (proyectado) ────────────────────────────────────────────────────
  hd.text(72, 1250, "ROADMAP (proyectado)", { size: 15, fill: "#5c6774", weight: "700", letterSpacing: "1.5" });
  const RX = [72, 378, 684], RW = 264, RH = 112, RY = 1268;
  function future(id, groups, col, drawIcon, title, sub) {
    const x = RX[col];
    hd.node(id, groups, [], () => {
      hd.box(x, RY, RW, RH, { color: "gray", dashed: true, fill: false, r: 14 });
      drawIcon(x + 26, RY + 20);
      hd.text(x + 72, RY + 46, title, { size: 20, fill: "#5c6774" });
      hd.text(x + 26, RY + 84, sub, { size: 13.5, fill: "#5c6774" });
    });
  }
  future("gpu", "roadmap", 0, (x, y) => hd.cpu(x, y, 30, "gray"),         "GPU",      "potencia para la IA local");
  future("node3", "roadmap", 1, (x, y) => hd.cube(x, y, 28, "gray"),      "3er nodo", "HA real / quórum");
  future("offsite", "roadmap datos", 2, (x, y) => hd.cloud(x + 16, y + 18, 54, "gray"), "Off-site", "3ª copia (WireGuard → AWS)");

  const fut = { color: "gray", dashed: true, strokeWidth: 2, head: 12, roughness: 1 };
  hd.curveArrow("M204 1262 C 116 1120, 112 950, 172 828", { x: 172, y: 824, angle: -1.15 }, fut); // GPU → Ollama
  hd.curveArrow("M540 1262 C 660 1230, 802 1232, 802 1070", { x: 802, y: 1066, angle: -1.57 }, fut); // 3er nodo → Proxmox
  hd.curveArrow("M812 1262 C 788 1236, 742 1220, 706 1206", { x: 703, y: 1204, angle: -2.76 }, fut); // off-site → Backup

  // ── Firma ──────────────────────────────────────────────────────────────────
  hd.text(W - 40, H - 26, "❯ Roman Fandrich · homelab", { size: 18, anchor: "end", fill: "#495057" });

  // ── Interactividad: filtros + panel de detalle (oculto en el PNG) ───────────
  const DETAIL = {
    gate: "Yo, el gate humano. Lo ROJO (borrar/restaurar/wipe) SIEMPRE pide mi OK + backup verificado. La IA nunca decide sola lo destructivo.",
    brain: "Claude (nube) es el cerebro: planifica, decide y CONECTA. Opera Proxmox por un token MCP scopeado + conectores (calendar, GitHub) + n8n.",
    gov: "La barrera dura: cada operación se clasifica con un semáforo y el permiso real lo da la ACL de Proxmox (rol+scope), NO el prompt. Un jailbreak no puede exceder la ACL.",
    proxmox: "Proxmox: 2 nodos standalone. Nodo 1 = producción (read-only para la IA); Nodo 2 = sandbox. El sustrato: todo corre acá arriba.",
    ollama: "Ollama: modelos de IA LOCALES en un guest, sin GPU. Para lo privado (generación, RAG, visión). Los datos no salen de casa.",
    n8n: "n8n: orquesta los flujos automáticos (monitoreo, avisos, y el auto-publish de esta serie). El pegamento.",
    posse: "El pipeline posse-media (guest): toma las piezas versionadas y publica sola esta serie. El homelab se auto-promociona.",
    vault: "Vaultwarden: bóveda de secrets self-hosted (tokens, deploy keys). Nada de credenciales sueltas en el repo o los hosts.",
    pfsense: "pfSense: firewall del homelab. Segmentación de red y seguridad perimetral.",
    cloudflare: "Cloudflare Tunnel: expone servicios (el sitio self-hosted de diagramas) sin abrir puertos. Acceso externo seguro.",
    ntfy: "ntfy: notificaciones push. n8n te avisa acá cuando publica, o si el token está por vencer.",
    backup: "Proxmox Backup Server en OTRO nodo (off-box), con restores probados. Regla 3-2-1. La red de seguridad.",
    gpu: "Roadmap: GPU dedicada (VRAM) para modelos más grandes y rápidos en local. Hoy es CPU pura.",
    node3: "Roadmap: un tercer nodo para HA real con quórum. Hoy son 2 standalone (a propósito).",
    offsite: "Roadmap: la 3ª copia off-site (vía túnel WireGuard a AWS). Protege contra el peor caso: incendio/robo del sitio.",
  };
  const FILTERS = [["", "Todo"], ["ia", "🧠 IA"], ["seg", "🔒 Seguridad"], ["orq", "⚙️ Orquestación"], ["datos", "🗄️ Datos"]];
  const base = "👆 Tocá o pasá por cada bloque para ver su rol · o filtrá por IA / Seguridad / Orquestación / Datos.";
  hd.interactive({ detail: DETAIL, base, filters: FILTERS });
})();
