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
import urllib.parse
from pathlib import Path
from typing import Callable

import httpx

from posse.models import Asset, Pieza
from posse.platforms.base import PublishResult

log = logging.getLogger("posse.linkedin")

API_POSTS_URL = "https://api.linkedin.com/rest/posts"
API_IMAGES_URL = "https://api.linkedin.com/rest/images"
API_SOCIAL_URL = "https://api.linkedin.com/rest/socialActions"
RESTLI_VERSION = "2.0.0"
_TIMEOUT = httpx.Timeout(60.0)  # subir imagenes puede tardar


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


# Caracteres reservados del formato "Little Text" de la Posts API: hay que escaparlos con '\'
# o LinkedIn trunca/mangonea el texto (ej. un '(' sin escapar corta el post).
_LITTLE_TEXT_RESERVED = frozenset(r"\|{}@[]()<>#*_~")


def _escape_commentary(texto: str) -> str:
    return "".join("\\" + c if c in _LITTLE_TEXT_RESERVED else c for c in texto)


def _commentary(pieza: Pieza) -> str:
    """Texto del post = cuerpo (escapado) + hashtags al final (el '#' NO se escapa)."""
    texto = _escape_commentary(pieza.cuerpo.rstrip())
    if pieza.hashtags:
        tags = " ".join(h if h.startswith("#") else f"#{h}" for h in pieza.hashtags)
        texto = f"{texto}\n\n{tags}"  # hashtags sin escapar: el '#' debe quedar para que funcionen
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

    def _body(self, pieza: Pieza, media: list[dict]) -> dict:
        body = {
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
        if len(media) == 1:
            body["content"] = {"media": media[0]}
        elif len(media) > 1:
            body["content"] = {"multiImage": {"images": media}}
        return body

    def _upload_image(self, c: httpx.Client, asset: Asset) -> dict:
        """Sube una imagen (initialize + PUT) y devuelve el descriptor {id, altText}."""
        init = c.post(
            API_IMAGES_URL,
            params={"action": "initializeUpload"},
            headers=self._headers(),
            json={"initializeUploadRequest": {"owner": self._person_urn}},
        )
        self._raise_for_status(init)
        value = init.json()["value"]
        upload_url, image_urn = value["uploadUrl"], value["image"]

        data = Path(asset.path).read_bytes()
        up = c.put(
            upload_url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            content=data,
        )
        if up.status_code not in (200, 201):
            raise LinkedInError(
                f"upload de imagen '{asset.path}' fallo ({up.status_code})",
                status_code=up.status_code,
                body=up.text,
            )
        log.info("imagen subida: %s (%s)", image_urn, asset.path)
        return {"id": image_urn, "altText": asset.alt or ""}

    def publish(self, pieza: Pieza) -> PublishResult:
        c = self._client or httpx.Client(timeout=_TIMEOUT)
        media = [self._upload_image(c, a) for a in pieza.assets]
        resp = c.post(API_POSTS_URL, headers=self._headers(), json=self._body(pieza, media))
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

    def comment(self, post_urn: str, text: str) -> str:
        """Postea un comentario en un post existente (Comments API / socialActions).

        ⚠️ Requiere el producto **partner** `partnerApiSocialActions` de LinkedIn — NO es self-serve.
        Con la app self-serve (`w_member_social`) devuelve 403 ACCESS_DENIED. El comentario, en la
        práctica, se hace a mano en la UI. El código queda por si se obtiene acceso partner.
        """
        c = self._client or httpx.Client(timeout=_TIMEOUT)
        encoded = urllib.parse.quote(post_urn, safe="")
        body = {"actor": self._person_urn, "message": {"text": _escape_commentary(text)}}
        resp = c.post(f"{API_SOCIAL_URL}/{encoded}/comments", headers=self._headers(), json=body)
        self._raise_for_status(resp)
        urn = resp.headers.get("x-restli-id")
        if not urn:
            try:
                urn = resp.json().get("$URN") or resp.json().get("object")
            except Exception:  # noqa: BLE001
                urn = None
        log.info("comentario creado en %s: %s", post_urn, urn)
        return str(urn) if urn else "(ok, sin urn)"

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
