# metrics — informes de rendimiento (raw)

Exports crudos de analíticas de cada publicación (el Excel que baja LinkedIn), archivados y versionados.
El respaldo fino, por si querés el detalle (impresiones por día, demografía, clics, etc.).

## Convención
- Un archivo por post, en `metrics/<plataforma>/`, nombrado con el **id de la pieza**:
  `metrics/linkedin/2026-08-11-ia-local-en-casa.xlsx`
- Así se correlaciona 1:1 con `content/<id>.yaml` — mismo nombre, fácil de cruzar.

## Dos capas (raw + resumen)
1. **Raw (acá):** el Excel completo de LinkedIn = archivo histórico.
2. **Resumen estructurado:** los números clave (impresiones/reacciones/comentarios/seguidores) se cargan
   al YAML de la pieza con
   `posse metrics content/<id>.yaml --impresiones N --reacciones N --comentarios N --seguidores N`,
   y de ahí sale `posse report` (qué tema/formato rinde).

O sea: **el Excel es el respaldo; el `metricas:` de la pieza es lo consultable.**

## Idea a futuro
Un `posse metrics-import <xlsx>` que parsee el Excel y complete el `posse metrics` solo. Por ahora, manual.
