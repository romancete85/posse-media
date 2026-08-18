/* backup-dr.scene.js — "HA no es backup: qué te salva de qué" hand-drawn. Matriz amenaza × solución.
 * Misma info que diagrama-backup-dr.html, sanitizada. Interactivo: hover en cada amenaza → detalle.
 */
(function () {
  const W = 980, H = 850;
  const svg = document.getElementById("cv");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const hd = HD(svg);
  const cx = W / 2;

  // ✓ y ✕ dibujados a mano
  const check = (x, y, s, c) => { hd.line(x - s * 0.42, y + s * 0.02, x - s * 0.08, y + s * 0.36, { color: c, strokeWidth: 4, roughness: 1.1 }); hd.line(x - s * 0.08, y + s * 0.36, x + s * 0.46, y - s * 0.4, { color: c, strokeWidth: 4, roughness: 1.1 }); };
  const cross = (x, y, s, c) => { hd.line(x - s * 0.4, y - s * 0.4, x + s * 0.4, y + s * 0.4, { color: c, strokeWidth: 4, roughness: 1.1 }); hd.line(x + s * 0.4, y - s * 0.4, x - s * 0.4, y + s * 0.4, { color: c, strokeWidth: 4, roughness: 1.1 }); };

  hd.title(cx, 66, "HA no es backup", { size: 42, underline: 190, gap: 16 });
  hd.text(cx, 104, "qué te salva de qué", { size: 18, anchor: "middle", fill: "#495057" });
  hd.pill(812, 34, 150, 34, "✓ sanitizado", { color: "green", fillColor: "#ffffff", textColor: "#2f9e44", size: 15 });

  hd.box(40, 140, 900, 74, { color: "violet", r: 14, hachureGap: 9, fillWeight: 1.6 });
  hd.text(64, 175, "Un cluster te salva de que se muera un nodo.", { size: 17, fill: "#1e1e1e" });
  hd.text(64, 200, "De TODO lo demás te salva un restore — off-box y probado.", { size: 17, fill: "#1e1e1e" });

  // columnas
  const TX = 40, TW = 520, HX = 588, BX = 770, CW = 172;
  hd.text(HX + CW / 2, 250, "Cluster / HA", { size: 18, anchor: "middle", fill: "#e03131", weight: "700" });
  hd.text(BX + CW / 2, 250, "Backup off-box", { size: 18, anchor: "middle", fill: "#2f9e44", weight: "700" });

  const ROWS = [
    { id: "nodo",     t: "Se muere un nodo (hardware)", ha: [true, "failover"],  bk: [true, "restore"] },
    { id: "borrado",  t: "Borrado por error (rm -rf)",  ha: [false, "no ayuda"], bk: [true, "restore"] },
    { id: "update",   t: "Update que rompe todo",       ha: [false, "no ayuda"], bk: [true, "restore"] },
    { id: "ransom",   t: "Ransomware / corrupción",     ha: [false, "se replica"], bk: [true, "off-box"] },
    { id: "incendio", t: "Se quema el sitio entero",    ha: [false, "no ayuda"], bk: [true, "off-site"] },
  ];
  const RH = 74, RY = 272;
  ROWS.forEach((r, i) => {
    const y = RY + i * (RH + 10);
    hd.node(r.id, "", [], () => {
      hd.box(TX, y, TW, RH, { color: "gray", r: 12, fill: false, strokeWidth: 2 });
      hd.text(TX + 22, y + RH / 2 + 6, r.t, { size: 17, fill: "#1e1e1e" });
      [[HX, r.ha], [BX, r.bk]].forEach(([x, cell]) => {
        const ok = cell[0];
        hd.box(x, y, CW, RH, { color: ok ? "green" : "red", r: 12, hachureGap: 7, fillWeight: 1.6 });
        if (ok) check(x + CW / 2, y + RH / 2 - 4, 24, "green");
        else cross(x + CW / 2, y + RH / 2 - 4, 20, "red");
        hd.text(x + CW / 2, y + RH - 12, cell[1], { size: 13, anchor: "middle", fill: ok ? "#2f9e44" : "#e03131" });
      });
    });
  });

  hd.box(40, 700, 900, 78, { color: "yellow", r: 14, hachureGap: 9, fillWeight: 1.5 });
  hd.text(64, 733, "🗄️ Por eso: 2 nodos standalone + PBS en OTRO nodo (off-box) + restores probados.", { size: 16, fill: "#1e1e1e" });
  hd.text(64, 759, "La regla 3-2-1. Y ojo: un backup NO probado no es un backup.", { size: 16, fill: "#1e1e1e" });

  hd.text(W - 40, H - 18, "❯ Roman Fandrich · homelab", { size: 18, anchor: "end", fill: "#495057" });

  const DETAIL = {
    nodo: "Se muere un nodo: el cluster hace failover a otro (HA). El backup también sirve: restaurás en otro nodo. Es el único caso donde HA ayuda.",
    borrado: "rm -rf o un delete de más: el otro nodo del cluster tiene… lo mismo, ya borrado. HA no ayuda. El restore desde el backup, sí.",
    update: "Un update o cambio que rompe todo: se propaga; el cluster no te devuelve el estado anterior. El backup (o un snapshot previo), sí.",
    ransom: "Ransomware / corrupción: se replica al nodo par. Por eso el backup tiene que ser OFF-BOX (y mejor, retenido/inmutable), nunca en la misma caja.",
    incendio: "Se quema el sitio entero: los dos nodos se van juntos. Solo te salva un backup OFF-SITE. Es el corazón de la regla 3-2-1.",
  };
  hd.interactive({ detail: DETAIL, base: "👆 Tocá o pasá por cada amenaza para ver por qué HA no alcanza y el backup sí." });
})();
