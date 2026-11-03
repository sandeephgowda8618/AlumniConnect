"""AlumniConnect Redis Client & Resilient In-Memory Cache Fallback
Implements Redis Design Specification §3 key naming conventions (ac:{env}:v1:...)
and provides automatic in-memory fallback when Redis is offline or running sandboxed.
"""

import time
import json
import logging
from typing import Any, Dict, Optional, List

from app.core.config import settings

logger = logging.getLogger("alumniconnect.redis")


class InMemoryCacheStore:
    """Thread-safe in-memory key-value store matching Redis TTL and Hash semantics."""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expires: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        if key in self._expires and time.time() > self._expires[key]:
            self.delete(key)
            return True
        return False

    def get(self, key: str) -> Optional[str]:
        if self._is_expired(key) or key not in self._data:
            return None
        val = self._data[key]
        return val if isinstance(val, str) else json.dumps(val)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        if ex:
            self._expires[key] = time.time() + ex
        elif key in self._expires:
            del self._expires[key]
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
            if k in self._expires:
                del self._expires[k]
        return count

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        current = self.hgetall(name)
        current.update({k: str(v) for k, v in mapping.items()})
        self._data[name] = current
        return len(mapping)

    def hgetall(self, name: str) -> Dict[str, str]:
        if self._is_expired(name) or name not in self._data:
            return {}
        val = self._data.get(name, {})
        return val if isinstance(val, dict) else {}

    def exists(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if not self._is_expired(k) and k in self._data:
                count += 1
        return count

    def keys(self, pattern: str = "*") -> List[str]:
        # Simple glob prefix pattern support
        prefix = pattern.replace("*", "")
        valid = []
        for k in list(self._data.keys()):
            if not self._is_expired(k) and k.startswith(prefix):
                valid.append(k)
        return valid

    def flushall(self):
        self._data.clear()
        self._expires.clear()


class RedisManager:
    """Manages Redis connection with graceful in-memory fallback."""
    def __init__(self):
        self._client = None
        self._is_connected = False
        self._fallback_store = InMemoryCacheStore()
        self._init_connection()

    def _init_connection(self):
        try:
            import redis
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0
            )
            client.ping()
            self._client = client
            self._is_connected = True
            logger.info("Connected successfully to Redis server.")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}). Using resilient in-memory cache store.")
            self._client = None
            self._is_connected = False

    @property
    def is_live_redis(self) -> bool:
        return self._is_connected and self._client is not None

    def build_key(self, feature: str, resource: str, identifier: Any, variant: Optional[str] = None) -> str:
        """Constructs standardized key: ac:{env}:v1:{feature}:{resource}:{identifier}[:{variant}]"""
        base = f"{settings.REDIS_KEY_PREFIX}{feature}:{resource}:{identifier}"
        return f"{base}:{variant}" if variant else base

    def get(self, key: str) -> Optional[str]:
        if self.is_live_redis:
            try:
                return self._client.get(key)
            except Exception:
                pass
        return self._fallback_store.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self.is_live_redis:
            try:
                return bool(self._client.set(key, value, ex=ex))
            except Exception:
                pass
        return self._fallback_store.set(key, value, ex=ex)

    def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        if self.is_live_redis:
            try:
                return self._client.delete(*keys)
            except Exception:
                pass
        return self._fallback_store.delete(*keys)

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        if self.is_live_redis:
            try:
                return self._client.hset(name, mapping=mapping)
            except Exception:
                pass
        return self._fallback_store.hset(name, mapping)

    def hgetall(self, name: str) -> Dict[str, str]:
        if self.is_live_redis:
            try:
                return self._client.hgetall(name)
            except Exception:
                pass
        return self._fallback_store.hgetall(name)

    def keys(self, pattern: str) -> List[str]:
        if self.is_live_redis:
            try:
                return self._client.keys(pattern)
            except Exception:
                pass
        return self._fallback_store.keys(pattern)

    def delete_by_pattern(self, pattern: str) -> int:
        matching = self.keys(pattern)
        if matching:
            return self.delete(*matching)
        return 0


redis_client = RedisManager()

