"""High-Performance Thread-Safe In-Memory Cache with TTL and Telemetry."""
from __future__ import annotations

import time
import threading
import functools
import hashlib
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class MemoryCache:
    """Thread-safe in-memory key-value cache with TTL expiration and stats tracking."""

    def __init__(self, max_entries: int = 2000, default_ttl: int = 300) -> None:
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str, default: Any = None) -> Any:
        now = time.time()
        with self._lock:
            if key in self._store:
                val, expires_at = self._store[key]
                if now < expires_at:
                    self._hits += 1
                    return val
                else:
                    # Expired
                    del self._store[key]
                    self._evictions += 1
            self._misses += 1
            return default

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_val = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl_val
        with self._lock:
            # Enforce max entries via simple pruning if needed
            if len(self._store) >= self.max_entries and key not in self._store:
                # Remove oldest 10%
                keys_to_remove = list(self._store.keys())[: max(1, self.max_entries // 10)]
                for k in keys_to_remove:
                    self._store.pop(k, None)
                    self._evictions += 1

            self._store[key] = (value, expires_at)

    def invalidate(self, prefix: str = "") -> int:
        with self._lock:
            if not prefix:
                count = len(self._store)
                self._store.clear()
                return count
            keys_to_del = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_del:
                del self._store[k]
            return len(keys_to_del)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = round((self._hits / total_requests * 100), 2) if total_requests > 0 else 0.0
            return {
                "active_entries": len(self._store),
                "max_entries": self.max_entries,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate_pct": hit_rate,
            }


# Global cache instance
GLOBAL_CACHE = MemoryCache(max_entries=3000, default_ttl=300)


def _make_key(func_name: str, args: tuple, kwargs: dict) -> str:
    key_str = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:24]


def cached(ttl_seconds: int = 300, key_prefix: str = "") -> Callable:
    """Decorator to cache function results in memory with a given TTL."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            prefix = key_prefix or func.__name__
            cache_key = f"{prefix}:{_make_key(func.__name__, args, kwargs)}"
            cached_val = GLOBAL_CACHE.get(cache_key)
            if cached_val is not None:
                return cached_val
            result = func(*args, **kwargs)
            GLOBAL_CACHE.set(cache_key, result, ttl=ttl_seconds)
            return result
        return wrapper
    return decorator
