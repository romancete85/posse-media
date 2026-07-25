"""Publisher de Mastodon — API REST estándar (self-serve, gratis).

Endpoint:  POST https://<instancia>/api/v1/statuses
Media:     POST https://<instancia>/api/v2/media  (multipart + description = alt text)
Auth:      Authorization: Bearer <access_token>   (Preferences > Development > New application,
           scopes write:statuses + write:media)

Idempotencia: header `Idempotency-Key` = id de la pieza → reintentar no duplica el toot.
Límite: 500 chars por defecto (configurable por instancia, `mastodon_max_chars`).
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from pathlib import Path
from typing import Callable

import httpx

from posse.models import Asset, Pieza
from posse.platforms.base import PublishResult

log = logging.getLogger("posse.mastodon")

_TIMEOUT = httpx.Timeout(60.0)
_MEDIA_POLL_INTERVAL = 1.0
_MEDIA_POLL_MAX = 30


class MastodonError(RuntimeError):
    """Error de la API de Mastodon. Lleva código y cuerpo para diagnosticar."""

    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class MastodonConfigError(MastodonError):
    """Falta configurar la instancia o el token (mastodon_instance / mastodon_access_token)."""


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _status_text(pieza: Pieza) -> str:
    """Texto del toot = cuerpo + hashtags inline (Mastodon no necesita escapes)."""
    cuerpo, hashtags = pieza.contenido_para("mastodon")
    texto = cuerpo.rstrip()
    if hashtags:
        tags = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        texto = f"{texto}\n\n{tags}"
    return texto


class MastodonPublisher:
    """Implementa base.Publisher para Mastodon (perfil propio)."""

    name = "mastodon"

    def __init__(
        self,
        *,
        instance: str,
        access_token: str,
        max_chars: int = 500,
        client: httpx.Client | None = None,
        clock: Callable[[], dt.datetime] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if not instance or not access_token:
            raise MastodonConfigError(
                "falta mastodon_instance y/o mastodon_access_token en .env "
                "(Preferences > Development > New application, scopes write:statuses + write:media)"
            )
        self._base = instance.rstrip("/")
        self._access_token = access_token
        self._max_chars = max_chars
        self._client = client
        self._clock = clock or _utcnow
        self._sleep = sleep or time.sleep

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {"Authorization": f"Bearer {self._access_token}"}
        if extra:
            h.update(extra)
        return h

    def _upload_media(self, c: httpx.Client, asset: Asset) -> str:
        """Sube una imagen con su alt text. Devuelve el media id (espera si queda 'processing')."""
        data = Path(asset.path).read_bytes()
        files = {"file": (Path(asset.path).name, data)}
        form = {"description": asset.alt or ""}
        resp = c.post(f"{self._base}/api/v2/media", headers=self._headers(), files=files, data=form)
        self._raise_for_status(resp)
        media = resp.json()
        media_id = media["id"]

        # 202 = subida OK pero aún procesando; hay que esperar a que esté lista antes de postear.
        if resp.status_code == 202:
            for _ in range(_MEDIA_POLL_MAX):
                self._sleep(_MEDIA_POLL_INTERVAL)
                chk = c.get(f"{self._base}/api/v1/media/{media_id}", headers=self._headers())
                if chk.status_code == 200:
                    break
        log.info("media subida a Mastodon: %s (%s)", media_id, asset.path)
        return media_id

    def publish(self, pieza: Pieza) -> PublishResult:
        texto = _status_text(pieza)
        if len(texto) > self._max_chars:
            raise MastodonError(
                f"el texto ({len(texto)} chars) excede el límite de Mastodon ({self._max_chars}); "
                f"agregá una variante en la pieza: variantes.mastodon.cuerpo (probá `posse adapt {pieza.id} mastodon`)"
            )
        c = self._client or httpx.Client(timeout=_TIMEOUT)
        media_ids = [self._upload_media(c, a) for a in pieza.assets]

        body: dict = {"status": texto, "visibility": "public"}
        if media_ids:
            body["media_ids"] = media_ids
        resp = c.post(
            f"{self._base}/api/v1/statuses",
            headers=self._headers({"Idempotency-Key": pieza.id}),  # reintentar no duplica
            json=body,
        )
        self._raise_for_status(resp)
        out = resp.json()
        post_id, url = str(out["id"]), out["url"]
        log.info("toot creado en Mastodon: %s", url)
        return PublishResult(fecha=self._clock().isoformat(), url=url, post_id=post_id)

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code in (200, 202):
            return
        sc, body = resp.status_code, resp.text
        log.error("Mastodon respondió %s: %s", sc, body)
        if sc == 401:
            raise MastodonError("401: token inválido (revisá mastodon_access_token)", status_code=sc, body=body)
        if sc == 403:
            raise MastodonError("403: el token no tiene scope write:statuses/write:media", status_code=sc, body=body)
        if sc == 429:
            raise MastodonError("429: rate limit de la instancia", status_code=sc, body=body)
        raise MastodonError(f"error HTTP {sc}", status_code=sc, body=body)
