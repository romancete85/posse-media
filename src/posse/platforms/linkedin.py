"""Publisher de LinkedIn — Posts API (no UGC legacy).

Endpoint:  POST https://api.linkedin.com/rest/posts
Headers:   Authorization: Bearer <access_token>
           LinkedIn-Version: <YYYYMM>
           X-Restli-Protocol-Version: 2.0.0
Author:    urn:li:person:<sub>   (person URN cacheado en el token store)
Scope:     w_member_social

Manejo de errores: mapear 401 (token) / 403 (scope) / 429 (rate limit ~100/dia) a errores claros;
loguear codigo + cuerpo. Sin retry silencioso.

Extensibilidad: upload_image() para adjuntar assets (Images API) queda para la fase de imagenes.
SCAFFOLD: contrato y firmas; logica en Fase 1.
"""

from __future__ import annotations

from posse.platforms.base import PublishResult

API_POSTS_URL = "https://api.linkedin.com/rest/posts"


class LinkedInPublisher:
    """Implementa base.Publisher para LinkedIn."""

    name = "linkedin"

    def publish(self, pieza: "object") -> PublishResult:
        """Publica el texto de la pieza en el perfil propio via Posts API."""
        raise NotImplementedError(
            "TODO(Fase 1): construir el body del post + headers de version -> POST /rest/posts -> "
            "parsear post_id/url -> PublishResult"
        )

    # def upload_image(self, path: str) -> str:  # TODO(futuro): Images API -> asset URN
    #     ...
