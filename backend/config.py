from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "H1-AI"
    app_tagline: str = "Assistant Pharmacy"
    environment: str = "dev"
    api_v1_prefix: str = "/v1"
    debug: bool = True

    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    jwt_refresh_token_expire_days: int = 30

    products_csv_path: str = "../data/products.csv"
    chroma_persist_dir: str = "./chroma_db"

    rate_limit_chat: str = "10/minute"
    rate_limit_auth: str = "5/minute"

    cors_origins: list[str] = ["*"]

    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
