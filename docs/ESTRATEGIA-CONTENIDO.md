# Estrategia de contenido — LinkedIn (marca personal)

Objetivo: **consistencia** para trabajar el algoritmo, ganar visualizaciones y construir autoridad en
**Cloud / DevOps / Seguridad**, con **contenido real basado en proyectos propios** (modelo POSSE).

> **Regla de oro de marca:** solo experiencia general y **proyectos propios**. **Nunca** datos, nombres
> ni detalles de clientes (Tivit / Edenor / MELI / ChileAtiende) — confidencialidad.

---

## 1. Cadencia (comprometida)

- **Arranque: 1 post/semana firme** → **ramp a 2/semana** cuando el flujo salga fluido.
- **Día ancla: martes** (buen horario LinkedIn). Al rampear, 2º día: **jueves**.
- **Nunca saltarse la semana.** Mejor un post simple a tiempo que uno perfecto tarde.
- Reminder automático en Google Calendar (martes; sumar jueves al rampear).

## 2. Pilar (por ahora: **solo A**)

- **A — Cloud / DevOps / Seguridad:** AWS, IaC/Terraform, Kubernetes, homelab Proxmox, automatización, FinOps, seguridad.
- **B (mentoría)** y **C (música)** → más adelante, para humanizar.

## 3. Formatos (rotar)

- **Post texto con hook** (base).
- **Diagrama** — ya tenés el tooling (`posse-render` + sitio interactivo self-hosted).
- **Serie** — la del homelab crea anticipación (el algoritmo premia followers que vuelven).
- A futuro: carruseles, "detrás de escena", lecciones/tips cortos.

## 4. Best-practices del algoritmo (checklist por post)

- **Hook fuerte en la 1ª línea** (se ve antes del "…ver más").
- **Sin links externos en el cuerpo** → link en el **1er comentario** (protege el alcance).
- **3–5 hashtags** relevantes.
- **CTA (pregunta)** al final → comentarios = alcance.
- **Responder TODOS los comentarios**, sobre todo en la **1ª hora**.
- Publicar y quedarte **~30–60 min** interactuando.
- **Horario:** mar–jue, media mañana (ART).
- **No editar** apenas publicado (reinicia el reach).

## 5. Networking activo (amplifica)

- Comentar **con sustancia** en 3–5 posts de tu nicho (Cloud/DevOps LATAM) por semana.
- Conectar con gente del rubro; **aportar > pedir**.
- Mencionar/etiquetar solo cuando es genuino (comunidades, herramientas, autores).

## 6. Cross-post POSSE (a futuro)

- La misma pieza (fuente de verdad versionada) → X / Mastodon / blog propio.
- El pipeline ya está pensado multi-destino (`platforms/`); se activa cuando quieras.

---

## 7. Backlog de contenido (real, pilar A)

**Serie Homelab (proxmox-ai-ops) — el ancla:**
1. ✅ Arquitectura: "IA operativa con límites" *(publicado)*.
2. **Gobernanza de la IA:** verde/amarillo/rojo, ACLs de Proxmox, el gate humano.
3. **Backup / DR off-box:** por qué standalone + PBS, la decisión de no-cluster.
4. **IA local:** Ollama en el homelab → generación/RAG gratis.
5. **La red del homelab** (conceptual, sanitizado): segmentación, por qué un firewall dedicado.
6. **"Errores que cometí armando el homelab"** (mentoría encubierta; engancha).

**Otros temas pilar A (proyectos/experiencia propia):**
7. **Estructura real de un proyecto Terraform** (de `tpintegrador`): módulos + backend remoto (S3+lock).
8. **AWS: 3 costos que no ves venir** (data transfer, NAT, egress) — de tu experiencia.
9. **CI/CD end-to-end:** pipeline con Terraform + Ansible + Kubernetes + GitOps (`tpintegrador`).
10. **De sysadmin a DevOps:** qué automatizar primero (tu transición real).
11. **FinOps básico:** optimización de costos en la nube (tu cert + práctica).
12. **Seguridad en IaC:** escaneo de imágenes (Trivy), least-privilege, manejo de secretos.

> Regenerá ideas nuevas cuando quieras: `posse ideas "<tema>" --n 5 --pilar A` (grounded en tu perfil/proyectos).

---

## 8. Checklist semanal

- [ ] **Lun:** elegir tema del backlog → generar draft (`posse draft` / `posse ideas`).
- [ ] **Mar:** refinar + diagrama si aplica → `posse publish` → link en el **1er comentario**.
- [ ] **Mar (1ª hora):** responder comentarios + comentar en **3–5 posts** del nicho.
- [ ] **(Al rampear) Jue:** 2º post.
- [ ] **Registrar** qué salió + métricas (abajo) para doblar la apuesta en lo que rinde.

## 9. Métricas (sin obsesionarse)

- Impresiones · tasa de comentarios · seguidores nuevos · clics al comentario.
- **Qué pilar/formato/tema rinde → doblar la apuesta.** Iterar mensual.
