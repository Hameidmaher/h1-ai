"""التحقق من صحة الإعدادات."""
from __future__ import annotations
from config_loader import prod_config


class ConfigError(Exception):
    pass


def validate_production_config() -> list[str]:
    warnings = []
    is_prod = prod_config.is_production

    jwt_key = prod_config.jwt_secret_key
    if not jwt_key or jwt_key in ("CHANGE_ME_IN_PRODUCTION", ""):
        if is_prod:
            raise ConfigError("JWT_SECRET_KEY must be set in production")
        warnings.append("JWT_SECRET_KEY uses default value")

    if len(jwt_key) < 32:
        if is_prod:
            raise ConfigError("JWT_SECRET_KEY must be at least 32 chars")
        warnings.append("JWT_SECRET_KEY is short")

    cors = prod_config.get("backend.cors_origins", [])
    if is_prod and "*" in cors:
        raise ConfigError("CORS wildcard not allowed in production")

    wa_phone = prod_config.whatsapp_phone
    if not wa_phone:
        warnings.append("WhatsApp phone not configured")
    elif not wa_phone.startswith("+"):
        warnings.append("WhatsApp phone should start with +")

    provider = prod_config.llm_provider
    if provider not in ("ollama", "groq", "openai", "together"):
        warnings.append(f"Unknown LLM provider: {provider}")

    return warnings


def validate_and_report() -> bool:
    try:
        warnings = validate_production_config()
        if warnings:
            print()
            print("⚠️  Config Warnings:")
            for w in warnings:
                print(f"   • {w}")
            print()
        return True
    except ConfigError as e:
        print()
        print(f"❌ Config Error: {e}")
        print()
        return False
