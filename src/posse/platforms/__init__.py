"""Plataformas de destino. Cada una implementa el Protocol de base.Publisher.

Agregar una red nueva = crear su modulo con un Publisher + sumar una rama en get_publisher().
El core (models, content_store, publisher) no cambia.

Cada plataforma se construye con SUS credenciales: LinkedIn usa el TokenBundle del token_store
(OAuth), Mastodon/X usan tokens de las Settings (.env).
"""

from __future__ import annotations

import httpx

from posse.config import Settings
from posse.platforms.base import Publisher


def get_publisher(
    name: str,
    *,
    settings: Settings,
    bundle=None,
    client: httpx.Client | None = None,
) -> Publisher:
    """Construye el Publisher del destino `name` con sus credenciales.

    `bundle` es el TokenBundle de LinkedIn (solo lo necesita LinkedIn); Mastodon/X leen de settings.
    """
    if name == "linkedin":
        from posse.platforms.linkedin import LinkedInPublisher

        if bundle is None:
            raise RuntimeError("LinkedIn necesita tokens; corré `posse auth` primero")
        return LinkedInPublisher(
            access_token=bundle.access_token,
            person_urn=bundle.person_urn,
            version=settings.linkedin_version,
            client=client,
        )
    if name == "mastodon":
        from posse.platforms.mastodon import MastodonPublisher

        return MastodonPublisher(
            instance=settings.mastodon_instance,
            access_token=settings.mastodon_access_token,
            max_chars=settings.mastodon_max_chars,
            client=client,
        )
    if name == "twitter":
        from posse.platforms.twitter import TwitterPublisher

        return TwitterPublisher(
            api_key=settings.twitter_api_key,
            api_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_secret=settings.twitter_access_secret,
            max_chars=settings.twitter_max_chars,
            client=client,
        )
    raise ValueError(f"plataforma no soportada: {name}")


def necesita_linkedin_bundle(destinos: list[str]) -> bool:
    """True si algún destino requiere el token de LinkedIn (para cargarlo solo cuando hace falta)."""
    return "linkedin" in destinos
