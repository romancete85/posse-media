"""Publisher de X/Twitter — API v2 (tier PAGO).

Endpoint:  POST https://api.twitter.com/2/tweets   (body {"text": ...})
Auth:      OAuth 1.0a user context (api key/secret + access token/secret), firmado HMAC-SHA1.

⚠️ La API de posteo de X es PAGA (tier Basic ~USD 100/mes). Sin credenciales, el publisher
lanza TwitterConfigError con un mensaje claro. El código queda listo para cuando actives el acceso.

Límite: 280 chars (free/basic). Si el cuerpo es más largo, agregá variantes.twitter.cuerpo.
Media: la subida de imágenes usa otro flujo (v1.1 media/upload) — no implementado todavía;
si la pieza trae assets, avisa. Para X, publicá texto (con link en variante) por ahora.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import logging
import secrets
import time
import urllib.parse
from typing import Callable

import httpx

from posse.models import Pieza
from posse.platforms.base import PublishResult

log = logging.getLogger("posse.twitter")

API_TWEETS_URL = "https://api.twitter.com/2/tweets"
_TIMEOUT = httpx.Timeout(30.0)


class TwitterError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class TwitterConfigError(TwitterError):
    """Faltan las 4 credenciales de X (requiere API paga)."""


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _tweet_text(pieza: Pieza) -> str:
    cuerpo, hashtags = pieza.contenido_para("twitter")
    texto = cuerpo.rstrip()
    if hashtags:
        tags = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        texto = f"{texto}\n\n{tags}"
    return texto


def _oauth1_header(
    method: str,
    url: str,
    *,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
    nonce: str,
    timestamp: str,
) -> str:
    """Firma OAuth 1.0a HMAC-SHA1 y devuelve el header Authorization.

    Nota: para POST /2/tweets el body es JSON (no form-encoded), así que NO entra en la firma;
    solo los oauth_* params, que es correcto para OAuth1 con cuerpos no-form.
    """
    oauth = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp,
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    # Base string: METHOD&url&sorted-encoded-params
    param_str = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(oauth.items())
    )
    base = "&".join(
        urllib.parse.quote(x, safe="") for x in (method.upper(), url, param_str)
    )
    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
    digest = hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()
    oauth["oauth_signature"] = base64.b64encode(digest).decode()
    return "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth.items())
    )


class TwitterPublisher:
    """Implementa base.Publisher para X/Twitter (texto; requiere API paga)."""

    name = "twitter"

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        max_chars: int = 280,
        client: httpx.Client | None = None,
        clock: Callable[[], dt.datetime] | None = None,
        nonce_fn: Callable[[], str] | None = None,
    ) -> None:
        if not all((api_key, api_secret, access_token, access_secret)):
            raise TwitterConfigError(
                "faltan credenciales de X (twitter_api_key/secret/access_token/access_secret). "
                "La API de posteo de X es paga (tier Basic ~USD 100/mes)."
            )
        self._api_key = api_key
        self._api_secret = api_secret
        self._access_token = access_token
        self._access_secret = access_secret
        self._max_chars = max_chars
        self._client = client
        self._clock = clock or _utcnow
        self._nonce_fn = nonce_fn or (lambda: secrets.token_hex(16))

    def publish(self, pieza: Pieza) -> PublishResult:
        if pieza.assets:
            raise TwitterError(
                "subir imágenes a X no está implementado todavía (usa el flujo v1.1 media/upload); "
                "publicá texto para X o dejá la imagen solo en LinkedIn/Mastodon"
            )
        texto = _tweet_text(pieza)
        if len(texto) > self._max_chars:
            raise TwitterError(
                f"el texto ({len(texto)} chars) excede el límite de X ({self._max_chars}); "
                f"agregá variantes.twitter.cuerpo (probá `posse adapt {pieza.id} twitter`)"
            )
        auth = _oauth1_header(
            "POST",
            API_TWEETS_URL,
            api_key=self._api_key,
            api_secret=self._api_secret,
            access_token=self._access_token,
            access_secret=self._access_secret,
            nonce=self._nonce_fn(),
            timestamp=str(int(time.time())),
        )
        c = self._client or httpx.Client(timeout=_TIMEOUT)
        resp = c.post(
            API_TWEETS_URL,
            headers={"Authorization": auth, "Content-Type": "application/json"},
            json={"text": texto},
        )
        self._raise_for_status(resp)
        data = resp.json()["data"]
        tweet_id = str(data["id"])
        url = f"https://twitter.com/i/web/status/{tweet_id}"
        log.info("tweet creado: %s", url)
        return PublishResult(fecha=self._clock().isoformat(), url=url, post_id=tweet_id)

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code in (200, 201):
            return
        sc, body = resp.status_code, resp.text
        log.error("X respondió %s: %s", sc, body)
        if sc == 401:
            raise TwitterError("401: credenciales OAuth inválidas", status_code=sc, body=body)
        if sc == 403:
            raise TwitterError("403: la app no tiene permiso de escritura o el tier no lo permite", status_code=sc, body=body)
        if sc == 429:
            raise TwitterError("429: rate limit de X", status_code=sc, body=body)
        raise TwitterError(f"error HTTP {sc}", status_code=sc, body=body)
