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

### Frente futuro (GATEADO) — Animación en el feed = video
LinkedIn muestra la imagen del post **estática** (no interactivo, no animado); la versión interactiva/animada
va como **link al artifact en un comentario** (patrón actual). Para animación **dentro del feed** hay que subir
**MP4**, lo que implica dos piezas nuevas:
1. **Render animado → MP4**: Playwright graba la página (webm) + `imageio-ffmpeg` (trae ffmpeg) → MP4. Sin ffmpeg de sistema.
2. **LinkedIn Videos API**: `register upload` de video + upload (chunked) + referencia en el post — más compleja que la Images API.
El `gen-image`/diagrama estático + link interactivo cubre el caso hoy; el video es un proyecto dedicado.

### Frente — Sitio de diagramas self-hosted ✅ construido · deploy = operador
Sitio estático (Caddy) con los diagramas interactivos/animados de la serie, en `site/`. Se expone por
**Cloudflare Tunnel** (CT 200) → link **propio y permanente** (`https://diagramas.<dominio>/...`), sin
depender de claude.ai ni del partner API, y sin abrir puertos (contenido estático + sanitizado = bajo riesgo).
El **contenido** (`site/public/`) es de este repo; el **túnel/DNS** lo cablea el operador (red/host). Ver `site/DEPLOY.md`.

### Futuro (diseñado, no comprometido)
- **Difusión local (GATEADO)** — Stable Diffusion / ComfyUI como servicio del homelab para generar
  imágenes gratis (mismo patrón HTTP que Ollama). Es un **proyecto aparte**, lo arranca el operador con
  `proxmox-ai-ops`. Acá entraría como un `generate_fn` alternativo en `generators/images.py`.
- **Nuevas redes** (X, Mastodon, Instagram…) vía el `Protocol` de `platforms/base.py`.
- **Integración n8n** (Topología 1): webhook autenticado al endpoint HTTPS público de n8n.
- **Migración a Topología 2** (self-hosted runner en el homelab) si se necesita alcance LAN directo — solo cambia
  *dónde corre el runner*, no el diseño. Ahí sí reconecta proxmox-ai-ops (el runner sería un guest más).
- **OIDC** GitHub↔AWS reemplazando la access key.
