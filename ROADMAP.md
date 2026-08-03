# Roadmap — posse-pipeline

Pipeline de contenido POSSE. Repo **independiente** (no vinculado a proxmox-ai-ops mientras corra en cloud).
Este doc ordena las fases de ingeniería; la redacción de contenido queda fuera de alcance.

## Decisiones de arquitectura (cerradas)

| Tema | Decisión |
|---|---|
| Ubicación | Repo hermano independiente. Sin puntero en proxmox-ai-ops (el pipeline no toca el cluster). |
| Fuente de verdad | Git — piezas YAML versionadas en `content/`. |
| Hosting / runner | GitHub Actions (cloud git-native). |
| Gate humano | Label `approved` en PR + `workflow_dispatch` manual. |
| Auth Actions → AWS | Access key en GitHub Secrets (OIDC = upgrade posterior). |
| Token store | AWS SSM Parameter Store (SecureString + KMS). |
| Integración n8n | Topología 1 (n8n público como puente). Seam de webhook, no activo en Fase 1. |

## Fases

### Fase 0 — Scaffold ✅ (este commit)
- Estructura de carpetas, `pyproject`, `.env.example`, `.gitignore`.
- Contratos y esqueletos de módulos (sin lógica funcional).
- Workflows esqueleto (`publish`, `refresh-tokens`).
- README con setup objetivo + pieza de ejemplo.

### Fase 1 — Publicar en LinkedIn (perfil propio)

**Progreso:** módulos 1–6 ✅ (**33 tests**). **Validado end-to-end en LinkedIn real (2026-07-22):** `posse auth` OK + `posse publish` local → **201 Created** (`urn:li:share:...`), pieza reescrita a `published`. Pendiente (opcional): flujo por **GitHub Actions** (Pasos C/D del README — SSM + Secrets), para publicar por PR en vez de local.

Implementación módulo por módulo, cada uno con tests:
1. **`models` + `content_store`** — schema tipado de la pieza + load/validate/reescritura in-place del YAML.
   Tests: validación, round-trip preservando comentarios, transición de estado.
2. **`auth`** — flujo OpenID Connect (authorization-code + callback local) + refresh; `token_store` con backend
   SSM (prod) y LocalJson (dev); cache del person URN (`sub` vía `/userinfo`).
3. **`platforms/linkedin`** — cliente Posts API (`POST /rest/posts`, headers de versión), mapeo de errores,
   rate-limit. Tests con HTTP mockeado (nunca la API real).
4. **`publisher` + `preview`** — orquesta approved → publish → published (**idempotente**); render de "qué se publica".
5. **`cli`** — `auth · validate · preview · publish`.
6. **Workflows** — `publish.yml` (label `approved` → preview en PR → publish → commit del estado) y
   `refresh-tokens.yml` (cron → refresh → SSM).
7. **README** — completar el paso a paso con los comandos reales + primera publicación de prueba.

**Gate de salida de Fase 1:** una pieza real pasa `draft → approved (label) → published` con `post_id`/url
commiteados de vuelta, de forma idempotente, y el refresh de token funciona.

### Frente 1 — Imágenes en LinkedIn ✅
`assets: [{path, alt}]` (1..N) + `LinkedInPublisher._upload_image` (Images API) → `content.media` / `multiImage`. Video sigue fuera de alcance.

### Frente 2 — Generación con IA (upstream del gate) ✅ texto · ✅ imágenes
Todo produce `estado: draft`; el gate humano sigue intacto.
- **Texto (`posse draft` / `posse repurpose`)** — backend **pluggable** (`LLM_BACKEND`):
  **ollama** (default, homelab, gratis) | **claude** (API). Structured outputs en ambos.
- **Imágenes (`posse gen-image`)** — Google Imagen genera; **Gemini visión** escribe el alt; a `assets:`.

### Frente 3 — Auto-publicar en fecha ✅ (lo dispara n8n)
`Pieza.programado` (YYYY-MM-DD) + `posse publish-due` (publica lo `approved` vencido, idempotente) +
`scripts/webhook.py` (webhook stdlib con token compartido). n8n hace **Schedule → HTTP Request** (o
**Execute Command** directo). El **gate humano intacto**: solo se publica lo `approved`.
**Límite:** el token de LinkedIn expira ~60 días sin refresh → `posse token-status` avisa; se re-autentica
a mano. Ver **`docs/AUTO-PUBLISH.md`**. n8n corre en la LAN (VMID 115 `ai-managed`,
`http://192.168.100.213:5678`, REST API con `X-N8N-API-KEY`); el workflow se crea por API o en la UI.

### Frente 4 — Cross-post multi-red ✅ Mastodon · 🔒 X (API paga)
Una pieza va a varios `destinos: [linkedin, mastodon]`. **Mastodon** self-serve (token simple, media+alt,
idempotencia por id). **X/Twitter** listo pero gateado tras la API paga (~USD 100/mes). Texto por red vía
`Pieza.variantes[destino]` + `posse adapt <pieza> <red>` (genera la versión corta con IA). Registry con
credenciales por plataforma; el token de LinkedIn se carga solo si un destino lo necesita.

### Frente 5 — Métricas ✅ log manual (API partner-gated)
Investigado: la API de analytics de LinkedIn (`memberCreatorPostAnalytics`) es **partner-gated** para
perfiles personales (Community Management API: Company Page + demo + producto multi-usuario; rechaza uso
personal). Member Data Portability = solo EEA/Suiza y sin analytics. → **No hay lectura self-serve por API.**
Solución: `posse metrics` (registro manual desde la UI, 10 seg) + `posse report` (qué pilar/tema rinde).

### Frente futuro (GATEADO) — Animación en el feed = video
LinkedIn muestra la imagen del post **estática** (no interactivo, no animado); la versión interactiva/animada
va como **link al artifact en un comentario** (patrón actual). Para animación **dentro del feed** hay que subir
**MP4**, lo que implica dos piezas nuevas:
1. **Render animado → MP4**: Playwright graba la página (webm) + `imageio-ffmpeg` (trae ffmpeg) → MP4. Sin ffmpeg de sistema.
2. **LinkedIn Videos API**: `register upload` de video + upload (chunked) + referencia en el post — más compleja que la Images API.
El `gen-image`/diagrama estático + link interactivo cubre el caso hoy; el video es un proyecto dedicado.

### 🎯 Cadencia de contenido (COMPROMISO recurrente)
**Publicar en LinkedIn: 1/semana firme → ramp a 2/semana.** Foco **pilar A** (Cloud/DevOps/Seguridad),
contenido **real** basado en proyectos propios (nunca clientes). Estrategia completa, backlog y checklist
semanal en **`docs/ESTRATEGIA-CONTENIDO.md`**. Reminder automático en el calendario (martes; jueves al rampear).

**Checklist semanal (mínimo):**
- [ ] Elegir tema del backlog + generar draft (`posse draft`/`ideas`).
- [ ] Refinar + diagrama si aplica + `posse publish` + link en el 1er comentario.
- [ ] Responder comentarios (1ª hora) + comentar en 3–5 posts del nicho.
- [ ] (Al rampear) 2º post de la semana.

### Frente — Sitio de diagramas self-hosted ✅ construido · deploy = operador
Sitio estático (Caddy) con los diagramas interactivos/animados de la serie, en `site/`. Se expone por
**Cloudflare Tunnel** (CT 200) → link **propio y permanente** (`https://diagramas.<dominio>/...`), sin
depender de claude.ai ni del partner API, y sin abrir puertos (contenido estático + sanitizado = bajo riesgo).
El **contenido** (`site/public/`) es de este repo; el **túnel/DNS** lo cablea el operador (red/host). Ver `site/DEPLOY.md`.

### Futuro (diseñado, no comprometido)
- **Clasificados — POSSE para avisos (proyecto aparte)** — automatizar publicación/rotación de **inmuebles**
  (proyecto "sitios prop") + **productos** en Argentina/LATAM. Investigado 2026-08-02: **MercadoLibre API**
  es el ancla (oficial, self-serve, individuos, sirve productos e inmuebles); portales inmob.
  (Zonaprop/Argenprop/Properati) = **fase 2** vía CRM (Tokko) o feed Proppit; **Facebook FUERA** del flujo
  automático (sin API legal; bots = ban). Reusa el ADN de este pipeline. **Detalle + fuentes: `docs/FUTURO-CLASIFICADOS.md`**.
- **Difusión local (GATEADO)** — Stable Diffusion / ComfyUI como servicio del homelab para generar
  imágenes gratis (mismo patrón HTTP que Ollama). Es un **proyecto aparte**, lo arranca el operador con
  `proxmox-ai-ops`. Acá entraría como un `generate_fn` alternativo en `generators/images.py`.
- **Nuevas redes** (X, Mastodon, Instagram…) vía el `Protocol` de `platforms/base.py`.
- **Integración n8n** (Topología 1): webhook autenticado al endpoint HTTPS público de n8n.
- **Migración a Topología 2** (self-hosted runner en el homelab) si se necesita alcance LAN directo — solo cambia
  *dónde corre el runner*, no el diseño. Ahí sí reconecta proxmox-ai-ops (el runner sería un guest más).
- **OIDC** GitHub↔AWS reemplazando la access key.
