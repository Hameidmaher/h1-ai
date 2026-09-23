"""
Rate Limiter + Retry + Cache
يمنع 429 من Groq API
"""
import asyncio
import hashlib
import time
from collections import OrderedDict
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Async rate limiter مع retry + exponential backoff"""

    def __init__(
        self,
        max_requests: int = 25,
        window_seconds: int = 60,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """ينتظر لحد ما يكون فيه slot متاح"""
        async with self._lock:
            now = time.time()
            # نشيل الطلبات القديمة
            self._timestamps = [
                t for t in self._timestamps
                if now - t < self.window_seconds
            ]
            # لو وصلنا الحد، ننتظر
            if len(self._timestamps) >= self.max_requests:
                wait = self.window_seconds - (now - self._timestamps[0])
                if wait > 0:
                    logger.info("rate_limit.wait", seconds=round(wait, 1))
                    await asyncio.sleep(wait)
                    now = time.time()
                    self._timestamps = [
                        t for t in self._timestamps
                        if now - t < self.window_seconds
                    ]
            self._timestamps.append(now)

    async def execute(
        self,
        fn: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """ينفذ دالة مع rate limit + retry"""
        last_error = None
        for attempt in range(self.max_retries + 1):
            await self.acquire()
            try:
                if asyncio.iscoroutinefunction(fn):
                    return await fn(*args, **kwargs)
                else:
                    return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # لو rate limit، ننتظر ونحاول تاني
                if "429" in error_str or "rate" in error_str or "limit" in error_str:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "rate_limit.retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=error_str[:100],
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # خطأ تاني، نرفعه
                    raise
        raise last_error or Exception("Max retries exceeded")


class ResponseCache:
    """Cache ذكي للردود المتكررة"""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    def _key(self, message: str, **kwargs) -> str:
        raw = f"{message}|{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def get(self, message: str, **kwargs) -> Optional[Any]:
        async with self._lock:
            key = self._key(message, **kwargs)
            if key not in self._cache:
                return None
            value, ts = self._cache[key]
            if time.time() - ts > self.ttl:
                del self._cache[key]
                return None
            # نحركها في الآخر (LRU)
            self._cache.move_to_end(key)
            return value

    async def set(self, message: str, value: Any, **kwargs):
        async with self._lock:
            key = self._key(message, **kwargs)
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
            # نشيل الأقدم لو تجاوزنا الحد
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def stats(self) -> dict:
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
        }


# Singletons
rate_limiter = RateLimiter()
response_cache = ResponseCache()
