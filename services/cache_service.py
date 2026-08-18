import time
from threading import Lock

class CacheService:
    """Thread-safe in-memory cache with Time-To-Live (TTL) support."""
    _cache = {}
    _lock = Lock()

    @classmethod
    def get(cls, key):
        with cls._lock:
            entry = cls._cache.get(key)
            if not entry:
                return None
            val, expiry = entry
            if expiry is not None and time.time() > expiry:
                cls._cache.pop(key, None)
                return None
            return val

    @classmethod
    def set(cls, key, value, ttl_seconds=60):
        with cls._lock:
            expiry = time.time() + ttl_seconds if ttl_seconds else None
            cls._cache[key] = (value, expiry)

    @classmethod
    def delete(cls, key):
        with cls._lock:
            cls._cache.pop(key, None)

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._cache.clear()
