# Auto-publish, cross-post y métricas

Guía operativa de tres frentes nuevos del pipeline:
- **A — Auto-publicar** piezas `approved` en su fecha (lo dispara n8n).
- **C — Cross-post** a Mastodon y X/Twitter (multi-destino).
- **Métricas** — registro manual + reporte (la API de LinkedIn es partner-gated).

> El **gate humano sigue intacto**: nada se publica si no está `approved`. La automatización solo
> decide *cuándo* se dispara y *a qué redes*, nunca *qué* sale.

---

## A — Auto-publicar en fecha (`publish-due`)

### Cómo funciona
1. A la pieza le agregás una fecha objetivo:
   ```yaml
   estado: approved        # el gate: sin approved no se publica
   programado: 2026-07-28  # a partir de esta fecha, publish-due la publica
   ```
2. Un cron corre `posse publish-due` a diario. Publica lo `approved` cuya fecha ya llegó
   (`programado <= hoy`), **idempotente**: lo ya publicado se saltea; sin `programado` o con
   fecha futura, no se toca.
   ```bash
   posse publish-due --dry-run   # lista qué publicaría, sin publicar
   posse publish-due             # publica de verdad
   ```
   > La fecha se compara en **UTC** por defecto (Buenos Aires = UTC-3). Si el cron corre a la
   > mañana ART, la fecha coincide. El runner define la TZ.

### Enganche en n8n
n8n corre en el homelab: **VMID 115 `n8n-sandbox`, pool `ai-managed`, `http://192.168.100.213:5678`**
(healthz OK; REST API `/api/v1` habilitada, requiere `X-N8N-API-KEY` = `/root/.n8n-api-key`; también
detrás del túnel `n8n.sysdevops.cloudns.be`). Es alcanzable desde la LAN. Dos formas, elegí una:

> El **conector MCP** de claude.ai ("n8n") es aparte y pide OAuth interactivo; no hace falta para esto —
> la REST API de n8n alcanza para crear el workflow (con la API key) o se arma a mano en la UI.

### Deploy real (armado por proxmox-ai-ops)
`posse` corre en su propio guest, disparado por n8n vía webhook:

| Pieza | Detalle |
|---|---|
| **Guest** | LXC **VMID 116 `posse-runner` · `192.168.100.171`** · pool `ai-managed` · Debian 13 · onboot=1 · unprivileged |
| **Runtime** | `/opt/posse/.venv` (Python 3.13) · corre como usuario `posse` (no root) |
| **Servicio** | `posse-webhook.service` (systemd, hardened) — sirve `8790` (publish) + `8791` (token-status) |
| **Secreto** | `POSSE_WEBHOOK_TOKEN` en `/etc/posse/webhook.env` (`0640 root:posse`, **fuera del repo**) |
| **Firewall** | nftables dropea `8790/8791` si el origen no es RFC1918 (**solo-LAN**) |
| **Workflows n8n** | `posse-publish-due` (diario 09:00 ART → `POST .171:8790/publish-due` → ntfy) · `posse-token-check` (lunes 09:00 → `GET .171:8791/token-status` → avisa si < 7 días) |

**Contrato de los endpoints** (ambos exigen header `X-Posse-Token`):
```
POST 8790 /publish-due[?dry_run=1]  -> {"published": [...ids...], "dry_run": bool}
GET  8791 /token-status             -> {"valido": bool, "dias_restantes": int|null,
                                        "expira": str|null, "mensaje": "token válido, N días restantes"}
```
El `8791` es **read-only** (rechaza POST con 405); el `8790` rechaza GET. Separados a propósito para que
el firewall/n8n traten distinto lo que muta de lo que solo lee.

### Pasos de deploy (humano — el código y la auth llevan secretos)
En el guest `posse-runner` (después de que ai-ops dejó la infra lista):
```bash
# 1. copiar el código a /opt/posse (como root; ej. rsync/scp desde tu Mac o git clone con deploy key)
# 2. instalar y permisos:
sudo -u posse /opt/posse/.venv/bin/pip install /opt/posse
posse-fixperms                       # helper que dejó ai-ops
# 3. crear /opt/posse/.env con las claves de la app de LinkedIn (NO el token, ese lo genera `posse auth`)
# 4. login OAuth de LinkedIn (una vez, abre navegador):
sudo -u posse /opt/posse/.venv/bin/posse auth
# 5. arrancar el webhook:
systemctl start posse-webhook
```
Recién ahí activás los dos workflows en n8n (ai-ops los dejó **inactivos** para no fallar contra un puerto muerto).

### ⚠️ Límite del token de LinkedIn (importante)
El token de LinkedIn **expira ~60 días** y la app **no emite refresh token** (no hay forma
self-serve de evitarlo). Un cron desatendido funciona *dentro* de esa ventana; después hay que
re-autenticar a mano:
```bash
posse token-status   # ✅/⚠️/❌ con los días restantes
posse auth           # re-autenticar cuando queden pocos días (abre el navegador)
```
Ya está cubierto: el workflow **`posse-token-check`** (lunes 09:00) pega a `GET :8791/token-status` y
te avisa por ntfy cuando queden < 7 días (o si no puede interpretar la respuesta).

---

## C — Cross-post (Mastodon + X/Twitter)

Una pieza puede ir a varias redes: `destinos: [linkedin, mastodon]`. `posse publish` recorre los
destinos pendientes (idempotente por plataforma). Filtrás con `posse publish <pieza> --destino mastodon`.

### Mastodon (gratis, self-serve) ✅
1. En tu instancia: **Preferences → Development → New application**, scopes `write:statuses` + `write:media`.
   Copiás el **access token**.
2. En `.env`:
   ```
   MASTODON_INSTANCE=https://mastodon.social
   MASTODON_ACCESS_TOKEN=...
   MASTODON_MAX_CHARS=500
   ```
3. Listo: agregá `mastodon` a `destinos` y publicá.

### X/Twitter (API PAGA) 🔒
La API de posteo de X requiere el tier **Basic (~USD 100/mes)**. El cliente está listo; sin las 4
claves tira un error claro. Cuando tengas acceso (developer.twitter.com, app OAuth 1.0a Read+Write):
```
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
```
> Subir imágenes a X todavía no está implementado (usa otro flujo, v1.1 media/upload). Para X,
> publicá texto por ahora.

### Adaptar el texto por red (`posse adapt`)
Los posts del homelab superan los 280/500 chars. Cada red puede tener su **variante**:
```yaml
variantes:
  twitter:  { cuerpo: "versión de 280…", hashtags: [Proxmox, IA] }
  mastodon: { cuerpo: "versión de 500…" }
```
La generás con IA (Ollama) y la revisás (el gate sigue):
```bash
posse adapt content/2026-07-28-….yaml mastodon
posse adapt content/2026-07-28-….yaml twitter
```
Si no hay variante y el texto excede el límite, `publish` **falla con un mensaje claro** (no trunca a ciegas).

---

## Métricas (registro manual + reporte)

**Por qué a mano:** la API de analytics de LinkedIn (`memberCreatorPostAnalytics`) existe pero vive
dentro de la **Community Management API, partner-gated**: requiere Company Page + demo + un producto
multi-usuario, y rechaza el uso personal. La Member Data Portability API es solo EEA/Suiza y ni
siquiera trae analytics. Conclusión: **para un perfil personal no hay lectura self-serve por API.**
Se copian los números de *"Ver analíticas"* del post (10 segundos) y el pipeline hace el análisis.

```bash
# registrar (copiás de la UI de LinkedIn)
posse metrics content/2026-07-23-….yaml --impresiones 1200 --reacciones 18 --comentarios 3 --clics 25

# reporte: qué pieza/pilar rinde (ordena por impresiones + engagement rate por pilar)
posse report
```
Quedan versionadas en la pieza (`metricas.linkedin`), así medís qué tema/formato rinde y doblás la apuesta.

---

## Referencia de comandos nuevos

| Comando | Qué hace |
|---|---|
| `posse publish-due [--dry-run]` | Publica lo `approved` con `programado <= hoy` (lo corre n8n/cron). |
| `posse token-status` | Días restantes del token de LinkedIn (avisa antes de que expire). |
| `posse publish <p> --destino mastodon` | Publica solo en un destino. |
| `posse adapt <p> mastodon\|twitter` | Genera con IA la variante corta para esa red. |
| `posse metrics <p> --impresiones N …` | Registra métricas a mano. |
| `posse report` | Reporte de rendimiento por pieza/pilar. |
