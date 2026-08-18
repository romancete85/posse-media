/* engine.js — primitivas de dibujo "hand-drawn" estilo Excalidraw sobre rough.js.
 * Se inyecta inline (junto con rough.min.js + la escena) por build-handdrawn.py.
 * Requiere el global `rough` (rough.min.js) cargado antes.
 *
 * Todo shape lleva un `seed` derivado de sus coordenadas: así el trazo "tembloroso"
 * es DETERMINISTA entre renders (mismo PNG siempre), sin depender de Math.random.
 */
(function () {
  const NS = "http://www.w3.org/2000/svg";

  // Paleta Excalidraw: trazo saturado + relleno pastel. `ink` = tinta negra base.
  const PAL = {
    ink:    { stroke: "#1e1e1e", fill: null },
    gray:   { stroke: "#495057", fill: "#e9ecef" },
    blue:   { stroke: "#1971c2", fill: "#a5d8ff" },
    green:  { stroke: "#2f9e44", fill: "#b2f2bb" },
    violet: { stroke: "#7048e8", fill: "#d0bfff" },
    yellow: { stroke: "#f08c00", fill: "#ffec99" },
    red:    { stroke: "#e03131", fill: "#ffc9c9" },
    grape:  { stroke: "#9c36b5", fill: "#eebefa" },
    teal:   { stroke: "#0c8599", fill: "#99e9f2" },
    cyan:   { stroke: "#1098ad", fill: "#c5f6fa" },
  };

  const pal = (c) => PAL[c] || PAL.gray;
  const seedFor = (a, b) => Math.abs(Math.round(a * 13.37 + b * 7.11)) % 100000 || 1;

  // Path de rectángulo redondeado (rough.js no tiene rounded-rect nativo).
  function rrPath(x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    return `M${x + r} ${y} h${w - 2 * r} a${r} ${r} 0 0 1 ${r} ${r} ` +
           `v${h - 2 * r} a${r} ${r} 0 0 1 ${-r} ${r} h${-(w - 2 * r)} ` +
           `a${r} ${r} 0 0 1 ${-r} ${-r} v${-(h - 2 * r)} a${r} ${r} 0 0 1 ${r} ${-r} z`;
  }

  function HD(svg) {
    const rc = rough.svg(svg);
    const g = document.createElementNS(NS, "g"); // capa de contenido
    svg.appendChild(g);
    let cur = g;                                  // target de append actual
    const add = (n) => { cur.appendChild(n); return n; };

    // Agrupa el dibujo de un nodo en un <g class="grp"> etiquetado (para filtros/hover interactivos).
    function node(id, groups, links, fn) {
      const sub = document.createElementNS(NS, "g");
      sub.setAttribute("class", "grp");
      sub.setAttribute("data-id", id);
      sub.setAttribute("data-groups", groups || "");
      sub.setAttribute("data-links", (links || []).join(" "));
      sub.setAttribute("tabindex", "0");
      g.appendChild(sub);
      const prev = cur; cur = sub;
      try { fn(); } finally { cur = prev; }
      return sub;
    }

    // — Caja redondeada con relleno hachure (el bloque base del estilo).
    function box(x, y, w, h, o = {}) {
      const p = pal(o.color || "gray");
      const opts = {
        stroke: p.stroke, strokeWidth: o.strokeWidth ?? 2.2,
        roughness: o.roughness ?? 1.05, bowing: o.bowing ?? 1.6,
        seed: seedFor(x + w, y + h),
      };
      if (o.fill !== false && p.fill) {
        opts.fill = o.fillColor || p.fill;
        opts.fillStyle = o.fillStyle || "hachure";
        opts.fillWeight = o.fillWeight ?? 2.2;
        opts.hachureGap = o.hachureGap ?? 7;
        opts.hachureAngle = o.hachureAngle ?? -41;
      }
      if (o.dashed) opts.strokeLineDash = [9, 7];
      return add(rc.path(rrPath(x, y, w, h, o.r ?? 14), opts));
    }

    // — Texto Virgil (rough.js no dibuja texto; va como <text> encima).
    function text(x, y, str, o = {}) {
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", x); t.setAttribute("y", y);
      t.setAttribute("font-family", "Virgil, Segoe Print, Comic Sans MS, cursive");
      t.setAttribute("font-size", o.size ?? 18);
      t.setAttribute("text-anchor", o.anchor || "start");
      t.setAttribute("fill", o.fill || "#1e1e1e");
      if (o.opacity != null) t.setAttribute("opacity", o.opacity);
      if (o.weight) t.setAttribute("font-weight", o.weight);
      if (o.letterSpacing) t.setAttribute("letter-spacing", o.letterSpacing);
      t.textContent = str;
      return add(t);
    }

    // — Línea con trazo hand-drawn.
    function line(x1, y1, x2, y2, o = {}) {
      const p = pal(o.color || "ink");
      const opts = { stroke: p.stroke, strokeWidth: o.strokeWidth ?? 2, roughness: o.roughness ?? 1.1, bowing: o.bowing ?? 1, seed: seedFor(x1 + x2, y1 + y2) };
      if (o.dashed) opts.strokeLineDash = [8, 6];
      return add(rc.line(x1, y1, x2, y2, opts));
    }

    // — Flecha con punta dibujada a mano.
    function arrow(x1, y1, x2, y2, o = {}) {
      const p = pal(o.color || "ink");
      line(x1, y1, x2, y2, o);
      const ang = Math.atan2(y2 - y1, x2 - x1);
      const L = o.head ?? 14, spread = 0.42;
      const hopt = { stroke: p.stroke, strokeWidth: o.strokeWidth ?? 2, roughness: 0.7 };
      add(rc.line(x2, y2, x2 - L * Math.cos(ang - spread), y2 - L * Math.sin(ang - spread), { ...hopt, seed: seedFor(x2, y2) }));
      add(rc.line(x2, y2, x2 - L * Math.cos(ang + spread), y2 - L * Math.sin(ang + spread), { ...hopt, seed: seedFor(x2 + 1, y2 + 1) }));
    }

    // — Círculo relleno tipo "bullet" de color.
    function dot(cx, cy, r, color) {
      const p = pal(color);
      return add(rc.circle(cx, cy, r * 2, { stroke: p.stroke, strokeWidth: 2, fill: p.fill, fillStyle: "solid", roughness: 1.2, seed: seedFor(cx, cy) }));
    }

    // — Ícono "chip/CPU" sketchy (para el mini-PC / contenedor).
    function cpu(x, y, s, color = "gray") {
      const p = pal(color);
      const base = { stroke: p.stroke, strokeWidth: 2, roughness: 1, seed: seedFor(x, y) };
      add(rc.rectangle(x, y, s, s, { ...base, fill: p.fill, fillStyle: "solid" }));
      add(rc.rectangle(x + s * 0.28, y + s * 0.28, s * 0.44, s * 0.44, { ...base, seed: seedFor(x + 3, y + 3) }));
      for (let i = 1; i <= 3; i++) {
        const px = x + (s * i) / 4, py = y + (s * i) / 4;
        add(rc.line(px, y - 6, px, y, { ...base, roughness: 0.6, seed: seedFor(px, y) }));
        add(rc.line(px, y + s, px, y + s + 6, { ...base, roughness: 0.6, seed: seedFor(px, y + s) }));
        add(rc.line(x - 6, py, x, py, { ...base, roughness: 0.6, seed: seedFor(x, py) }));
        add(rc.line(x + s, py, x + s + 6, py, { ...base, roughness: 0.6, seed: seedFor(x + s, py) }));
      }
    }

    // — Título centrado con subrayado dibujado a mano (como los diagramas de Excalidraw).
    function title(cx, y, str, o = {}) {
      text(cx, y, str, { size: o.size ?? 40, anchor: "middle", fill: o.fill || "#1e1e1e" });
      const half = (o.underline ?? 150);
      const uy = y + (o.gap ?? 16);
      line(cx - half, uy, cx + half, uy, { color: o.color || "ink", strokeWidth: 3, roughness: 1.4, bowing: 2 });
    }

    // — Pill/etiqueta chica (para tags).
    function pill(x, y, w, h, str, o = {}) {
      box(x, y, w, h, { color: o.color || "gray", r: h / 2, fillStyle: "solid", fillColor: o.fillColor, strokeWidth: 1.6, roughness: 0.9 });
      text(x + w / 2, y + h / 2 + 5, str, { size: o.size ?? 14, anchor: "middle", fill: o.textColor || pal(o.color || "gray").stroke });
    }

    // ── set de íconos sketchy (Excalidraw-like) ────────────────────────────
    const _fill = (c, style = "solid") => ({ fill: pal(c).fill, fillStyle: style });

    // Persona (cabeza + hombros) — el gate humano.
    function person(cx, cy, s, c = "gray") {
      const p = pal(c);
      add(rc.circle(cx, cy, s * 0.62, { stroke: p.stroke, strokeWidth: 2.4, roughness: 1, ..._fill(c), seed: seedFor(cx, cy) }));
      add(rc.path(`M${cx - s * 0.6} ${cy + s * 1.0} a ${s * 0.6} ${s * 0.6} 0 0 1 ${s * 1.2} 0 z`,
        { stroke: p.stroke, strokeWidth: 2.4, roughness: 1, ..._fill(c), seed: seedFor(cx + 1, cy + 1) }));
    }

    // Nube — Claude (la nube).
    function cloud(cx, cy, w, c = "blue") {
      const p = pal(c), k = w / 95, X = (v) => cx - w / 2 + v * k, Y = (v) => cy - 30 * k + v * k;
      const d = `M ${X(30)} ${Y(58)} Q ${X(5)} ${Y(58)} ${X(5)} ${Y(40)} Q ${X(5)} ${Y(26)} ${X(24)} ${Y(24)} ` +
        `Q ${X(28)} ${Y(6)} ${X(50)} ${Y(9)} Q ${X(68)} ${Y(3)} ${X(76)} ${Y(22)} Q ${X(97)} ${Y(22)} ${X(97)} ${Y(41)} ` +
        `Q ${X(97)} ${Y(58)} ${X(74)} ${Y(58)} Z`;
      add(rc.path(d, { stroke: p.stroke, strokeWidth: 2.2, roughness: 1, bowing: 1.1, ..._fill(c), seed: seedFor(cx, cy) }));
    }

    // Engranaje — n8n / orquestación.
    function gear(cx, cy, r, c = "gray") {
      const p = pal(c), o = { stroke: p.stroke, strokeWidth: 2.2, roughness: 1 };
      add(rc.circle(cx, cy, r * 2, { ...o, ..._fill(c), seed: seedFor(cx, cy) }));
      add(rc.circle(cx, cy, r * 0.82, { ...o, seed: seedFor(cx + 2, cy + 2) }));
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI) / 4;
        add(rc.line(cx + Math.cos(a) * r, cy + Math.sin(a) * r, cx + Math.cos(a) * (r + 7), cy + Math.sin(a) * (r + 7),
          { stroke: p.stroke, strokeWidth: 3, roughness: 0.7, seed: seedFor(cx + i, cy + i) }));
      }
    }

    // Escudo — firewall / seguridad.
    function shield(cx, cyTop, s, c = "teal") {
      const p = pal(c), h = s * 1.15;
      const d = `M ${cx} ${cyTop} L ${cx + s / 2} ${cyTop + s * 0.16} L ${cx + s / 2} ${cyTop + s * 0.62} ` +
        `Q ${cx + s / 2} ${cyTop + h * 0.9} ${cx} ${cyTop + h} Q ${cx - s / 2} ${cyTop + h * 0.9} ${cx - s / 2} ${cyTop + s * 0.62} ` +
        `L ${cx - s / 2} ${cyTop + s * 0.16} Z`;
      add(rc.path(d, { stroke: p.stroke, strokeWidth: 2.2, roughness: 1, ..._fill(c), seed: seedFor(cx, cyTop) }));
    }

    // Candado — secrets / vault.
    function lock(cx, cyTop, s, c = "violet") {
      const p = pal(c), bw = s, bh = s * 0.72, bx = cx - bw / 2, by = cyTop + s * 0.5;
      add(rc.path(`M ${cx - s * 0.3} ${by} v ${-s * 0.24} a ${s * 0.3} ${s * 0.3} 0 0 1 ${s * 0.6} 0 v ${s * 0.24}`,
        { stroke: p.stroke, strokeWidth: 2.4, roughness: 0.9, seed: seedFor(cx, cyTop) }));
      add(rc.rectangle(bx, by, bw, bh, { stroke: p.stroke, strokeWidth: 2.2, roughness: 1, ..._fill(c), seed: seedFor(cx + 1, cyTop + 1) }));
      add(rc.circle(cx, by + bh * 0.5, s * 0.16, { stroke: p.stroke, strokeWidth: 2, roughness: 1, fill: p.stroke, fillStyle: "solid", seed: seedFor(cx + 2, cyTop + 2) }));
    }

    // Campana — notificaciones push.
    function bell(cx, cyTop, s, c = "yellow") {
      const p = pal(c);
      add(rc.path(`M ${cx - s * 0.5} ${cyTop + s * 0.82} Q ${cx - s * 0.5} ${cyTop + s * 0.12} ${cx} ${cyTop + s * 0.02} ` +
        `Q ${cx + s * 0.5} ${cyTop + s * 0.12} ${cx + s * 0.5} ${cyTop + s * 0.82} Z`,
        { stroke: p.stroke, strokeWidth: 2.2, roughness: 1, ..._fill(c), seed: seedFor(cx, cyTop) }));
      add(rc.line(cx - s * 0.62, cyTop + s * 0.82, cx + s * 0.62, cyTop + s * 0.82, { stroke: p.stroke, strokeWidth: 2.2, roughness: 0.7, seed: seedFor(cx + 1, cyTop) }));
      add(rc.circle(cx, cyTop + s * 0.98, s * 0.15, { stroke: p.stroke, strokeWidth: 2, roughness: 1, fill: p.stroke, fillStyle: "solid", seed: seedFor(cx + 2, cyTop) }));
    }

    // Cubo isométrico — guest / contenedor.
    function cube(x, y, s, c = "gray") {
      const p = pal(c), d = s * 0.36, base = { stroke: p.stroke, strokeWidth: 2.2, roughness: 1 };
      add(rc.path(`M${x} ${y + d} L${x + d} ${y} L${x + s + d} ${y} L${x + s} ${y + d} Z`, { ...base, ..._fill(c), seed: seedFor(x, y) }));
      add(rc.path(`M${x + s} ${y + d} L${x + s + d} ${y} L${x + s + d} ${y + s} L${x + s} ${y + s + d} Z`, { ...base, ..._fill(c, "hachure"), hachureGap: 5, seed: seedFor(x + 1, y + 1) }));
      add(rc.rectangle(x, y + d, s, s, { ...base, ..._fill(c), seed: seedFor(x + 2, y + 2) }));
    }

    // Cilindro — base de datos / backup (cx = centro x).
    function cylinder(cx, yTop, w, h, c = "green") {
      const p = pal(c), eh = w * 0.34, x = cx - w / 2, base = { stroke: p.stroke, strokeWidth: 2.2, roughness: 1 };
      add(rc.rectangle(x, yTop + eh / 2, w, h - eh, { stroke: p.fill, strokeWidth: 0.5, ..._fill(c), seed: seedFor(cx, yTop) }));
      add(rc.line(x, yTop + eh / 2, x, yTop + h - eh / 2, { ...base, seed: seedFor(cx + 1, yTop) }));
      add(rc.line(x + w, yTop + eh / 2, x + w, yTop + h - eh / 2, { ...base, seed: seedFor(cx + 2, yTop) }));
      add(rc.path(`M ${x} ${yTop + h - eh / 2} A ${w / 2} ${eh / 2} 0 0 0 ${x + w} ${yTop + h - eh / 2}`, { ...base, seed: seedFor(cx + 3, yTop) }));
      add(rc.ellipse(cx, yTop + eh / 2, w, eh, { ...base, ..._fill(c), seed: seedFor(cx + 4, yTop) }));
    }

    // Cabeza-IA (robot amigable) — IA local / Ollama.
    function aihead(cx, cy, s, c = "green") {
      const p = pal(c), w = s * 1.32, h = s * 1.05, x = cx - w / 2;
      const o = { stroke: p.stroke, strokeWidth: 2.2, roughness: 1 };
      add(rc.line(cx, cy - 9, cx, cy, { ...o, strokeWidth: 2, roughness: 0.6, seed: seedFor(cx, cy) }));       // antena
      add(rc.circle(cx, cy - 12, 6, { ...o, fill: p.stroke, fillStyle: "solid", seed: seedFor(cx + 1, cy) }));
      add(rc.path(rrPath(x, cy, w, h, 8), { ...o, ..._fill(c), seed: seedFor(cx + 2, cy) }));                   // cabeza
      add(rc.circle(cx - w * 0.22, cy + h * 0.42, 6, { stroke: p.stroke, strokeWidth: 2, fill: p.stroke, fillStyle: "solid", roughness: 1, seed: seedFor(cx, cy + 1) }));
      add(rc.circle(cx + w * 0.22, cy + h * 0.42, 6, { stroke: p.stroke, strokeWidth: 2, fill: p.stroke, fillStyle: "solid", roughness: 1, seed: seedFor(cx, cy + 2) }));
      add(rc.line(cx - w * 0.18, cy + h * 0.74, cx + w * 0.18, cy + h * 0.74, { stroke: p.stroke, strokeWidth: 2, roughness: 0.7, seed: seedFor(cx, cy + 3) }));  // boca
    }

    // Flecha sobre un path curvo (d = path SVG; tip = {x,y,angle} para la punta).
    function curveArrow(d, tip, o = {}) {
      const p = pal(o.color || "ink");
      const sw = o.strokeWidth ?? 2;
      const opts = { stroke: p.stroke, strokeWidth: sw, roughness: o.roughness ?? 1.1, bowing: o.bowing ?? 1, seed: seedFor(tip.x, tip.y) };
      if (o.dashed) opts.strokeLineDash = [9, 7];
      add(rc.path(d, opts));
      const L = o.head ?? 13, sp = 0.42, a = tip.angle, hopt = { stroke: p.stroke, strokeWidth: sw, roughness: 0.7 };
      add(rc.line(tip.x, tip.y, tip.x - L * Math.cos(a - sp), tip.y - L * Math.sin(a - sp), { ...hopt, seed: seedFor(tip.x, tip.y) }));
      add(rc.line(tip.x, tip.y, tip.x - L * Math.cos(a + sp), tip.y - L * Math.sin(a + sp), { ...hopt, seed: seedFor(tip.x + 1, tip.y + 1) }));
    }

    // Documento con esquina doblada — pipeline / publica.
    function doc(x, y, w, h, c = "gray") {
      const p = pal(c), f = w * 0.28;
      add(rc.path(`M${x} ${y} L${x + w - f} ${y} L${x + w} ${y + f} L${x + w} ${y + h} L${x} ${y + h} Z`, { stroke: p.stroke, strokeWidth: 2.2, roughness: 1, ..._fill(c), seed: seedFor(x, y) }));
      add(rc.path(`M${x + w - f} ${y} L${x + w - f} ${y + f} L${x + w} ${y + f}`, { stroke: p.stroke, strokeWidth: 2, roughness: 1, seed: seedFor(x + 1, y + 1) }));
      for (let i = 0; i < 3; i++) add(rc.line(x + w * 0.18, y + h * 0.42 + i * h * 0.18, x + w * 0.82, y + h * 0.42 + i * h * 0.18, { stroke: p.stroke, strokeWidth: 1.6, roughness: 0.6, seed: seedFor(x + i, y + i) }));
    }

    // ── Interactividad reusable: panel de detalle + filtros opcionales ─────────
    // Los controles van en un <div class="detail"> que el render OCULTA (PNG limpio)
    // pero el artifact de claude.ai muestra. `filters` = [[grupo, label], …] o null.
    function interactive({ detail = {}, base = "", filters = null } = {}) {
      if (!document.getElementById("hd-ui-css")) {
        const style = document.createElement("style");
        style.id = "hd-ui-css";
        style.textContent =
          `.grp{cursor:pointer;transition:opacity .2s}` +
          `.grp:hover,.grp:focus-visible{outline:none;filter:drop-shadow(0 3px 9px rgba(112,72,232,.28))}` +
          `svg.filtered .grp.dim{opacity:.15}` +
          `.hd-ui{margin-top:18px;font-family:"Virgil","Segoe Print",cursive}` +
          `.hd-bar{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:12px}` +
          `.hd-btn{font:600 16px "Virgil",cursive;color:#5c6774;background:#fff;border:2px solid #d3dae2;border-radius:999px;padding:7px 16px;cursor:pointer;transition:.15s}` +
          `.hd-btn:hover{border-color:#7048e8;color:#7048e8}.hd-btn.on{background:#7048e8;border-color:#7048e8;color:#fff}` +
          `.hd-foot{font:400 18px "Virgil",cursive;color:#1e1e1e;background:#f6f8fa;border:2px solid #e9ecef;border-radius:12px;padding:14px 17px;min-height:3.3em;line-height:1.4}`;
        (document.head || document.documentElement).appendChild(style);
      }
      const controls = document.createElement("div");
      controls.className = "detail hd-ui";
      let html = "";
      if (filters) html += `<div class="hd-bar">` +
        filters.map(([gp, l], i) => `<button class="hd-btn${i === 0 ? " on" : ""}" data-g="${gp}">${l}</button>`).join("") + `</div>`;
      html += `<div class="hd-foot" id="hd-foot"></div>`;
      controls.innerHTML = html;
      (svg.closest(".wrap") || document.body).appendChild(controls);

      const foot = controls.querySelector("#hd-foot");
      foot.textContent = base;
      svg.querySelectorAll(".grp[data-id]").forEach((el) => {
        const id = el.getAttribute("data-id");
        const on = () => { if (detail[id]) foot.textContent = detail[id]; };
        const off = () => { foot.textContent = base; };
        el.addEventListener("mouseenter", on); el.addEventListener("mouseleave", off);
        el.addEventListener("focus", on); el.addEventListener("blur", off);
        el.addEventListener("click", () => { if (detail[id]) foot.textContent = detail[id]; });
      });
      if (filters) controls.querySelectorAll(".hd-btn").forEach((b) => b.addEventListener("click", () => {
        const gsel = b.getAttribute("data-g");
        svg.classList.toggle("filtered", gsel !== "");
        svg.querySelectorAll(".grp[data-groups]").forEach((el) => {
          const gs = (el.getAttribute("data-groups") || "").split(" ");
          el.classList.toggle("dim", gsel !== "" && !gs.includes(gsel));
        });
        controls.querySelectorAll(".hd-btn").forEach((x) => x.classList.toggle("on", x === b));
      }));
      return controls;
    }

    return {
      svg, rc, g, add, node, interactive, box, text, line, arrow, curveArrow, dot, cpu, title, pill,
      person, cloud, gear, shield, lock, bell, cube, cylinder, doc, aihead,
      PAL, pal, seedFor,
    };
  }

  HD.PAL = PAL;
  window.HD = HD;
})();
