"""يقرأ config.production.yaml ويحوّله إلى إعدادات."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Optional
import yaml


class ProductionConfig:
    _instance: Optional["ProductionConfig"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "../config.production.yaml"):
        if getattr(self, "_initialized", False):
            return
        self.config_path = Path(config_path)
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        else:
            self.data = {}
        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        val: Any = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    @property
    def app_name(self) -> str:
        return os.getenv("APP_NAME") or self.get("app.name", "H1-AI")

    @property
    def whatsapp_phone(self) -> str:
        return os.getenv("WHATSAPP_PHONE") or self.get("whatsapp.phone", "")

    @property
    def whatsapp_mode(self) -> str:
        return os.getenv("WHATSAPP_MODE") or self.get("whatsapp.mode", "link")

    @property
    def llm_provider(self) -> str:
        return os.getenv("LLM_PROVIDER") or self.get("llm.provider", "ollama")

    @property
    def database_type(self) -> str:
        return os.getenv("DATABASE_TYPE") or self.get("database.type", "sqlite")

    @property
    def jwt_secret_key(self) -> str:
        return (os.getenv("JWT_SECRET_KEY")
                or self.get("security.jwt_secret_key", "")
                or "CHANGE_ME_IN_PRODUCTION")

    @property
    def is_production(self) -> bool:
        env = os.getenv("ENVIRONMENT", "development")
        return env in ("production", "prod")  # قبول prod للتوافق


prod_config = ProductionConfig()
