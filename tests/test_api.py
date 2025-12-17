"""Tests for FastAPI endpoints"""

import pytest
from fastapi.testclient import TestClient
from api_server_fastapi import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestLanguagesEndpoint:
    """Tests for languages endpoint"""
    
    def test_get_languages(self, client):
        response = client.get("/api/languages")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "languages" in data
        assert "en" in data["languages"]
        assert "es" in data["languages"]


class TestDetectEndpoint:
    """Tests for language detection endpoint"""
    
    def test_detect_english(self, client):
        response = client.post("/api/detect", json={"text": "Hello, how are you?"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["detected_language"] == "en"
    
    def test_detect_spanish(self, client):
        response = client.post("/api/detect", json={"text": "Hola, ¿cómo estás?"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["detected_language"] == "es"
    
    def test_detect_empty_text(self, client):
        response = client.post("/api/detect", json={"text": ""})
        assert response.status_code == 422  # Validation error


class TestTranslateEndpoint:
    """Tests for translation endpoint"""
    
    @pytest.mark.slow
    def test_translate_basic(self, client):
        response = client.post("/api/translate", json={
            "text": "Hello",
            "source_lang": "en",
            "target_lang": "es"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "translation" in data
        assert data["target_lang"] == "es"
    
    @pytest.mark.slow
    def test_translate_auto_detect(self, client):
        response = client.post("/api/translate", json={
            "text": "Bonjour",
            "source_lang": "auto",
            "target_lang": "en"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_translate_empty_text(self, client):
        response = client.post("/api/translate", json={
            "text": "",
            "source_lang": "en",
            "target_lang": "es"
        })
        assert response.status_code == 422  # Validation error
    
    def test_translate_missing_text(self, client):
        response = client.post("/api/translate", json={
            "source_lang": "en",
            "target_lang": "es"
        })
        assert response.status_code == 422


class TestCacheStatsEndpoint:
    """Tests for cache stats endpoint"""
    
    def test_get_cache_stats(self, client):
        response = client.get("/api/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data


class TestHomeEndpoint:
    """Tests for home page"""
    
    def test_home_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Translator API" in response.text


class TestTTSEndpoint:
    """Tests for text-to-speech endpoint"""
    
    @pytest.mark.slow
    def test_tts_basic(self, client):
        response = client.post("/api/tts", json={
            "text": "Hello world",
            "language": "en"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
    
    def test_tts_empty_text(self, client):
        response = client.post("/api/tts", json={
            "text": "",
            "language": "en"
        })
        assert response.status_code == 422
