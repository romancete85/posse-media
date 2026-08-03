# Futuro — automatización de clasificados (inmuebles + productos)

> **Estado: investigado, NO comprometido.** Registro de factibilidad y arquitectura para retomar más
> adelante. Fecha de la investigación: 2026-08-02 (dos research agents, con fuentes). No se construyó nada.

## Objetivo
Automatizar la publicación / rotación / actualización de **avisos** en portales de Argentina/LATAM:
- **Inmuebles** (venta + alquiler) — para el proyecto propio "sitios prop".
- **Productos generales** — tipo MercadoLibre / (deRemate ya no existe).

Es el **mismo patrón POSSE** del pipeline de LinkedIn, aplicado a clasificados: **el sitio propio como
fuente de verdad → sindicar avisos a los portales**, con gate humano.

## Veredicto (en una frase)
**MercadoLibre es la única API oficial, self-serve y para individuos que sirve para las dos cosas
(productos e inmuebles) en Argentina.** El resto es manual, murió, o es B2B por CRM/feed.
**Facebook queda FUERA del flujo automático** (decisión tomada 2026-08-02).

## Factibilidad por plataforma

| Plataforma | Productos | Inmuebles | Cómo / letra chica |
|---|:--:|:--:|---|
| **MercadoLibre** | ✅ API | ✅ API | `POST /items`, OAuth. **Individuos permitidos.** Inmuebles = `buying_mode: classified` (leads, sin checkout). **El ancla.** |
| **Zonaprop / Argenprop** | — | ⚠️ CRM | Sin API pública. Ingieren por **conectores de CRM** (Grupo Navent, hoy de QuintoAndar). Requiere cuenta inmobiliaria |
| **Properati** | — | ⚠️ Feed XML | Vía **Proppit** (Lifull Connect) — feed XML. También B2B; alimenta Trovit/Mitula/Nestoria/etc. |
| **Facebook Marketplace** | 🚫 | 🚫 | Productos P2P: **nunca tuvo API**. Inmuebles: el feed de partners **se dio de baja el 13/09/2021**. Manual only. Bots = ban |
| **deRemate / OLX AR** | ⚰️ | ⚰️ | deRemate absorbido por ML (2008). OLX se fue de Argentina (2023). alamaula sin API |
| **CRM hub — Tokko Broker** | — | ✅ práctico | Publica **un aviso a muchos portales** (ML, Zonaprop, Argenprop, Properati). API pública de **lectura**; el push a portales es por sus conectores internos, no un endpoint público de publicación |
| **Integradores (Astroselling…)** | ✅* | — | SaaS **arriba de la API de ML**; no exponen API abierta propia. Atajo con dashboard, no automatización propia |

## Arquitectura propuesta (POSSE para clasificados)

```
Tu sitio (fuente de verdad) → modelo de aviso estructurado → GATE humano
        │
        ├─ MercadoLibre  (API directa)  ← funciona SOLO, sin B2B  ✅ MVP
        └─ Portales inmob. (Zonaprop/Argenprop/Properati)
              vía Tokko Broker (CRM) o feed Proppit XML  ← requiere cuenta inmobiliaria  (fase 2)

Facebook → manual, o ads pagos (catálogo/dynamic real-estate ads). Fuera del flujo automático.
```

Reusa el ADN del pipeline de LinkedIn: el `platforms/` Protocol, el modelo + `content_store`, el gate,
idempotencia, scheduling, `publish-due`.

## MVP recomendado
**Arrancar por la integración con MercadoLibre**, porque es lo único que:
- funciona **solo** (sin onboarding B2B ni CRM pago),
- sirve para **productos e inmuebles**,
- es **oficial** (cero riesgo de ban),
- y encaja en la arquitectura existente.

**Fase 2:** portales inmobiliarios (Zonaprop/Argenprop/Properati) vía **Tokko Broker** (o feed Proppit)
cuando exista la cuenta inmobiliaria. **Facebook:** manual o ads; nunca bots.

## Notas técnicas clave (para el build)
- **ML "User Products":** ML migra a un modelo de publicación nuevo, **arrancando por Argentina en 2026**.
  Construir contra **User Products**, no el modelo viejo. (Docs actualizadas 2026-01-09.)
- **OAuth 2.0** authorization-code; **access token expira a las 6 h** → usar refresh token. App en el DevCenter.
  En AR/MX/BR/CL, la app se valida solo si los **datos de identidad del titular coinciden** con la cuenta.
- **Inmuebles:** `buying_mode: "classified"`; categorías `MLA…` (bajar el árbol por la API de categorías,
  cambian); atributos requeridos (`ROOMS`, `BEDROOMS`, `FULL_BATHROOMS`, `PARKING_LOTS`, `COVERED_AREA`,
  `TOTAL_AREA`, `location` con lat/long); **imagen obligatoria desde 23/02/2026**; leads por webhook
  **"VIS Leads"** (el `notification_url` viejo se deprecia el 23/03/2026). **No** poner datos de contacto
  personales en la descripción (penaliza el aviso).
- **Productos:** tipos de publicación MLA: `free` (**Gratuita**, tope 10 activas) / `gold_special` (Clásica) /
  `gold_pro` (Premium). Descripción por `POST /items/$ID/description`. Actualizar/pausar con `PUT /items/$ID`
  (stock 0 → paused). Usados en moda/deportes: `available_quantity` = 1 y auto-close tras venta.
- **Límites:** ~**1500 req/min por vendedor** (backoff en 429); topes de publicación por **reputación**
  (`GET /marketplace/users/cap`), no por API.
- **Riesgo/ToS:** oficial y seguro = API de ML + conectores de CRM + feed Proppit. **Riesgoso (evitar para
  publicar):** cualquier "API de Zonaprop/Argenprop" de Apify/Parse.bot = **scraping**; y **bots a FB
  Marketplace** = violan ToS, riesgo de baneo.

## A verificar al momento de construir
- Schema exacto del **feed XML de Proppit para Argentina** (los docs públicos que se hallaron eran de otros países).
- Si **Navent** (Zonaprop/Argenprop) ofrece algún feed directo a no-CRM, o estrictamente conectores por CRM.
- Si **Tokko** expone un endpoint público de *push* a portales o solo config de conectores en la UI (la
  evidencia apunta a lo segundo; su API pública es de **lectura**).
- **Category IDs y atributos** de inmuebles AR vigentes (bajar en vivo de la API de categorías).

## Fuentes (curadas)
- MELI Developers · https://developers.mercadolibre.com.ar/
- MELI — Publica inmuebles · https://developers.mercadolibre.com.ar/productos-recibe-notificaciones/publica-inmueble
- MELI — Experiencia inmuebles (leads/webhooks) · https://developers.mercadolibre.com.ar/es_ar/experiencia-para-inmuebles
- MELI — Publica productos · https://developers.mercadolibre.com.ar/es_ar/sobre-nuestra-api/publica-productos
- MELI — Auth · https://developers.mercadolibre.com.ar/en_us/authentication-and-authorization
- Tokko Broker — App Exchange · https://www.tokkobroker.com/es-ar/app-exchange · Developers · https://developers.tokkobroker.com/docs/home
- Proppit XML (Lifull) · https://info.proppit.com/en/support/how-to-prepare-an-xml-file-for-proppit
- FB Marketplace API no existe (2026) · https://www.realtyapi.io/blog/facebook-marketplace-api
- FB — baja del feed de inmuebles (2021) · https://blog.tenantturner.com/changes-coming-for-zumper-and-facebook-marketplace
- Software inmobiliario AR 2026 · https://developargentina.com/blog/software-inmobiliaria-argentina-2026
