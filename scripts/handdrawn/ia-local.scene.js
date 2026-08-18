/* ia-local.scene.js — escena "IA local en casa" en estilo hand-drawn.
 * Data-driven: editá MODELS / META y se redibuja. Usa las primitivas de engine.js (HD).
 * El canvas SVG lo crea build-handdrawn.py; acá sólo dibujamos.
 */
(function () {
  const W = 920, H = 660;

  const META = {
    title: "IA local en casa",
    subtitle: "4 modelos · 1 mini-PC · sin GPU · nada sale de casa",
    container: "mini-PC · contenedor Ollama (sin GPU)",
    note: "keep_alive los mantiene calientes en RAM (si no, ~20s de recarga por llamada). " +
          "En CPU es lento, pero es gratis, sin rate-limits y privado.",
    brand: "❯ Roman Fandrich · homelab",
  };

  // Un modelo por tarea (mismo mapeo de color que el post: verde/azul/violeta/amarillo).
  const MODELS = [
    { name: "llama3.2:3b",     color: "green",  task: "Borradores rápidos, tareas simples", tag: "liviano" },
    { name: "qwen2.5:14b",     color: "blue",   task: "Cuando importa la calidad del texto", tag: "lento en CPU" },
    { name: "nomic-embed-text", color: "violet", task: "RAG: busca en la doc de mis proyectos", tag: "embeddings" },
    { name: "llava:7b",        color: "yellow", task: "Lee imágenes → alt-text accesible", tag: "visión" },
  ];

  const svg = document.getElementById("cv");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W);
  svg.setAttribute("height", H);
  const hd = HD(svg);

  // — Título + subrayado a mano.
  hd.title(W / 2, 66, META.title, { size: 42, underline: 168, gap: 18 });
  hd.text(W / 2, 108, META.subtitle, { size: 19, anchor: "middle", fill: "#495057" });

  // — Badge "sanitizado" arriba a la derecha.
  hd.pill(742, 34, 150, 34, "✓ sanitizado", { color: "green", fillColor: "#ffffff", textColor: "#2f9e44", size: 15 });

  // — Contenedor (mini-PC): caja punteada que agrupa los modelos.
  const CX = 60, CY = 150, CW = 800, CH = 300;
  hd.box(CX, CY, CW, CH, { color: "gray", dashed: true, fill: false, r: 18 });
  hd.cpu(CX + 24, CY + 22, 34, "gray");
  hd.text(CX + 74, CY + 46, META.container, { size: 21, fill: "#1e1e1e" });

  // — 4 modelos en grilla 2×2 dentro del contenedor.
  const bx = [CX + 24, CX + 412], by = [CY + 74, CY + 190];
  const BW = 364, BH = 100;
  MODELS.forEach((m, i) => {
    const x = bx[i % 2], y = by[i < 2 ? 0 : 1];
    hd.box(x, y, BW, BH, { color: m.color, r: 15, hachureGap: 8 });
    hd.dot(x + 34, y + 50, 13, m.color);
    hd.text(x + 62, y + 42, m.name, { size: 21, fill: "#1e1e1e" });
    hd.text(x + 62, y + 72, m.task, { size: 16, fill: "#343a40" });
    // tag arriba-derecha (angosto, para no pisar nombres largos)
    const tw = 10 + m.tag.length * 7.8;
    hd.pill(x + BW - tw - 14, y + 15, tw, 25, m.tag, { color: m.color, fillColor: "#ffffff", size: 12.5 });
  });

  // — Nota keep_alive (banda inferior, amarilla).
  const NY = 476, NW = W - 120;
  hd.box(60, NY, NW, 96, { color: "yellow", r: 14, hachureGap: 8, fillWeight: 1.8 });
  hd.text(84, NY + 30, "🔌 el truco que mueve la aguja:", { size: 18, fill: "#1e1e1e" });
  // texto largo partido en 2 líneas
  hd.text(84, NY + 56, "keep_alive los mantiene calientes en RAM (si no, ~20s de recarga por llamada).", { size: 16, fill: "#343a40" });
  hd.text(84, NY + 80, "En CPU es lento, pero es gratis, sin rate-limits y privado.", { size: 16, fill: "#343a40" });

  // — Firma.
  hd.text(W - 40, H - 26, META.brand, { size: 18, anchor: "end", fill: "#495057" });
})();
