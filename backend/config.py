"""H1-AI — Configuration with strict validation."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Literal
import yaml
from pathlib import Path as _Path


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
    environment: Literal["development", "staging", "production", "test"] = "development"
    api_v1_prefix: str = "/v1"
    debug: bool = False

    # ═══ JWT (STRICT!) ═══
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    # ═══ Webhook Security ═══
    webhook_api_key: str = Field(
        default="change_me_webhook_key_min_16_chars",
        min_length=16,
        description="API key for webhook authentication",
    )

    # ═══ Paths ═══
    products_csv_path: str = "../data/products.csv"
    chroma_persist_dir: str = "./chroma_db"

    # ═══ Rate Limiting ═══
    rate_limit_chat: str = "30/minute"
    rate_limit_auth: str = "30/minute"

    # ═══ CORS ═══
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
    ]

    # ═══ LLM ═══
    ollama_model: str = "qwen2.5:0.5b"
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
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment in ("development", "test")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Webhook security (add to Settings class)


# ═══════════════════════════════════════════════════════════
# YAML Config Loader
# ═══════════════════════════════════════════════════════════
class YamlConfig:
    """يقرأ config.yaml من مجلد config/ في جذر المشروع."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        possible_paths = [
            _Path(__file__).parent.parent / "config" / "config.yaml",
            _Path("/app/config/config.yaml"),
            _Path("config/config.yaml"),
        ]
        config_path = None
        for p in possible_paths:
            if p.exists():
                config_path = p
                break

        if not config_path:
            raise FileNotFoundError("config/config.yaml not found")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)

        self.path = config_path

    @property
    def system_prompt(self) -> str:
        return self.data['ai']['system_prompt']

    @property
    def model(self) -> str:
        return self.data['ai']['model']

    @property
    def temperature(self) -> float:
        return self.data['ai']['temperature']

    @property
    def max_tokens(self) -> int:
        return self.data['ai']['max_tokens']

    @property
    def provider(self) -> str:
        return self.data['ai']['provider']

    @property
    def disclaimer_ar(self) -> str:
        return self.data['disclaimer']['ar']

    @property
    def disclaimer_en(self) -> str:
        return self.data['disclaimer']['en']

    @property
    def search_config(self) -> dict:
        return self.data['search']


yaml_config = YamlConfig()
