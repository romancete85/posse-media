"""Flujo OAuth 2.0 + OpenID Connect con LinkedIn.

- authorization-code con callback local (una sola vez): abre el browser, captura el `code`
  en http://localhost:<port>/callback, intercambia por access + refresh token.
- scopes: "openid profile w_member_social".
- person URN: se obtiene el `sub` desde /userinfo y se cachea (lo necesita el author del post).
- refresh: intercambia el refresh token por un access token nuevo (access ~60d, refresh ~365d).

SCAFFOLD: firmas y contrato; logica en Fase 1.
"""

from __future__ import annotations


def run_authorization_code_flow() -> dict:
    """Flujo interactivo de una vez. Devuelve el bundle de tokens (+ person URN) para persistir."""
    raise NotImplementedError(
        "TODO(Fase 1): armar authorize URL -> server local en callback -> intercambiar code -> "
        "/userinfo para el sub/URN"
    )


def refresh_access_token(refresh_token: str) -> dict:
    """Refresca el access token usando el refresh token. Devuelve el bundle actualizado."""
    raise NotImplementedError("TODO(Fase 1): POST al token endpoint con grant_type=refresh_token")
