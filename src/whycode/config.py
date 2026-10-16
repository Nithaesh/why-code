"""Centralized application configuration loaded from environment variables."""

from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for Phase 0, with safe defaults for non-secret values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr = Field(default=SecretStr(""), alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL")
    whycode_provider: str = Field(default="gemini", alias="WHYCODE_PROVIDER")
    whycode_cache_dir: Path = Field(default=Path(".whycode_cache"), alias="WHYCODE_CACHE_DIR")
    whycode_temperature: float = Field(default=0.0, ge=0.0, le=2.0, alias="WHYCODE_TEMPERATURE")

    def require_gemini_key(self) -> str:
        """Return the API key or fail with a clear setup instruction."""
        key = self.gemini_api_key.get_secret_value().strip()
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Add your key to the local .env file; "
                "never put it in source code or commit it to Git."
            )
        return key
