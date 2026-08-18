/* homelab.scene.js — "Proxmox AI-Ops: una infra que opera la IA… con límites" hand-drawn.
 * Serie 1. Misma info que diagrama-homelab.html, sanitizada. Interactivo: hover en cada bloque.
 */
(function () {
  const W = 1040, H = 772;
  const svg = document.getElementById("cv");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const hd = HD(svg);
  const cx = W / 2;

  const globe = (gx, gy, r, c) => {
    const p = hd.pal(c);
    hd.add(hd.rc.circle(gx, gy, r * 2, { stroke: p.stroke, strokeWidth: 2, fill: p.fill, fillStyle: "solid", roughness: 1, seed: hd.seedFor(gx, gy) }));
    hd.add(hd.rc.ellipse(gx, gy, r * 0.9, r * 2, { stroke: p.stroke, strokeWidth: 1.5, roughness: 1, seed: hd.seedFor(gx + 1, gy) }));
    hd.add(hd.rc.line(gx - r, gy, gx + r, gy, { stroke: p.stroke, strokeWidth: 1.5, roughness: 0.7, seed: hd.seedFor(gx, gy + 1) }));
  };

  hd.title(cx, 64, "Proxmox AI-Ops", { size: 40, underline: 190, gap: 15 });
  hd.text(cx, 100, "una infra que opera la IA… con límites", { size: 18, anchor: "middle", fill: "#495057" });
  hd.pill(852, 32, 156, 34, "✓ sin IPs/VLANs", { color: "green", fillColor: "#ffffff", textColor: "#2f9e44", size: 14 });

  // leyenda de zonas
  const LEG = [["Gobernanza", "#f08c00"], ["IA-Ops", "#7048e8"], ["Producción", "#0c8599"], ["Sandbox", "#9c36b5"], ["Backup/DR", "#2f9e44"], ["Proyectado", "#868e96"]];
  let lx = 70;
  LEG.forEach(([lbl, col]) => {
    hd.add(hd.rc.rectangle(lx, 128, 13, 13, { stroke: col, strokeWidth: 1.5, fill: col, fillStyle: "solid", roughness: 1, seed: hd.seedFor(lx, 128) }));
    hd.text(lx + 20, 140, lbl, { size: 14, fill: "#495057" });
    lx += 34 + lbl.length * 8.6;
  });

  // helper: bloque con ícono + título (agrupado, hover)
  function unit(id, x, y, w, h, color, drawIcon, title) {
    hd.node(id, "", [], () => {
      hd.box(x, y, w, h, { color, r: 12, hachureGap: 7, fillWeight: 1.7 });
      drawIcon(x + 34, y + h / 2);
      hd.text(x + 64, y + h / 2 + 6, title, { size: 16.5, fill: "#1e1e1e" });
    });
  }

  // gate + IA-Ops
  unit("gate", 70, 168, 250, 72, "yellow", (c, y) => hd.person(c, y - 12, 22, "yellow"), "Gate humano");
  hd.text(134, 226, "aprueba lo destructivo", { size: 13, fill: "#5c6774" });
  hd.node("ops", "", [], () => {
    hd.box(440, 158, 360, 92, { color: "violet", r: 14, hachureGap: 8 });
    hd.cloud(492, 196, 74, "violet");
    hd.text(548, 190, "IA-Ops", { size: 22, fill: "#7048e8" });
    hd.text(548, 220, "opera vía MCP · contenida · auditada", { size: 14, fill: "#495057" });
  });
  hd.arrow(320, 200, 438, 200, { color: "gray" });
  hd.arrow(500, 250, 360, 306, { color: "gray" });
  hd.arrow(720, 250, 800, 306, { color: "gray" });

  // Nodo 1 · Producción
  hd.box(70, 308, 440, 254, { color: "teal", fill: false, r: 16, strokeWidth: 2.4 });
  hd.text(94, 340, "Nodo 1 · Producción", { size: 18, fill: "#0c8599", weight: "700" });
  unit("fw", 94, 366, 196, 68, "teal", (c, y) => hd.shield(c, y - 16, 30, "teal"), "Firewall");
  unit("dns", 306, 366, 180, 68, "teal", (c, y) => globe(c, y, 15, "teal"), "DNS");
  unit("apps", 94, 456, 392, 72, "teal", (c, y) => hd.cube(c - 15, y - 15, 26, "teal"), "Contenedores / Automatización");

  // Nodo 2 · Sandbox
  hd.box(560, 308, 440, 254, { color: "grape", fill: false, r: 16, strokeWidth: 2.4 });
  hd.text(584, 340, "Nodo 2 · Sandbox / Staging", { size: 18, fill: "#9c36b5", weight: "700" });
  unit("pruebas", 584, 366, 196, 68, "grape", (c, y) => hd.gear(c, y, 18, "grape"), "Pruebas de la IA");
  unit("llm", 796, 366, 180, 68, "grape", (c, y) => hd.aihead(c, y - 15, 26, "grape"), "IA local");
  unit("backup", 584, 456, 392, 72, "green", (c, y) => hd.cylinder(c, y - 22, 40, 46, "green"), "Backup off-box (DR)");

  // promover a prod (dashed, entre contenedores)
  hd.curveArrow("M556 424 L514 424", { x: 514, y: 424, angle: Math.PI }, { color: "grape", dashed: true, strokeWidth: 1.8, head: 11 });
  hd.text(535, 410, "promover", { size: 12, anchor: "middle", fill: "#9c36b5" });

  // Proyectado
  hd.box(70, 592, 930, 108, { color: "gray", dashed: true, fill: false, r: 14 });
  hd.text(94, 624, "Proyectado", { size: 18, fill: "#5c6774", weight: "700" });
  hd.node("future", "", [], () => {
    hd.add(hd.rc.rectangle(80, 636, 910, 54, { stroke: "none", fill: "none", seed: 1 }));
    hd.text(96, 668, "▸ 3er nodo → HA real (quórum)", { size: 15, fill: "#495057" });
    hd.text(416, 668, "▸ GPU → inferencia local", { size: 15, fill: "#495057" });
    hd.text(716, 668, "▸ n8n → orquestación", { size: 15, fill: "#495057" });
  });

  hd.text(W - 40, H - 16, "❯ Roman Fandrich · homelab", { size: 18, anchor: "end", fill: "#495057" });

  const DETAIL = {
    gate: "Gate humano: toda operación destructiva requiere confirmación humana explícita. La IA nunca se auto-otorga permisos.",
    ops: "Claude opera el cluster vía MCP con escritura contenida a un pool sandbox; cada acción queda auditada. El permiso lo da la ACL de Proxmox, no el prompt.",
    fw: "Firewall del homelab: segmentación de red y control de tráfico.",
    dns: "Resolución DNS interna del homelab + ad-block.",
    apps: "Servicios en contenedores y flujos de automatización del día a día.",
    pruebas: "La IA crea, configura y valida guests de cero, sin riesgo para producción. Lo que valida OK se promueve a prod.",
    llm: "Inferencia local con modelos open-source para generación de contenido y RAG, sin costo de API.",
    backup: "Respaldo del cluster fuera del nodo principal: copias off-box para disaster recovery.",
    future: "Próximos pasos: HA real con un tercer nodo (quórum), GPU para IA local fluida, y orquestación de flujos con n8n.",
  };
  hd.interactive({ detail: DETAIL, base: "👆 Tocá o pasá por cada bloque para ver su rol. La regla de oro: el permiso lo da la ACL, nunca un prompt." });
})();
