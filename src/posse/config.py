"""Settings tipados desde .env / entorno (pydantic-settings).

SCAFFOLD: contrato definido, sin logica funcional. Ver ROADMAP Fase 1.
"""

from __future__ import annotations

# TODO(Fase 1): from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings:  # TODO(Fase 1): heredar de BaseSettings
    """Config del pipeline. Carga de .env / variables de entorno.

    Campos objetivo (ver .env.example):
        linkedin_client_id / linkedin_client_secret / linkedin_redirect_uri
        linkedin_version           (YYYYMM)
        oauth_callback_port
        aws_region / ssm_token_param
        token_store_backend        ("ssm" | "local")
        local_token_file
        content_dir
    """

    # TODO(Fase 1): declarar los campos tipados + model_config(env_file=".env").


def get_settings() -> "Settings":
    """Devuelve las settings cargadas (cacheadas)."""
    raise NotImplementedError("TODO(Fase 1): cargar Settings desde .env/entorno")
