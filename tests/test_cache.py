"""Tests for High-Performance In-Memory Cache Engine."""
import time
import pytest
from src.cache import MemoryCache, cached, GLOBAL_CACHE


def test_memory_cache_set_get():
    c = MemoryCache(max_entries=10, default_ttl=2)
    c.set("k1", "v1")
    assert c.get("k1") == "v1"
    assert c.get("k2") is None


def test_memory_cache_expiration():
    c = MemoryCache(max_entries=10, default_ttl=1)
    c.set("temp", "val", ttl=1)
    assert c.get("temp") == "val"
    time.sleep(1.1)
    assert c.get("temp") is None


def test_memory_cache_stats():
    c = MemoryCache(max_entries=5, default_ttl=10)
    c.set("a", 1)
    c.get("a")  # hit
    c.get("b")  # miss
    s = c.stats()
    assert s["hits"] == 1
    assert s["misses"] == 1
    assert s["active_entries"] == 1


def test_cached_decorator():
    call_count = 0

    @cached(ttl_seconds=5, key_prefix="test_fn")
    def heavy_op(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    assert heavy_op(5) == 10
    assert call_count == 1
    # Second call should hit cache
    assert heavy_op(5) == 10
    assert call_count == 1
    # Different arg should compute
    assert heavy_op(6) == 12
    assert call_count == 2
