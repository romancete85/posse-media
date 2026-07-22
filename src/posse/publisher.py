"""Orquestacion: pieza approved -> publish -> published. Idempotente.

- Gate: solo publica piezas en estado 'approved' (o 'published' -> no-op idempotente).
- Idempotencia por destino: si ya tiene post_id en esa plataforma, NO republica.
- Refresca el access token si esta por expirar, antes de publicar.
- Tras publicar OK, marca la pieza (content_store) y loguea.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Callable

from posse import content_store
from posse.auth import oauth
from posse.auth.token_store import TokenBundle, TokenStore, get_token_store
from posse.config import Settings, get_settings
from posse.models import Estado
from posse.platforms import get_publisher

log = logging.getLogger("posse.publisher")

_REFRESH_MARGIN = dt.timedelta(minutes=5)


class GateError(RuntimeError):
    """La pieza no esta 'approved' — el gate no deja publicar."""


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _ensure_fresh(
    bundle: TokenBundle,
    settings: Settings,
    store: TokenStore,
    clock: Callable[[], dt.datetime],
) -> TokenBundle:
    """Refresca el access token si esta vencido o por vencer, y persiste el nuevo bundle."""
    expira = dt.datetime.fromisoformat(bundle.access_expires_at)
    if clock() >= expira - _REFRESH_MARGIN:
        log.info("access token por expirar (%s); refrescando", bundle.access_expires_at)
        bundle = oauth.refresh(bundle, settings)
        store.save(bundle)
    return bundle


def publish(
    path: str | Path,
    *,
    settings: Settings | None = None,
    store: TokenStore | None = None,
    client=None,
    clock: Callable[[], dt.datetime] | None = None,
) -> None:
    """Publica una pieza approved en sus destinos, idempotente."""
    settings = settings or get_settings()
    store = store or get_token_store(settings)
    clock = clock or _utcnow

    pieza = content_store.load(path)
    if pieza.estado not in (Estado.APPROVED, Estado.PUBLISHED):
        raise GateError(
            f"la pieza '{pieza.id}' esta en '{pieza.estado.value}'; solo se publica 'approved'"
        )

    pendientes = [d for d in pieza.destinos if not pieza.esta_publicado_en(d)]
    if not pendientes:
        log.info("pieza '%s': nada para publicar (todos los destinos ya publicados)", pieza.id)
        return

    bundle = store.load()
    if bundle is None:
        raise RuntimeError("no hay tokens guardados; corre `posse auth` primero")
    bundle = _ensure_fresh(bundle, settings, store, clock)

    for destino in pendientes:
        pub = get_publisher(
            destino,
            access_token=bundle.access_token,
            person_urn=bundle.person_urn,
            version=settings.linkedin_version,
            client=client,
        )
        result = pub.publish(pieza)
        content_store.marcar_publicado(
            path, destino, fecha=result.fecha, url=result.url, post_id=result.post_id
        )
        log.info("publicado '%s' en %s: %s", pieza.id, destino, result.post_id)
