/* gobernanza.scene.js — "Gobernanza de la IA" hand-drawn. Semáforo verde/amarillo/rojo + ACL.
 * Misma info que diagrama-gobernanza.html, sanitizada. Interactivo: hover en cada franja → detalle.
 */
(function () {
  const W = 960, H = 838;
  const svg = document.getElementById("cv");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const hd = HD(svg);
  const cx = W / 2;

  hd.title(cx, 66, "Gobernanza de la IA", { size: 40, underline: 210, gap: 16 });
  hd.text(cx, 104, "cómo dejo que una IA opere mi infra… sin romper nada", { size: 18, anchor: "middle", fill: "#495057" });
  hd.pill(792, 34, 150, 34, "✓ sanitizado", { color: "green", fillColor: "#ffffff", textColor: "#2f9e44", size: 15 });

  // regla de oro
  hd.box(40, 140, 880, 74, { color: "violet", r: 14, hachureGap: 9, fillWeight: 1.6 });
  hd.text(64, 175, "La regla de oro: el permiso lo da la ACL de Proxmox (control técnico),", { size: 17, fill: "#1e1e1e" });
  hd.text(64, 200, "no el prompt. Cada operación se clasifica con un semáforo. 👇", { size: 17, fill: "#1e1e1e" });

  const LANES = [
    { id: "green",  color: "green",  sat: "#2f9e44", tag: "VERDE",    kind: "Read-only",
      ex: "Leer inventario, estado, storage (get_*). Sin efecto de estado.", out: "Auto-aprobable — sin riesgo, en cualquier scope." },
    { id: "amber",  color: "yellow", sat: "#f08c00", tag: "AMARILLO", kind: "Reversible",
      ex: "Crear/arrancar/apagar, snapshots, editar RAM/CPU/tags.", out: "Permitido solo dentro del pool sandbox que la ACL autoriza." },
    { id: "red",    color: "red",    sat: "#e03131", tag: "ROJO",     kind: "Destructivo",
      ex: "Borrar, rollback, restaurar sobre existente, wipe de disco.", out: "Gate humano + backup verificado, SIEMPRE. Nunca auto-aprobado." },
  ];

  LANES.forEach((L, i) => {
    const y = 246 + i * 146, x = 40, w = 880, h = 130;
    hd.node(L.id, "", [], () => {
      hd.box(x, y, w, h, { color: L.color, r: 16, hachureGap: 9, fillWeight: 1.7 });
      // columna de luz + tag
      hd.add(hd.rc.circle(x + 66, y + 52, 46, { stroke: L.sat, strokeWidth: 2.5, fill: L.sat, fillStyle: "solid", roughness: 1.1, seed: hd.seedFor(x, y) }));
      hd.text(x + 66, y + 102, L.tag, { size: 17, anchor: "middle", fill: L.sat, weight: "700" });
      hd.line(x + 132, y + 18, x + 132, y + h - 18, { color: L.color, strokeWidth: 1.5, roughness: 1 });
      // cuerpo
      hd.text(x + 156, y + 42, L.kind, { size: 22, fill: L.sat });
      hd.text(x + 156, y + 74, L.ex, { size: 15.5, fill: "#495057" });
      hd.text(x + 156, y + 104, L.out, { size: 15.5, fill: "#1e1e1e" });
    });
  });

  hd.box(40, 700, 880, 74, { color: "red", r: 14, hachureGap: 9, fillWeight: 1.5 });
  hd.text(64, 735, "🔒 Barrera dura = ACL (rol + scope, por pveum). Un error de prompt NO puede exceder", { size: 16, fill: "#1e1e1e" });
  hd.text(64, 760, "lo que la ACL permite. La IA nunca se auto-otorga permisos.", { size: 16, fill: "#1e1e1e" });

  hd.text(W - 40, H - 20, "❯ Roman Fandrich · homelab", { size: 18, anchor: "end", fill: "#495057" });

  const DETAIL = {
    green: "Lecturas (get_nodes, get_vms, get_storage…): no cambian estado → auto-aprobables en cualquier scope. La IA ve TODO el cluster, pero solo mira.",
    amber: "Crear/arrancar/apagar, snapshots, editar RAM/CPU/tags. Reversibles. Solo dentro del pool sandbox que la ACL autoriza; producción sigue read-only.",
    red: "delete, rollback_snapshot, restore sobre existente, wipe de disco. SIEMPRE confirmación humana explícita + backup verificado ANTES. Nunca auto-aprobado.",
  };
  hd.interactive({ detail: DETAIL, base: "👆 Tocá o pasá por cada franja del semáforo para ver qué incluye y cómo se aprueba." });
})();
