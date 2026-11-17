"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # backend/.env, wherever the command is run from. Real environment variables
    # (e.g. set by docker-compose) take precedence over the file.
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "dev"

    # --- database ---
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str = "localhost"
    db_port: int = 5432
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    # --- seeded admin / demo accounts (no defaults on purpose) ---
    admin_email: str | None = None
    admin_password: str | None = None
    demo_password: str | None = None

    # --- embeddings ---
    embed_backend: Literal["local", "litellm", "hash"] = "local"
    embed_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embed_dim: int = 384

    # --- llm ---
    llm_model: str = "groq/openai/gpt-oss-120b"
    llm_fallback_model: str | None = "groq/openai/gpt-oss-20b"  # used when the main model is rate limited
    llm_api_base: str | None = None
    llm_price_in: float = 0.0  # USD per 1M prompt tokens (for the cost dashboard)
    llm_price_out: float = 0.0  # USD per 1M completion tokens
    llm_max_tool_rounds: int = 4
    chat_rate_per_minute: int = 15

    # --- auth ---
    jwt_secret: str | None = None
    jwt_ttl_minutes: int = 12 * 60

    # --- storage ---
    storage_backend: Literal["local", "s3", "supabase"] = "local"
    upload_dir: str = "uploads"
    uploads_url_prefix: str = "/uploads"
    max_images_per_listing: int = 8
    max_image_bytes: int = 5 * 1024 * 1024
    image_web_max_px: int = 1600
    image_thumb_size: tuple[int, int] = (480, 320)

    # --- misc ---
    cors_origins: str = "http://localhost:5173"
    city_default: str = "Pune"

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.db_host}:{self.db_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
