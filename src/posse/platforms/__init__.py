"""Plataformas de destino. Cada una implementa el Protocol de base.Publisher.

Agregar una red nueva = crear su modulo con un Publisher + sumar una rama en get_publisher().
El core (models, content_store, publisher) no cambia.
"""

from __future__ import annotations

import httpx

from posse.platforms.base import Publisher
from posse.platforms.linkedin import LinkedInPublisher


def get_publisher(
    name: str,
    *,
    access_token: str,
    person_urn: str,
    version: str,
    client: httpx.Client | None = None,
) -> Publisher:
    """Construye el Publisher del destino `name` con el contexto de auth."""
    if name == "linkedin":
        return LinkedInPublisher(
            access_token=access_token, person_urn=person_urn, version=version, client=client
        )
    raise ValueError(f"plataforma no soportada: {name}")
