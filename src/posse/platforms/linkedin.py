"""Publisher de LinkedIn — Posts API (no UGC legacy).

Endpoint:  POST https://api.linkedin.com/rest/posts
Headers:   Authorization: Bearer <access_token>
           LinkedIn-Version: <YYYYMM>
           X-Restli-Protocol-Version: 2.0.0
Author:    urn:li:person:<sub>   (person URN del token store)
Scope:     w_member_social

Errores: 401 (token) / 403 (scope) / 429 (rate limit ~100/dia) -> excepciones claras.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Callable

import httpx

from posse.models import Pieza
from posse.platforms.base import PublishResult

log = logging.getLogger("posse.linkedin")

API_POSTS_URL = "https://api.linkedin.com/rest/posts"
RESTLI_VERSION = "2.0.0"
_TIMEOUT = httpx.Timeout(30.0)


class LinkedInError(RuntimeError):
    """Error de la Posts API. Lleva el codigo y el cuerpo para loguear/diagnosticar."""

    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class LinkedInAuthError(LinkedInError):
    """401 — token invalido o expirado."""


class LinkedInPermissionError(LinkedInError):
    """403 — scope/permiso insuficiente (falta w_member_social?)."""


class LinkedInRateLimitError(LinkedInError):
    """429 — rate limit (~100 llamadas/dia/miembro)."""


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _commentary(pieza: Pieza) -> str:
    """Texto del post = cuerpo (+ hashtags al final)."""
    texto = pieza.cuerpo.rstrip()
    if pieza.hashtags:
        tags = " ".join(h if h.startswith("#") else f"#{h}" for h in pieza.hashtags)
        texto = f"{texto}\n\n{tags}"
    # TODO(futuro): escaping "Little Text" de LinkedIn para caracteres reservados en commentary.
    return texto


class LinkedInPublisher:
    """Implementa base.Publisher para LinkedIn (perfil propio, texto)."""

    name = "linkedin"

    def __init__(
        self,
        *,
        access_token: str,
        person_urn: str,
        version: str,
        client: httpx.Client | None = None,
        clock: Callable[[], dt.datetime] | None = None,
    ) -> None:
        self._access_token = access_token
        self._person_urn = person_urn
        self._version = version
        self._client = client
        self._clock = clock or _utcnow

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "LinkedIn-Version": self._version,
            "X-Restli-Protocol-Version": RESTLI_VERSION,
            "Content-Type": "application/json",
        }

    def _body(self, pieza: Pieza) -> dict:
        return {
            "author": self._person_urn,
            "commentary": _commentary(pieza),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

    def publish(self, pieza: Pieza) -> PublishResult:
        c = self._client or httpx.Client(timeout=_TIMEOUT)
        resp = c.post(API_POSTS_URL, headers=self._headers(), json=self._body(pieza))
        self._raise_for_status(resp)

        urn = resp.headers.get("x-restli-id")
        if not urn:
            try:
                urn = resp.json().get("id")
            except Exception:  # noqa: BLE001 — cuerpo no-JSON
                urn = None
        if not urn:
            raise LinkedInError(
                "respuesta OK sin id de post (x-restli-id ausente)",
                status_code=resp.status_code,
                body=resp.text,
            )

        url = f"https://www.linkedin.com/feed/update/{urn}"
        log.info("post creado en LinkedIn: %s", urn)
        return PublishResult(fecha=self._clock().isoformat(), url=url, post_id=str(urn))

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        sc = resp.status_code
        if sc in (200, 201):
            return
        body = resp.text
        log.error("LinkedIn respondio %s: %s", sc, body)
        if sc == 401:
            raise LinkedInAuthError("401: token invalido o expirado", status_code=sc, body=body)
        if sc == 403:
            raise LinkedInPermissionError("403: scope/permiso insuficiente", status_code=sc, body=body)
        if sc == 429:
            raise LinkedInRateLimitError("429: rate limit (~100/dia/miembro)", status_code=sc, body=body)
        raise LinkedInError(f"error HTTP {sc}", status_code=sc, body=body)
