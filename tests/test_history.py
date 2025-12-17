"""Unit tests for history manager module"""

import pytest
import tempfile
import os
from pathlib import Path
from core.history import HistoryManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def history_manager(temp_db):
    """Create history manager with temp database"""
    return HistoryManager(db_path=temp_db)


class TestHistoryManager:
    """Tests for HistoryManager"""
    
    def test_init_creates_database(self, temp_db):
        manager = HistoryManager(db_path=temp_db)
        assert Path(temp_db).exists()
    
    def test_add_entry(self, history_manager):
        result = {
            "translation": "Hola mundo",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.95,
            "time": 0.1
        }
        success = history_manager.add_entry("Hello world", result, "es")
        assert success is True
    
    def test_get_recent(self, history_manager):
        # Add some entries
        for i in range(5):
            result = {
                "translation": f"Translation {i}",
                "source_lang": "en",
                "method": "Test",
                "confidence": 0.9,
                "time": 0.1
            }
            history_manager.add_entry(f"Text {i}", result, "es")
        
        recent = history_manager.get_recent(3)
        assert len(recent) == 3
    
    def test_get_all(self, history_manager):
        # Add entries
        for i in range(3):
            result = {
                "translation": f"Translation {i}",
                "source_lang": "en",
                "method": "Test",
                "confidence": 0.9,
                "time": 0.1
            }
            history_manager.add_entry(f"Text {i}", result, "es")
        
        all_entries = history_manager.get_all()
        assert len(all_entries) == 3
    
    def test_search(self, history_manager):
        result = {
            "translation": "Hola mundo",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.95,
            "time": 0.1
        }
        history_manager.add_entry("Hello world", result, "es")
        history_manager.add_entry("Goodbye world", result, "es")
        
        results = history_manager.search("Hello")
        assert len(results) == 1
        assert "Hello" in results[0]["original_text"]
    
    def test_search_field_whitelist(self, history_manager):
        """Test that search field is whitelisted to prevent SQL injection"""
        result = {
            "translation": "Test",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Test text", result, "es")
        
        # Attempt SQL injection - should default to original_text
        results = history_manager.search("Test", field="id; DROP TABLE translations;--")
        # Should not raise an error, should use default field
        assert isinstance(results, list)
    
    def test_clear_history(self, history_manager):
        result = {
            "translation": "Test",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Test", result, "es")
        
        success = history_manager.clear_history()
        assert success is True
        
        all_entries = history_manager.get_all()
        assert len(all_entries) == 0
    
    def test_get_stats_empty(self, history_manager):
        stats = history_manager.get_stats()
        assert stats is None
    
    def test_get_stats(self, history_manager):
        for i in range(5):
            result = {
                "translation": f"Translation {i}",
                "source_lang": "en",
                "method": "Google Translate" if i % 2 == 0 else "AI Model",
                "confidence": 0.9,
                "time": 0.1
            }
            history_manager.add_entry(f"Text {i}", result, "es")
        
        stats = history_manager.get_stats()
        assert stats is not None
        assert stats["total_translations"] == 5
        assert "avg_confidence" in stats
        assert "methods_used" in stats
    
    def test_export_json(self, history_manager):
        result = {
            "translation": "Test",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Test", result, "es")
        
        exported = history_manager.export_history("json")
        assert exported is not None
        assert "Test" in exported
    
    def test_export_csv(self, history_manager):
        result = {
            "translation": "Test",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Test", result, "es")
        
        exported = history_manager.export_history("csv")
        assert exported is not None
        assert "original_text" in exported
    
    def test_get_by_language_pair(self, history_manager):
        result_en_es = {
            "translation": "Hola",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        result_en_fr = {
            "translation": "Bonjour",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Hello", result_en_es, "es")
        history_manager.add_entry("Hello", result_en_fr, "fr")
        
        results = history_manager.get_by_language_pair("en", "es")
        assert len(results) == 1
        assert results[0]["target_lang"] == "es"
    
    def test_get_database_size(self, history_manager):
        result = {
            "translation": "Test",
            "source_lang": "en",
            "method": "Test",
            "confidence": 0.9,
            "time": 0.1
        }
        history_manager.add_entry("Test", result, "es")
        
        size_info = history_manager.get_database_size()
        assert size_info is not None
        assert "size_bytes" in size_info
        assert "record_count" in size_info
        assert size_info["record_count"] == 1
