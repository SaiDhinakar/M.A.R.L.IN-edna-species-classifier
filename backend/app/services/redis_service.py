"""
Redis caching service for model caching and inference results.
"""

import json
import pickle
from typing import Any, Optional
import redis
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class RedisService:
    """Service for interacting with Redis cache."""
    
    def __init__(self):
        self.client = redis.from_url(
            settings.redis_url,
            decode_responses=False  # We'll handle encoding/decoding
        )
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection."""
        try:
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set a value in cache."""
        try:
            serialized = pickle.dumps(value)
            result = self.client.set(
                key,
                serialized,
                ex=expire or settings.redis_cache_expire
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(
        self,
        key: str
    ) -> Optional[Any]:
        """Get a value from cache."""
        try:
            data = self.client.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set_json(
        self,
        key: str,
        value: dict,
        expire: Optional[int] = None
    ) -> bool:
        """Set a JSON value in cache."""
        try:
            serialized = json.dumps(value)
            result = self.client.set(
                key,
                serialized,
                ex=expire or settings.redis_cache_expire
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting JSON cache key {key}: {e}")
            return False
    
    def get_json(
        self,
        key: str
    ) -> Optional[dict]:
        """Get a JSON value from cache."""
        try:
            data = self.client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting JSON cache key {key}: {e}")
            return None
    
    def delete(
        self,
        key: str
    ) -> bool:
        """Delete a key from cache."""
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(
        self,
        key: str
    ) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def clear_pattern(
        self,
        pattern: str
    ) -> int:
        """Clear all keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0
    
    def increment(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """Increment a counter."""
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0
    
    def get_ttl(
        self,
        key: str
    ) -> int:
        """Get time to live for a key in seconds."""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            return self.client.ping()
        except Exception:
            return False


# Global Redis service instance
redis_service = RedisService()
