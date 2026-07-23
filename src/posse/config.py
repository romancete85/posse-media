"""Settings tipados desde .env / entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config del pipeline. Ver .env.example."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LinkedIn app
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8765/callback"
    linkedin_version: str = "202606"  # YYYYMM — mantener actual (LinkedIn rota ~12 meses)

    # OAuth local (flujo de una vez)
    oauth_callback_port: int = 8765

    # AWS / token store
    aws_region: str = "us-east-1"
    ssm_token_param: str = "/posse-pipeline/linkedin/tokens"
    token_store_backend: str = "local"  # "ssm" (prod/CI) | "local" (dev)
    local_token_file: str = "~/.config/posse-pipeline/tokens.json"

    # Contenido
    content_dir: str = "content"

    # Generación con IA (upstream del gate; produce siempre drafts)
    anthropic_api_key: str = ""            # Claude (texto + alt text). Vacío -> SDK usa el entorno.
    claude_model: str = "claude-opus-4-8"  # modelo de generación/repurposing
    gemini_api_key: str = ""               # Google Imagen (generación de imágenes)
    imagen_model: str = "imagen-4.0-generate-001"


@lru_cache
def get_settings() -> Settings:
    """Devuelve las settings cargadas (cacheadas)."""
    return Settings()
