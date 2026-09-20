"""
LLM Factory — يدعم Ollama / Groq / OpenAI
يحمل .env تلقائياً عند الاستيراد
"""
from __future__ import annotations
import os
from pathlib import Path

# ─── تحميل .env تلقائياً ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    # مسار .env موجود في backend/
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=str(_env_path), override=False)
except ImportError:
    pass

from langchain_core.language_models import BaseChatModel
from config_loader import prod_config
import structlog

logger = structlog.get_logger()

# ─── الموديلات الافتراضية ──────────────────────────────────────
GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
OLLAMA_DEFAULT_MODEL = "qwen2.5:7b"
OLLAMA_DEFAULT_URL = "http://localhost:11434"


def _make_ollama(temperature: float, model: str | None = None):
    """إنشاء Ollama LLM."""
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model or prod_config.get("llm.ollama.model", OLLAMA_DEFAULT_MODEL),
        base_url=prod_config.get("llm.ollama.base_url", OLLAMA_DEFAULT_URL),
        temperature=temperature,
        num_ctx=prod_config.get("llm.ollama.num_ctx", 8192),
    )


def _make_groq(temperature: float):
    """إنشاء Groq LLM مع fallback آمن."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or not api_key.startswith("gsk_"):
        logger.warning("llm.groq_no_key",
                       has_key=bool(api_key),
                       fallback="ollama")
        return _make_ollama(temperature)

    try:
        from langchain_groq import ChatGroq
        model = prod_config.get("llm.groq.model", GROQ_DEFAULT_MODEL)
        logger.info("llm.groq_init", model=model, key_prefix=api_key[:8])
        return ChatGroq(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=prod_config.get("llm.groq.max_tokens", 1024),
        )
    except Exception as e:
        logger.error("llm.groq_failed", error=str(e)[:200], fallback="ollama")
        return _make_ollama(temperature)


def create_llm(temperature: float = 0.3) -> BaseChatModel:
    """
    إنشاء LLM حسب الإعدادات.
    """
    provider = (
        os.getenv("LLM_PROVIDER")
        or getattr(prod_config, "llm_provider", None)
        or "ollama"
    )

    if provider == "ollama":
        return _make_ollama(temperature)

    if provider == "groq":
        return _make_groq(temperature)

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=prod_config.get("llm.openai.model", "gpt-4o-mini"),
            temperature=temperature,
        )

    logger.warning("llm.unknown_provider", provider=provider, fallback="ollama")
    return _make_ollama(temperature)


# ─── Class-based wrapper (للتوافق) ──────────────────────────────
class LLMFactory:
    """Wrapper class — LLMFactory.create()"""

    @staticmethod
    def create(provider: str | None = None, temperature: float = 0.3):
        if provider == "groq":
            return _make_groq(temperature)
        if provider == "ollama":
            return _make_ollama(temperature)
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini",
                temperature=temperature,
            )
        return create_llm(temperature)
