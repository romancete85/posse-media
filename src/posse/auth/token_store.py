"""Persistencia de tokens de LinkedIn. Fuera del repo, siempre.

Backends (elegidos por settings.token_store_backend):
  - SsmTokenStore   (prod/CI): AWS SSM Parameter Store, SecureString + KMS.
  - LocalTokenStore (dev):     archivo JSON fuera del repo (chmod 600).

Contrato comun (Protocol): load() -> bundle | None ; save(bundle) -> None.
El bundle guarda: access_token, refresh_token, expiraciones y el person_urn (sub).

SCAFFOLD: contrato y firmas; logica en Fase 1.
"""

from __future__ import annotations

from typing import Protocol


class TokenStore(Protocol):
    """Contrato de un backend de tokens."""

    def load(self) -> dict | None:
        """Devuelve el bundle de tokens, o None si no hay."""
        ...

    def save(self, bundle: dict) -> None:
        """Persiste el bundle de tokens."""
        ...


class SsmTokenStore:
    """Backend SSM Parameter Store (SecureString). prod/CI."""

    def load(self) -> dict | None:
        raise NotImplementedError("TODO(Fase 1): boto3 ssm.get_parameter(WithDecryption=True)")

    def save(self, bundle: dict) -> None:
        raise NotImplementedError("TODO(Fase 1): boto3 ssm.put_parameter(Type=SecureString, Overwrite=True)")


class LocalTokenStore:
    """Backend archivo JSON local (chmod 600). Solo dev."""

    def load(self) -> dict | None:
        raise NotImplementedError("TODO(Fase 1): leer LOCAL_TOKEN_FILE si existe")

    def save(self, bundle: dict) -> None:
        raise NotImplementedError("TODO(Fase 1): escribir LOCAL_TOKEN_FILE con permisos restrictivos")


def get_token_store() -> TokenStore:
    """Factory: devuelve el backend segun settings.token_store_backend."""
    raise NotImplementedError("TODO(Fase 1): elegir Ssm/Local por settings")
