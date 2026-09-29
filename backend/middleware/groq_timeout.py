"""يضيف timeout + retry لاستدعاءات Groq"""
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)
GROQ_TIMEOUT_SECONDS = 30
GROQ_MAX_RETRIES = 2


def with_groq_timeout(timeout: int = GROQ_TIMEOUT_SECONDS):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(GROQ_MAX_RETRIES + 1):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except Exception as e:
                    last_exc = e
                    logger.warning(f"Groq attempt {attempt+1} failed: {e}")
                    if attempt < GROQ_MAX_RETRIES:
                        await asyncio.sleep(2 ** attempt)
            raise last_exc
        return wrapper
    return decorator
