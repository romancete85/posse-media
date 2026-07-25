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
from posse.platforms import get_publisher, necesita_linkedin_bundle

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
        if not bundle.refresh_token:
            log.warning(
                "access token por expirar (%s) y la app no emite refresh tokens; "
                "corre `posse auth` de nuevo si el publish falla",
                bundle.access_expires_at,
            )
            return bundle
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
    destinos_filtro: list[str] | None = None,
) -> None:
    """Publica una pieza approved en sus destinos, idempotente.

    `destinos_filtro`: si se pasa, solo publica en esos destinos (ej. `--destino mastodon`).
    El token de LinkedIn se carga solo si algún destino pendiente lo necesita.
    """
    settings = settings or get_settings()
    store = store or get_token_store(settings)
    clock = clock or _utcnow

    pieza = content_store.load(path)
    if pieza.estado not in (Estado.APPROVED, Estado.PUBLISHED):
        raise GateError(
            f"la pieza '{pieza.id}' esta en '{pieza.estado.value}'; solo se publica 'approved'"
        )

    pendientes = [d for d in pieza.destinos if not pieza.esta_publicado_en(d)]
    if destinos_filtro is not None:
        pendientes = [d for d in pendientes if d in destinos_filtro]
    if not pendientes:
        log.info("pieza '%s': nada para publicar (destinos ya publicados o filtrados)", pieza.id)
        return

    bundle = None
    if necesita_linkedin_bundle(pendientes):
        bundle = store.load()
        if bundle is None:
            raise RuntimeError("no hay tokens de LinkedIn guardados; corre `posse auth` primero")
        bundle = _ensure_fresh(bundle, settings, store, clock)

    for destino in pendientes:
        pub = get_publisher(destino, settings=settings, bundle=bundle, client=client)
        result = pub.publish(pieza)
        content_store.marcar_publicado(
            path, destino, fecha=result.fecha, url=result.url, post_id=result.post_id
        )
        log.info("publicado '%s' en %s: %s", pieza.id, destino, result.post_id)


def comment(
    path: str | Path,
    text: str,
    *,
    settings: Settings | None = None,
    store: TokenStore | None = None,
    client=None,
    clock: Callable[[], dt.datetime] | None = None,
) -> str:
    """Postea un comentario en una pieza YA publicada en LinkedIn (ej. el link interactivo)."""
    settings = settings or get_settings()
    store = store or get_token_store(settings)
    clock = clock or _utcnow

    pieza = content_store.load(path)
    destino = pieza.publicado.get("linkedin")
    if not destino or not destino.post_id:
        raise RuntimeError(f"la pieza '{pieza.id}' no tiene post_id de LinkedIn (¿está publicada?)")

    bundle = store.load()
    if bundle is None:
        raise RuntimeError("no hay tokens guardados; corre `posse auth` primero")
    bundle = _ensure_fresh(bundle, settings, store, clock)

    from posse.platforms.linkedin import LinkedInPublisher

    pub = LinkedInPublisher(
        access_token=bundle.access_token,
        person_urn=bundle.person_urn,
        version=settings.linkedin_version,
        client=client,
    )
    urn = pub.comment(destino.post_id, text)
    log.info("comentario en '%s': %s", pieza.id, urn)
    return urn


def publish_approved(
    *,
    settings: Settings | None = None,
    store: TokenStore | None = None,
    client=None,
    clock: Callable[[], dt.datetime] | None = None,
) -> list[str]:
    """Publica todas las piezas 'approved' del content_dir. Devuelve los ids publicados.

    Es lo que corre el workflow cuando se pone el label 'approved'. Las 'draft' se saltan;
    las ya 'published' no se tocan (idempotencia).
    """
    settings = settings or get_settings()
    ids: list[str] = []
    for path in sorted(Path(settings.content_dir).glob("*.yaml")):
        if content_store.load(path).estado is Estado.APPROVED:
            publish(path, settings=settings, store=store, client=client, clock=clock)
            ids.append(content_store.load(path).id)
    return ids


def publish_due(
    *,
    settings: Settings | None = None,
    store: TokenStore | None = None,
    client=None,
    clock: Callable[[], dt.datetime] | None = None,
    today: dt.date | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Publica las piezas 'approved' cuya fecha `programado` ya llegó (auto-publish).

    Es lo que corre el cron / n8n a diario. Idempotente: las ya publicadas se saltan;
    las sin `programado` o con fecha futura no se tocan. `dry_run` solo lista, no publica.
    La fecha se compara contra `today` (default: hoy en UTC; el runner define la TZ del cron).
    """
    settings = settings or get_settings()
    clock = clock or _utcnow
    hoy = today or clock().date()

    ids: list[str] = []
    for path in sorted(Path(settings.content_dir).glob("*.yaml")):
        pieza = content_store.load(path)
        if pieza.estado is not Estado.APPROVED or not pieza.esta_programada_para(hoy):
            continue
        if all(pieza.esta_publicado_en(d) for d in pieza.destinos):
            continue  # nada pendiente
        if dry_run:
            log.info("[dry-run] publicaría '%s' (programado %s)", pieza.id, pieza.programado)
            ids.append(pieza.id)
            continue
        publish(path, settings=settings, store=store, client=client, clock=clock)
        ids.append(pieza.id)
    if not ids:
        log.info("publish-due: nada para publicar hoy (%s)", hoy)
    return ids
