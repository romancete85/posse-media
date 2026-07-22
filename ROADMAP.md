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

**Progreso:** módulos 1–6 ✅ (models, content_store, auth, platforms/linkedin, publisher/preview, cli, workflows — **32 tests, todo mockeado**). Falta **7**: validación real end-to-end (crear la app de LinkedIn, `posse auth`, configurar SSM + GitHub Secrets/Variables, primera publicación de prueba) y README final. Ver setup en `README.md`.

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

### Futuro (diseñado, no comprometido)
- **Imágenes/assets** en LinkedIn (`upload_image()` + `assets:` con uso real).
- **Nuevas redes** (X, Mastodon, Instagram…) vía el `Protocol` de `platforms/base.py`.
- **Generación de contenido** upstream del gate (produce piezas `draft`).
- **Integración n8n** (Topología 1): webhook autenticado al endpoint HTTPS público de n8n.
- **Migración a Topología 2** (self-hosted runner en el homelab) si se necesita alcance LAN directo — solo cambia
  *dónde corre el runner*, no el diseño. Ahí sí reconecta proxmox-ai-ops (el runner sería un guest más).
- **OIDC** GitHub↔AWS reemplazando la access key.
