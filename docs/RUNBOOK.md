# Runbook — posse-pipeline

Guía operativa para **generar, revisar y publicar** contenido con `posse`.
Documento vivo: lo vamos actualizando a medida que crece el pipeline.

---

## 0. Correr `posse` — el "command not found"

`posse` vive en el venv del repo (`.venv/bin/posse`). Si tipeás `posse` **sin activar el venv** →
`zsh: command not found: posse`. Y conviene correrlo **desde el repo** (el `.env` y las rutas
`content/` son relativas al repo).

Tres formas (elegí una):

1. **Función global (recomendada)** — ya está en tu `~/.zshrc`:
   ```zsh
   posse() { ( cd "$HOME/Desktop/Roman/GITHUB/proxmox/posse-pipeline" && ./.venv/bin/posse "$@" ) }
   ```
   Andá a cualquier carpeta y usá `posse ...`. Recargá una vez: `source ~/.zshrc` (o terminal nueva).
   > Rutas de archivos **externos** (para `--from` / `repurpose`): usá **ruta absoluta**
   > (o `../proxmox-ai-ops/...`, que es repo hermano y resuelve).

2. **Activar el venv:**
   ```zsh
   cd ~/Desktop/Roman/GITHUB/proxmox/posse-pipeline
   source .venv/bin/activate     # ahora 'posse' anda en esta terminal
   ```

3. **Path completo** (desde el repo, sin activar): `.venv/bin/posse ...`

---

## 1. Setup (una vez)

```zsh
cd ~/Desktop/Roman/GITHUB/proxmox/posse-pipeline
python3 -m venv .venv
.venv/bin/pip install ".[dev]"    # instala el paquete (no-editable) + deps de test
cp .env.example .env              # completar claves. NUNCA commitear .env
```
> Tras editar **código**, reinstalá: `.venv/bin/pip install .` (el install es no-editable a propósito).

### Claves en `.env`
- **LinkedIn:** `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_VERSION` (YYYYMM vigente).
- **Ollama (texto, gratis):** `LLM_BACKEND=ollama`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_TIMEOUT=600`.
- **Google (imágenes):** `GEMINI_API_KEY`, `IMAGEN_MODEL`, `GEMINI_VISION_MODEL`.
- Los **tokens de LinkedIn** se guardan solos con `posse auth`.

---

## 2. Autenticación LinkedIn (una vez; repetir cada ~60 días)

```zsh
posse auth        # abre el browser, autorizás, guarda los tokens
```
> Esta app no emite refresh token → cuando expire, volvés a correr `posse auth`.

---

## 3. Generar contenido (IA — SIEMPRE sale `draft`)

```zsh
posse draft "un tema" --pilar A                    # 1 pieza draft
posse draft --from nota.md --model qwen2.5:14b     # desde un archivo + override de modelo
posse ideas "seguridad en IaC" --n 5 --pilar A     # backlog de N ideas
posse repurpose fuente.md --n 5 --pilar A          # fuente larga -> N piezas
posse gen-image content/<pieza>.yaml               # imagen (Google Imagen) + alt (Gemini)
```
- **Grounding:** usa `context/` (perfil + proyectos) para que suene a vos. Apagar: `--no-context`.
- **Contexto GitHub:** `posse context github` (solo repos públicos; los privados de clientes se excluyen).
- **Pilares:** A = Cloud/DevOps · B = Mentoría · C = Música.

---

## 4. Revisar

```zsh
posse list                            # backlog por estado (approved/draft/published)
posse preview content/<pieza>.yaml    # muestra EXACTO qué se publicaría
posse validate content/<pieza>.yaml   # valida el schema
```

---

## 5. Publicar (gate humano)

1. **(Opcional) Imagen/diagrama** → agregá a la pieza:
   ```yaml
   assets:
     - path: content/assets/mi-imagen.png
       alt: "descripción para accesibilidad"
   ```
   (Solo el `cuerpo` sale como texto del post; el `titulo` es metadata interna.)

   **Capturar un diagrama como PNG:**
   - **Automatizado (recomendado):** el diagrama vive como HTML versionado en `content/assets/`.
     ```zsh
     posse-render content/assets/diagrama-homelab.html content/assets/diagrama-homelab.png
     ```
     Sale en alta resolución (2x). Oculta el panel interactivo y el footer para una captura limpia.
     Setup (una vez): `pip install ".[render]" && python -m playwright install chromium`.
   - **Manual (alternativa):** abrí el artifact → tema claro → `Cmd+Shift+4` → seleccioná el bloque →
     `mv ~/Desktop/Captura*.png content/assets/<nombre>.png`.

   > **Diagramas de la serie:** copiás/editás un `content/assets/*.html`, corrés `posse-render`, y la
   > **versión interactiva** (animada) la publicás como artifact para compartir en comentarios.
2. **Aprobar:** en el YAML, `estado: draft` → `estado: approved`.
3. **Publicar:**
   ```zsh
   posse publish content/<pieza>.yaml     # sube la imagen + postea. Idempotente.
   ```
4. **Verificar** en LinkedIn.
5. **Comentario con el link interactivo:**
   - ⚠️ `posse comment` usa la **Comments API**, que es **partner-gated** (`partnerApiSocialActions`):
     **NO** funciona con la app self-serve (`w_member_social`) → **403 ACCESS_DENIED**. Requiere
     aprobación de partner de LinkedIn (no self-serve). El código queda listo por si algún día lo tenés.
   - **Práctico (hoy):** comentá **a mano** en la UI. Hacé público el artifact (**Share**) y pegá el link.

---

## 6. Modelos locales (Ollama, CPU)

| Modelo | Velocidad | Calidad |
|---|---|---|
| `llama3.2:3b` | segundos | básica |
| `qwen2.5:7b` | ~1-2 min | buena |
| `qwen2.5:14b` | varios min | muy buena (default) |

- `--model X` overridea por corrida (sin tocar `.env`).
- `keep_alive` deja el modelo caliente (evita recarga tras idle). GPU = el salto a interactivo fluido.

---

## 7. Troubleshooting

| Síntoma | Causa / fix |
|---|---|
| `command not found: posse` | venv sin activar → usá la función, `source .venv/bin/activate`, o `.venv/bin/posse` |
| `posse` no encuentra `.env` / `content` | lo corrés fuera del repo → usá la función (cd automático) o corré desde el repo |
| `No module named 'posse'` | reinstalá: `.venv/bin/pip install .` |
| Generación lentísima | 14b en CPU + contexto largo = minutos → `--model qwen2.5:7b` o `--no-context`; GPU lo arregla |
| `426 NONEXISTENT_VERSION` | `LINKEDIN_VERSION` caducó → poné el YYYYMM vigente en `.env` |
| Publish "no republica" | la pieza ya está `published` con post_id → es correcto (idempotencia) |
| `posse auth` falla | revisá `LINKEDIN_CLIENT_ID/SECRET` y el redirect `http://localhost:8765/callback` en la app |

---

## Pendientes / a incorporar (se actualiza)
- Flujo por **GitHub Actions** (publicar por label `approved` en un PR + SSM para tokens).
- **Webhook → n8n** al publicar (notificación / fan-out).
- **Difusión local** (Stable Diffusion en el homelab) como alternativa gratis a Imagen.
- **Alt text local** con un modelo de visión en Ollama (llava / llama3.2-vision).
