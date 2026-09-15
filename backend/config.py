"""H1-AI — Configuration with strict validation."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ═══ App ═══
    app_name: str = "H1-AI"
    app_tagline: str = "Assistant Pharmacy"
    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    api_v1_prefix: str = "/v1"
    debug: bool = False

    # ═══ JWT (STRICT!) ═══
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    # ═══ Paths ═══
    products_csv_path: str = "../data/products.csv"
    chroma_persist_dir: str = "./chroma_db"

    # ═══ Rate Limiting ═══
    rate_limit_chat: str = "10/minute"
    rate_limit_auth: str = "5/minute"

    # ═══ CORS ═══
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
    ]

    # ═══ LLM ═══
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        FORBIDDEN = {
            "CHANGE_ME_IN_PRODUCTION",
            "CHANGE_ME_use_openssl_rand_hex_32",
            "dev_only_change_in_production",
            "secret", "password", "test",
        }
        if v in FORBIDDEN:
            raise ValueError(
                "JWT_SECRET_KEY must be changed from default. "
                "Generate with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"

    @property
    def is_development(self) -> bool:
        return self.environment in ("dev", "test")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
