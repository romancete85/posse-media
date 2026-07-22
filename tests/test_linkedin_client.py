"""Tests del cliente LinkedIn con HTTP mockeado (pytest-httpx). Nunca la API real.

SCAFFOLD: se implementan en Fase 1. Cubrir: headers de version presentes, body correcto,
parseo de post_id/url, y mapeo de 401/403/429 a errores claros.
"""

import pytest


@pytest.mark.skip(reason="TODO(Fase 1): implementar junto con platforms.linkedin")
def test_publish_envia_headers_de_version():
    ...
