# posse-pipeline

Capa de **ingeniería** de un pipeline de contenido POSSE (*Publish on your Own Site, Syndicate Elsewhere*)
para marca personal. Una **fuente de verdad versionada** (piezas YAML en `content/`) que se **sindica** a
redes, con un **gate de aprobación humana** antes de publicar.

> **Alcance:** esto construye SOLO la capa de ingeniería. La **redacción del contenido se hace en otro lado**;
> acá entra como un archivo YAML ya escrito.

## Estado

**Fase 1 — publicar en un perfil personal de LinkedIn.** Una sola plataforma, diseñado para agregar más después.
Este repo está en **scaffold**: estructura y contratos definidos, implementación módulo por módulo pendiente
(ver `ROADMAP.md`).

## Arquitectura (decisiones tomadas)

- **Fuente de verdad:** Git. Cada pieza es un archivo YAML versionado en `content/`.
- **Runner / orquestación:** **GitHub Actions** (cloud git-native). No corre en el homelab.
- **Gate humano:** poner el label **`approved`** a un PR dispara la publicación (`workflow_dispatch` = fallback manual).
- **Secretos:**
  - `client_id` / `client_secret` de la app LinkedIn → **GitHub Secrets**.
  - Tokens de LinkedIn (rotan: access ~60d, refresh ~365d) → **AWS SSM Parameter Store (SecureString + KMS)**.
  - Auth de Actions → AWS: **access key** en GitHub Secrets (OIDC = upgrade posterior, sin rediseño).
- **Motor hosting-agnóstico:** `models` / `content_store` / `platforms` no saben quién los invoca. Los entrypoints
  (CLI, workflows de Actions, futuro webhook n8n) son finos.

### Modelo de contenido (schema de la pieza)

```yaml
id: 2026-07-21-mi-post        # <fecha>-<slug>
pilar: A                      # A=cloud/devops · B=mentoria · C=musica
estado: draft                 # draft | approved | published
destinos: [linkedin]
titulo: Título de la pieza
cuerpo: |
  Texto del post.
assets: []                    # rutas a imágenes/video (Fase 1: sin uso)
hashtags: []
publicado:
  linkedin: { fecha: null, url: null, post_id: null }
```

## Requisitos técnicos de LinkedIn (respetados por diseño)

- **Auth:** OAuth 2.0 + OpenID Connect. Productos de la app: *"Sign In with LinkedIn using OpenID Connect"* +
  *"Share on LinkedIn"*.
- **Scope:** `w_member_social` (self-serve, sin aprobación de partner) — más `openid profile` para el `sub`/URN.
- **Publicación:** Posts API — `POST https://api.linkedin.com/rest/posts` (**no** el endpoint UGC legacy).
  Headers `LinkedIn-Version` (`YYYYMM`) y `X-Restli-Protocol-Version: 2.0.0`.
- **Rate limit:** ~100 llamadas/día/miembro. Se loguea; ante fallo se corta (sin retry silencioso).

## Setup (paso a paso)

> Los comandos `posse ...` se implementan en fases siguientes; este README ya documenta el flujo objetivo.

### 1. App de LinkedIn
1. Crear la app en <https://www.linkedin.com/developers/apps>.
2. Agregar los productos **Sign In with LinkedIn using OpenID Connect** y **Share on LinkedIn**.
3. Anotar `Client ID` y `Client Secret`.
4. En *Auth → Authorized redirect URLs*, agregar `http://localhost:8765/callback` (para el flujo local de una vez).

### 2. Entorno local
```bash
python -m venv .venv && source .venv/bin/activate
pip install ".[dev]"         # instala el paquete + deps de test. Tras editar codigo, reinstalar.
cp .env.example .env         # completar client_id/secret, región AWS, path del parámetro SSM
```

> **Nota (dev):** se usa install no-editable a propósito — algunos entornos macOS/Homebrew no
> honran los `.pth` del editable install (`pip install -e`), y el comando `posse` no encuentra el
> paquete. Los tests corren contra `src/` igual (pytest `pythonpath`). Para iterar sin reinstalar:
> `PYTHONPATH=src python -m posse ...`.

### 3. Autenticación (una sola vez)
```bash
posse auth        # abre el browser, captura el callback en localhost, obtiene tokens + person URN,
                  # y los guarda en SSM Parameter Store (SecureString)
```

### 4. Primera pieza de prueba
```bash
# 1. crear content/<fecha>-<slug>.yaml (estado: draft) en una branch, abrir PR
posse validate content/2026-07-21-mi-post.yaml   # valida el schema
posse preview   content/2026-07-21-mi-post.yaml   # muestra EXACTO qué se publicaría
# 2. poner el label 'approved' al PR  ->  el workflow publica y commitea el estado 'published'
```

## Secretos y seguridad

- **Nunca** se commitea `.env` ni tokens (ver `.gitignore`).
- Los tokens viven en SSM, no en el repo ni en el árbol de trabajo.
- El webhook a n8n (futuro) irá **autenticado** (token/HMAC), nunca abierto.

## Extensibilidad (diseñada, no construida)

- **Nueva red social:** un archivo en `src/posse/platforms/` implementando el `Protocol` de `base.py` +
  `destinos:` crece. El core no cambia.
- **Generación de contenido (texto/imágenes):** etapa *upstream* del gate que produce piezas `draft` + `assets`;
  el publisher nunca genera (preserva el gate humano). Imágenes en LinkedIn = `upload_image()` en `linkedin.py`.
- **Integración n8n (Topología 1):** el pipeline hace `POST` autenticado al webhook HTTPS público de n8n;
  n8n hace el fan-out homelab-local. Seam documentado, no activo en Fase 1.
