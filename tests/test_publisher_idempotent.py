"""Tests de idempotencia del publisher.

SCAFFOLD: se implementan en Fase 1. Test clave: una pieza ya 'published' (o con post_id) NO
se republica; una 'draft' no se publica (gate); solo 'approved' publica.
"""

import pytest


@pytest.mark.skip(reason="TODO(Fase 1): implementar junto con publisher")
def test_no_republica_si_ya_publicado():
    ...


@pytest.mark.skip(reason="TODO(Fase 1): gate — draft no publica")
def test_draft_no_publica():
    ...
