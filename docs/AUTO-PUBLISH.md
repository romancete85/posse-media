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
No puedo cablear n8n desde acá (el conector pide autorización interactiva). Dos formas, elegí una:

**Opción 1 — Webhook** (n8n en Docker, posse en otro host):
1. En el host donde vive posse, corré el webhook (dejalo como servicio):
   ```bash
   POSSE_WEBHOOK_TOKEN=<algo-random-largo> ./.venv/bin/python scripts/webhook.py --port 8790
   ```
2. En n8n: nodo **Schedule** (ej. diario 09:00 ART) → nodo **HTTP Request**:
   - Method: `POST`
   - URL: `http://<host-posse>:8790/publish-due`
   - Header: `X-Posse-Token: <el mismo token>`
   - (para probar sin publicar: URL `…/publish-due?dry_run=1`)
3. Respuesta JSON: `{"published": ["2026-07-28-…"], "dry_run": false}`.

**Opción 2 — Directo** (n8n y posse en el mismo host):
- nodo **Schedule** → nodo **Execute Command** (o **SSH**): `posse publish-due`
- Más simple, sin webhook. Requiere que n8n pueda ejecutar el binario `posse`.

### ⚠️ Límite del token de LinkedIn (importante)
El token de LinkedIn **expira ~60 días** y la app **no emite refresh token** (no hay forma
self-serve de evitarlo). Un cron desatendido funciona *dentro* de esa ventana; después hay que
re-autenticar a mano:
```bash
posse token-status   # ✅/⚠️/❌ con los días restantes
posse auth           # re-autenticar cuando queden pocos días (abre el navegador)
```
Sugerencia: un segundo Schedule en n8n que corra `token-status` semanal y te avise (email/Telegram)
cuando queden < 7 días.

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
