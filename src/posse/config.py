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
    # Contexto de grounding (perfil, proyectos, fuentes)
    context_dir: str = "context"
    context_max_chars: int = 6000  # tope: en 14b CPU, más contexto = prompt más lento

    # Generación con IA (upstream del gate; produce siempre drafts)
    # Backend de texto: "ollama" (homelab, gratis) | "claude" (API, con créditos)
    llm_backend: str = "ollama"
    # Ollama (homelab)
    ollama_host: str = "http://localhost:11434"  # ej. http://192.168.100.x:11434 (minipve)
    ollama_model: str = "llama3.1"               # uno de tus modelos instalados
    ollama_keep_alive: str = "30m"               # mantiene el modelo caliente (evita recarga ~24s tras idle)
    ollama_timeout: float = 600.0                # segundos; 14b en CPU con prompts largos tarda minutos
    # Claude (opción; solo si llm_backend=claude)
    anthropic_api_key: str = ""            # vacío -> el SDK usa el entorno/perfil
    claude_model: str = "claude-opus-4-8"
    # Imágenes (Google): Imagen genera, Gemini visión escribe el alt text (misma key)
    gemini_api_key: str = ""
    imagen_model: str = "imagen-4.0-generate-001"
    gemini_vision_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    """Devuelve las settings cargadas (cacheadas)."""
    return Settings()
