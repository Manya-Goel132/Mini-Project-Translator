"""Unit tests for caching module"""

import pytest
import tempfile
import shutil
from pathlib import Path
from core.caching import ModelCache, SharedModelCache


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory"""
    path = tempfile.mkdtemp()
    yield path
    # Cleanup
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def cache(temp_cache_dir):
    """Create cache instance with temp directory (no Redis)"""
    return ModelCache(cache_dir=temp_cache_dir, use_redis=False)


class TestModelCache:
    """Tests for ModelCache"""
    
    def test_init_creates_directory(self, temp_cache_dir):
        cache = ModelCache(cache_dir=temp_cache_dir, use_redis=False)
        assert Path(temp_cache_dir).exists()
    
    def test_model_cache_set_get(self, cache):
        model_data = ("tokenizer", "model")
        cache.set_model("test-model", model_data)
        
        result = cache.get_model("test-model")
        assert result == model_data
    
    def test_model_cache_miss(self, cache):
        result = cache.get_model("nonexistent-model")
        assert result is None
    
    def test_clear_models(self, cache):
        cache.set_model("test-model", ("tokenizer", "model"))
        cache.clear_models()
        
        result = cache.get_model("test-model")
        assert result is None
    
    def test_translation_cache_set_get(self, cache):
        result = {
            "translation": "Hola mundo",
            "method": "Test",
            "confidence": 0.95
        }
        cache.cache_translation("Hello world", "en", "es", result)
        
        cached = cache.get_cached_translation("Hello world", "en", "es")
        assert cached is not None
        assert cached["translation"] == "Hola mundo"
    
    def test_translation_cache_miss(self, cache):
        cached = cache.get_cached_translation("Not cached", "en", "es")
        assert cached is None
    
    def test_translation_cache_different_languages(self, cache):
        result = {
            "translation": "Hola",
            "method": "Test",
            "confidence": 0.95
        }
        cache.cache_translation("Hello", "en", "es", result)
        
        # Same text, different target language should miss
        cached = cache.get_cached_translation("Hello", "en", "fr")
        assert cached is None
    
    def test_clear_translations(self, cache):
        result = {"translation": "Test", "method": "Test", "confidence": 0.9}
        cache.cache_translation("Test", "en", "es", result)
        
        cache.clear_translations()
        
        cached = cache.get_cached_translation("Test", "en", "es")
        assert cached is None
    
    def test_get_cache_stats(self, cache):
        cache.set_model("test-model", ("tokenizer", "model"))
        
        stats = cache.get_cache_stats()
        assert stats is not None
        assert "models_cached" in stats
        assert stats["models_cached"] == 1
        assert "redis_enabled" in stats
        assert stats["redis_enabled"] is False
    
    def test_make_key(self, cache):
        key = cache._make_key("trans", "en", "es", "hello")
        assert key.startswith("trans:")
        assert "en" in key
    
    def test_make_key_long_text(self, cache):
        """Long keys should be hashed"""
        long_text = "a" * 500
        key = cache._make_key("trans", "en", "es", long_text)
        assert len(key) < 250  # Should be hashed


class TestSharedModelCache:
    """Tests for SharedModelCache singleton"""
    
    def test_singleton(self):
        # Reset first
        SharedModelCache.reset()
        
        cache1 = SharedModelCache.get_cache()
        cache2 = SharedModelCache.get_cache()
        
        assert cache1 is cache2
    
    def test_reset(self):
        SharedModelCache.reset()
        cache1 = SharedModelCache.get_cache()
        
        SharedModelCache.reset()
        cache2 = SharedModelCache.get_cache()
        
        # After reset, should be different instances
        assert cache1 is not cache2
