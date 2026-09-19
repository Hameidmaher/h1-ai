from __future__ import annotations
from langchain_core.language_models import BaseChatModel
from config_loader import prod_config
import structlog

logger = structlog.get_logger()


def create_llm(temperature: float = 0.3) -> BaseChatModel:
    provider = prod_config.llm_provider

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=prod_config.get("llm.ollama.model", "llama3.1:8b"),
            base_url=prod_config.get("llm.ollama.base_url", "http://localhost:11434"),
            temperature=temperature,
            num_ctx=prod_config.get("llm.ollama.num_ctx", 8192),
        )

    if provider == "groq":
        import os
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key or not api_key.startswith("gsk_"):
            logger.warning(
                "llm.groq_missing_key",
                fallback="ollama",
                has_key=bool(api_key),
            )
            # Fallback to Ollama (use qwen2.5:7b for better quality)
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=prod_config.get("llm.ollama.model", "qwen2.5:7b"),
                base_url=prod_config.get("llm.ollama.base_url", "http://localhost:11434"),
                temperature=temperature,
                num_ctx=8192,
            )
        
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=api_key,
                model=prod_config.get("llm.groq.model", "llama-3.3-70b-versatile"),
                temperature=temperature,
            )
        except Exception as e:
            logger.error("llm.groq_init_failed", error=str(e)[:200], fallback="ollama")
            # Fallback to Ollama (use qwen2.5:7b for better quality)
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=prod_config.get("llm.ollama.model", "qwen2.5:7b"),
                base_url=prod_config.get("llm.ollama.base_url", "http://localhost:11434"),
                temperature=temperature,
                num_ctx=8192,
            )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        import os
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=prod_config.get("llm.openai.model", "gpt-4o-mini"),
            temperature=temperature,
        )

    logger.warning("llm.unknown_provider", provider=provider, fallback="ollama")
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        temperature=temperature,
    )
