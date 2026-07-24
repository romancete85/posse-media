# Deploy — sitio de diagramas (homelab + Cloudflare Tunnel)

Sitio estático (Caddy) con los diagramas de la serie, expuesto por **Cloudflare Tunnel** (CT 200) →
link propio y permanente, **sin abrir puertos** en pfSense. El contenido es estático y sanitizado
(sin IPs/VLANs/datos), así que exponerlo es de bajo riesgo.

> **Reparto:** el contenido (`public/`) es de este repo (posse-media). El túnel/DNS es tu terreno
> (red/host = operador, gobernanza de proxmox-ai-ops). Estos son los pasos; los aplica el operador.

## 1. Levantar el server (en el homelab)
Copiá `site/` al host de Docker (ej. `docker2` → `/opt/stacks/diagramas`) y:
```bash
cd /opt/stacks/diagramas
docker compose up -d
# sirve en http://<host>:8088  (probar: curl -I http://localhost:8088)
```
> `file_server` sirve directo del volumen: para actualizar un diagrama, editás `public/...` y ya
> queda servido (no hace falta reiniciar el contenedor).

## 2. Exponer por Cloudflare Tunnel (CT 200)
En **Cloudflare Zero Trust → Networks → Tunnels → tu túnel → Public Hostname → Add**:
- **Subdomain:** `diagramas` (o `lab`) · **Domain:** tu dominio en Cloudflare.
- **Service:** `HTTP` → `http://<IP-del-host-docker>:8088`.

Cloudflare crea el DNS + TLS automáticamente. Resultado:
```
https://diagramas.tudominio/                       # index de la serie
https://diagramas.tudominio/diagramas/homelab-serie-1.html   # diagrama pieza 1
```

## 3. Usar el link
- Pegá el link del diagrama en el **comentario** del post (o donde quieras).
- Es **propio y permanente** — no depende de claude.ai ni del partner API.

## Agregar un diagrama nuevo (por pieza de la serie)
1. Generás el HTML (mismo formato que `public/diagramas/homelab-serie-1.html`).
2. Lo guardás en `public/diagramas/<slug>.html` y lo linkeás desde `public/index.html`.
3. Commit + copiás al homelab (o un `git pull` si el stack clona el repo). El túnel ya lo sirve.
