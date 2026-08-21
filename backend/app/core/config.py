"""Application settings, loaded from environment variables (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://chainpilot:chainpilot@localhost:5432/chainpilot"

    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    mcp_server_url: str = ""
    a2a_server_url: str = ""

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
