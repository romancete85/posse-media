"""Persistencia de tokens de LinkedIn. Fuera del repo, siempre.

Backends (elegidos por settings.token_store_backend):
  - SsmTokenStore   (prod/CI): AWS SSM Parameter Store, SecureString + KMS.
  - LocalTokenStore (dev):     archivo JSON fuera del repo (chmod 600).

Contrato comun (Protocol): load() -> TokenBundle | None ; save(bundle) -> None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from posse.config import Settings, get_settings


class TokenBundle(BaseModel):
    """Tokens + metadata de expiracion + person URN. Lo que se persiste.

    refresh_token/refresh_expires_at son opcionales: LinkedIn NO emite refresh tokens por
    defecto (solo apps con 'programmatic refresh tokens'). Sin refresh, se re-corre `posse auth`.
    """

    access_token: str
    refresh_token: str | None = None
    access_expires_at: str  # ISO8601 UTC
    refresh_expires_at: str | None = None  # ISO8601 UTC (None si la app no emite refresh)
    person_urn: str  # urn:li:person:<sub>
    scope: str | None = None
    token_type: str = "Bearer"


class TokenStore(Protocol):
    """Contrato de un backend de tokens."""

    def load(self) -> TokenBundle | None:
        """Devuelve el bundle de tokens, o None si no hay."""
        ...

    def save(self, bundle: TokenBundle) -> None:
        """Persiste el bundle de tokens."""
        ...


class LocalTokenStore:
    """Backend archivo JSON local (chmod 600). Solo dev."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()

    def load(self) -> TokenBundle | None:
        if not self._path.exists():
            return None
        return TokenBundle.model_validate_json(self._path.read_text(encoding="utf-8"))

    def save(self, bundle: TokenBundle) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
        self._path.chmod(0o600)


class SsmTokenStore:
    """Backend SSM Parameter Store (SecureString + KMS). prod/CI. Cliente boto3 lazy."""

    def __init__(self, param_name: str, region: str, client=None) -> None:
        self._param = param_name
        self._region = region
        self._client = client

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("ssm", region_name=self._region)
        return self._client

    def load(self) -> TokenBundle | None:
        try:
            resp = self.client.get_parameter(Name=self._param, WithDecryption=True)
        except self.client.exceptions.ParameterNotFound:
            return None
        return TokenBundle.model_validate_json(resp["Parameter"]["Value"])

    def save(self, bundle: TokenBundle) -> None:
        self.client.put_parameter(
            Name=self._param,
            Value=bundle.model_dump_json(),
            Type="SecureString",
            Overwrite=True,
        )


def get_token_store(settings: Settings | None = None) -> TokenStore:
    """Factory: devuelve el backend segun settings.token_store_backend."""
    settings = settings or get_settings()
    if settings.token_store_backend == "ssm":
        return SsmTokenStore(settings.ssm_token_param, settings.aws_region)
    return LocalTokenStore(settings.local_token_file)
