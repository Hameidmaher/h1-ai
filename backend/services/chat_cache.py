"""Chat response caching — reduces LLM calls."""
from __future__ import annotations
import hashlib
import time
import json
from typing import Optional, Dict, Any
from pathlib import Path
from threading import Lock

import structlog

logger = structlog.get_logger()


class ChatCache:
    """Thread-safe LRU cache with TTL for chat responses."""
    
    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 3600,
        cache_file: str = "logs/chat_cache.json",
    ):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        
        self._load_from_disk()
    
    def _make_key(self, message: str, user_role: str = "customer") -> str:
        """Normalize message and create cache key."""
        normalized = message.strip().lower()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        raw = f"{user_role}:{normalized}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    
    def get(self, message: str, user_role: str = "customer") -> Optional[dict]:
        """Get cached response if exists and not expired."""
        key = self._make_key(message, user_role)
        
        with self.lock:
            entry = self.cache.get(key)
            if not entry:
                self.misses += 1
                return None
            
            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl:
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            logger.info(
                "chat_cache.hit",
                message=message[:50],
                hits=self.hits,
                misses=self.misses,
                hit_rate=round(self.hits / (self.hits + self.misses), 3),
            )
            return entry["response"]
    
    def set(self, message: str, response: dict, user_role: str = "customer"):
        """Store response in cache."""
        key = self._make_key(message, user_role)
        
        with self.lock:
            # Evict oldest if full
            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]["timestamp"]
                )
                del self.cache[oldest_key]
            
            self.cache[key] = {
                "timestamp": time.time(),
                "message": message[:200],  # store for debugging
                "response": response,
            }
    
    def _load_from_disk(self):
        """Load cache from disk on startup."""
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Filter expired entries
            now = time.time()
            self.cache = {
                k: v for k, v in data.items()
                if now - v.get("timestamp", 0) < self.ttl
            }
            logger.info("chat_cache.loaded", size=len(self.cache))
        except Exception as e:
            logger.warning("chat_cache.load_failed", error=str(e)[:100])
    
    def save_to_disk(self):
        """Persist cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.lock:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("chat_cache.save_failed", error=str(e)[:100])
    
    def clear(self):
        """Clear all cached responses."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
        self.save_to_disk()
        logger.info("chat_cache.cleared")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total > 0 else 0.0,
                "ttl_seconds": self.ttl,
            }


# Singleton
chat_cache = ChatCache()
