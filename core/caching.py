"""
Model caching utilities with Redis support for shared state across applications
"""

from pathlib import Path
import json
import pickle
import hashlib
import os
import diskcache


class ModelCache:
    """
    Manages caching of translation models and results.
    Supports in-memory, disk, and Redis-based caching for shared state.
    """
    
    def __init__(self, cache_dir=".cache", use_redis=None, redis_url=None):
        """
        Initialize cache with optional Redis support
        
        Args:
            cache_dir: Directory for disk cache
            use_redis: Enable Redis caching (auto-detects if None)
            redis_url: Redis connection URL (default: redis://localhost:6379/0)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache (fallback for models - too large for Redis)
        self.model_cache = {}
        
        # Disk cache for translations (persistent fallback)
        self.disk_cache = diskcache.Cache(str(self.cache_dir / 'translations'))
        
        # Redis setup
        self.redis_client = None
        self.use_redis = use_redis
        
        if use_redis is None:
            # Auto-detect Redis availability
            self.use_redis = self._detect_redis()
        
        if self.use_redis:
            self._init_redis(redis_url)
    
    def _detect_redis(self):
        """Auto-detect if Redis is available"""
        try:
            import redis
            # Check if REDIS_URL is set in environment
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, socket_connect_timeout=1)
            client.ping()
            return True
        except:
            return False
    
    def _init_redis(self, redis_url=None):
        """Initialize Redis connection"""
        try:
            import redis
            
            if redis_url is None:
                redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle binary data
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            self.redis_client.ping()
            print(f"✅ Redis cache connected: {redis_url}")
            
        except Exception as e:
            print(f"⚠️  Redis unavailable, using disk cache: {e}")
            self.redis_client = None
            self.use_redis = False
    
    def _make_key(self, prefix, *args):
        """Create a cache key"""
        key_parts = [str(arg) for arg in args]
        key_str = ":".join(key_parts)
        # Use hash for long keys
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        return f"{prefix}:{key_str}"
    
    def get_model(self, model_name):
        """Get cached model (models are memory-only, too large for Redis/disk)"""
        return self.model_cache.get(model_name)
    
    def set_model(self, model_name, model_data):
        """Cache a model (memory-only)"""
        self.model_cache[model_name] = model_data
    
    def clear_models(self):
        """Clear model cache"""
        self.model_cache.clear()
    
    def cache_translation(self, text, source_lang, target_lang, result, ttl=3600):
        """
        Cache a translation result with multi-tier caching
        
        Args:
            text: Original text
            source_lang: Source language
            target_lang: Target language
            result: Translation result dict
            ttl: Time to live in seconds (default: 1 hour)
        """
        cache_key = self._make_key("trans", source_lang, target_lang, hash(text))
        
        # Try Redis first (fastest for shared state)
        if self.redis_client:
            try:
                serialized = json.dumps(result)
                self.redis_client.setex(cache_key, ttl, serialized)
                return
            except Exception as e:
                print(f"Redis cache write failed: {e}")
        
        # Fallback to disk cache (persistent, slower but shared)
        try:
            self.disk_cache.set(cache_key, result, expire=ttl)
        except Exception as e:
            print(f"Disk cache write failed: {e}")
    
    def get_cached_translation(self, text, source_lang, target_lang):
        """Get cached translation with multi-tier lookup"""
        cache_key = self._make_key("trans", source_lang, target_lang, hash(text))
        
        # Try Redis first (fastest)
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis cache read failed: {e}")
        
        # Fallback to disk cache
        try:
            cached = self.disk_cache.get(cache_key)
            if cached:
                # Promote to Redis if available
                if self.redis_client:
                    try:
                        self.redis_client.setex(cache_key, 3600, json.dumps(cached))
                    except:
                        pass
                return cached
        except Exception as e:
            print(f"Disk cache read failed: {e}")
        
        return None
    
    def clear_translations(self):
        """Clear translation cache"""
        # Clear disk cache
        try:
            self.disk_cache.clear()
        except Exception as e:
            print(f"Disk cache clear failed: {e}")
        
        # Clear Redis cache
        if self.redis_client:
            try:
                pattern = self._make_key("trans", "*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis cache clear failed: {e}")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        stats = {
            'models_cached': len(self.model_cache),
            'cache_dir': str(self.cache_dir),
            'redis_enabled': self.use_redis,
            'redis_connected': self.redis_client is not None
        }
        
        # Disk cache stats
        try:
            stats['translations_cached_disk'] = len(self.disk_cache)
            stats['disk_cache_size'] = self.disk_cache.volume()
        except:
            stats['translations_cached_disk'] = 0
            stats['disk_cache_size'] = 0
        
        # Redis stats
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['redis_memory_used'] = info.get('used_memory_human', 'N/A')
                
                pattern = self._make_key("trans", "*")
                keys = self.redis_client.keys(pattern)
                stats['translations_cached_redis'] = len(keys)
            except:
                stats['translations_cached_redis'] = 0
        
        return stats


class SharedModelCache:
    """
    Singleton pattern for shared model cache across all applications.
    This ensures Streamlit, API, and Batch tools share the same cache.
    """
    _instance = None
    _cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._cache = ModelCache()
        return cls._instance
    
    @classmethod
    def get_cache(cls):
        """Get the shared cache instance"""
        if cls._cache is None:
            cls._cache = ModelCache()
        return cls._cache
    
    @classmethod
    def reset(cls):
        """Reset the cache (for testing)"""
        cls._cache = None
        cls._instance = None
