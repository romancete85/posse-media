"""Flujo OAuth 2.0 + OpenID Connect con LinkedIn.

- authorization-code con callback local (una sola vez): abre el browser, captura el `code`
  en http://localhost:<port>/callback, intercambia por access + refresh token.
- scopes: "openid profile w_member_social".
- person URN: se obtiene el `sub` desde /userinfo (lo necesita el author del post).
- refresh: intercambia el refresh token por un access token nuevo.

Funciones puras (build/exchange/refresh/userinfo/bundle) testeables con httpx mockeado.
La orquestacion interactiva (run_authorization_code_flow) se valida a mano.
"""

from __future__ import annotations

import datetime as dt
import secrets
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

from posse.auth.token_store import TokenBundle
from posse.config import Settings, get_settings

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile w_member_social"

_TIMEOUT = httpx.Timeout(30.0)


# --- Funciones puras (testeables) ---------------------------------------------------------------


def build_authorize_url(client_id: str, redirect_uri: str, state: str, scopes: str = SCOPES) -> str:
    """Arma la URL de autorizacion (donde el usuario consiente)."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scopes,
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    code: str,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    client: httpx.Client | None = None,
) -> dict:
    """Intercambia el authorization code por tokens. Devuelve el payload crudo de LinkedIn."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    c = client or httpx.Client(timeout=_TIMEOUT)
    resp = c.post(TOKEN_URL, data=data)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    refresh_token: str,
    *,
    client_id: str,
    client_secret: str,
    client: httpx.Client | None = None,
) -> dict:
    """Refresca el access token con el refresh token. Devuelve el payload crudo."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    c = client or httpx.Client(timeout=_TIMEOUT)
    resp = c.post(TOKEN_URL, data=data)
    resp.raise_for_status()
    return resp.json()


def fetch_person_urn(access_token: str, client: httpx.Client | None = None) -> str:
    """Obtiene el `sub` desde /userinfo y lo devuelve como urn:li:person:<sub>."""
    c = client or httpx.Client(timeout=_TIMEOUT)
    resp = c.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    resp.raise_for_status()
    return f"urn:li:person:{resp.json()['sub']}"


def bundle_from_token_response(
    payload: dict,
    *,
    person_urn: str,
    refresh_token_fallback: str | None = None,
    now: dt.datetime | None = None,
) -> TokenBundle:
    """Convierte el payload de LinkedIn en un TokenBundle con expiraciones absolutas."""
    now = now or dt.datetime.now(dt.timezone.utc)
    access_expires = now + dt.timedelta(seconds=int(payload["expires_in"]))
    refresh_expires = now + dt.timedelta(seconds=int(payload.get("refresh_token_expires_in", 0)))
    refresh_token = payload.get("refresh_token") or refresh_token_fallback
    if not refresh_token:
        raise ValueError("no hay refresh_token en la respuesta ni fallback")
    return TokenBundle(
        access_token=payload["access_token"],
        refresh_token=refresh_token,
        access_expires_at=access_expires.isoformat(),
        refresh_expires_at=refresh_expires.isoformat(),
        person_urn=person_urn,
        scope=payload.get("scope"),
        token_type=payload.get("token_type", "Bearer"),
    )


# --- Callback local (flujo interactivo de una vez) ----------------------------------------------


class _CallbackHandler(BaseHTTPRequestHandler):
    code: str | None = None
    error: str | None = None
    expected_state: str | None = None

    def do_GET(self) -> None:  # noqa: N802 (nombre impuesto por BaseHTTPRequestHandler)
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        qs = urllib.parse.parse_qs(parsed.query)
        cls = type(self)
        if qs.get("state", [None])[0] != cls.expected_state:
            cls.error = "state mismatch (posible CSRF)"
        else:
            cls.error = qs.get("error", [None])[0]
            cls.code = qs.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<h2>posse-pipeline: autorizacion recibida. Ya podes cerrar esta pestania.</h2>")

    def log_message(self, *args) -> None:  # silenciar logs del server
        pass


def _wait_for_code(port: int, expected_state: str) -> str:
    """Levanta un server de un solo request en localhost y devuelve el `code` del callback."""
    _CallbackHandler.code = None
    _CallbackHandler.error = None
    _CallbackHandler.expected_state = expected_state
    server = HTTPServer(("localhost", port), _CallbackHandler)
    try:
        server.handle_request()  # bloquea hasta un request
    finally:
        server.server_close()
    if _CallbackHandler.error:
        raise RuntimeError(f"OAuth callback error: {_CallbackHandler.error}")
    if not _CallbackHandler.code:
        raise RuntimeError("no se recibio 'code' en el callback")
    return _CallbackHandler.code


def run_authorization_code_flow(settings: Settings | None = None) -> TokenBundle:
    """Flujo interactivo de una vez: browser -> callback local -> tokens (+ person URN)."""
    settings = settings or get_settings()
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise RuntimeError("faltan LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET en .env")
    state = secrets.token_urlsafe(16)
    url = build_authorize_url(settings.linkedin_client_id, settings.linkedin_redirect_uri, state)
    print("Abriendo el navegador para autorizar. Si no abre, pega esta URL:\n", url)
    webbrowser.open(url)
    code = _wait_for_code(settings.oauth_callback_port, state)
    payload = exchange_code_for_tokens(
        code,
        client_id=settings.linkedin_client_id,
        client_secret=settings.linkedin_client_secret,
        redirect_uri=settings.linkedin_redirect_uri,
    )
    person_urn = fetch_person_urn(payload["access_token"])
    return bundle_from_token_response(payload, person_urn=person_urn)


def refresh(bundle: TokenBundle, settings: Settings | None = None) -> TokenBundle:
    """Refresca el access token de un bundle existente y devuelve el bundle actualizado."""
    settings = settings or get_settings()
    payload = refresh_access_token(
        bundle.refresh_token,
        client_id=settings.linkedin_client_id,
        client_secret=settings.linkedin_client_secret,
    )
    return bundle_from_token_response(
        payload, person_urn=bundle.person_urn, refresh_token_fallback=bundle.refresh_token
    )
