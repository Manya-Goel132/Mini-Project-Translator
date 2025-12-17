"""Unit tests for core translator module"""

import pytest
from core.translator import AITranslator


@pytest.fixture
def translator():
    """Create translator instance for tests"""
    return AITranslator()


class TestLanguageDetection:
    """Tests for language detection"""
    
    def test_detect_english(self, translator):
        text = "Hello, how are you today?"
        lang, confidence = translator.detect_language(text)
        assert lang == "en"
        assert confidence > 0.5
    
    def test_detect_spanish(self, translator):
        text = "Hola, ¿cómo estás hoy?"
        lang, confidence = translator.detect_language(text)
        assert lang == "es"
        assert confidence > 0.5
    
    def test_detect_french(self, translator):
        text = "Bonjour, comment allez-vous?"
        lang, confidence = translator.detect_language(text)
        assert lang == "fr"
        assert confidence > 0.5
    
    def test_detect_empty_text(self, translator):
        lang, confidence = translator.detect_language("")
        assert lang == "en"
        assert confidence < 0.5
    
    def test_detect_short_text(self, translator):
        lang, confidence = translator.detect_language("Hi")
        assert lang is not None
        assert 0 <= confidence <= 1
    
    def test_detect_chinese(self, translator):
        text = "你好世界"
        lang, confidence = translator.detect_language(text)
        assert lang == "zh"
    
    def test_detect_japanese(self, translator):
        text = "こんにちは"
        lang, confidence = translator.detect_language(text)
        assert lang == "ja"
    
    def test_detect_korean(self, translator):
        text = "안녕하세요"
        lang, confidence = translator.detect_language(text)
        assert lang == "ko"


class TestInputValidation:
    """Tests for input validation"""
    
    def test_validate_empty_text(self, translator):
        errors = translator.validate_input("", "en", "es")
        assert len(errors) > 0
        assert any("enter some text" in e.lower() for e in errors)
    
    def test_validate_same_language(self, translator):
        errors = translator.validate_input("Hello", "en", "en")
        assert len(errors) > 0
        assert any("same" in e.lower() for e in errors)
    
    def test_validate_auto_same_target(self, translator):
        # auto source with any target should be valid
        errors = translator.validate_input("Hello", "auto", "en")
        assert len(errors) == 0
    
    def test_validate_long_text(self, translator):
        long_text = "a" * 15000
        errors = translator.validate_input(long_text, "en", "es")
        assert len(errors) > 0
        assert any("too long" in e.lower() for e in errors)
    
    def test_validate_valid_input(self, translator):
        errors = translator.validate_input("Hello world", "en", "es")
        assert len(errors) == 0


class TestSupportedLanguages:
    """Tests for supported languages"""
    
    def test_has_supported_languages(self, translator):
        assert len(translator.supported_languages) > 0
    
    def test_english_supported(self, translator):
        assert "en" in translator.supported_languages
    
    def test_spanish_supported(self, translator):
        assert "es" in translator.supported_languages
    
    def test_language_names(self, translator):
        assert translator.supported_languages["en"] == "English"
        assert translator.supported_languages["es"] == "Spanish"


class TestTranslation:
    """Tests for translation (integration tests - may be slow)"""
    
    @pytest.mark.slow
    def test_translate_google(self, translator):
        result, source, method = translator.translate_with_google("Hello", "en", "es")
        assert result is not None
        assert method == "Google Translate"
    
    @pytest.mark.slow
    def test_translate_mymemory(self, translator):
        result, method = translator.translate_with_mymemory("Hello", "en", "es")
        assert result is not None
        assert method == "MyMemory"
    
    @pytest.mark.slow
    def test_smart_translate(self, translator):
        result = translator.smart_translate("Hello world", "en", "es")
        assert result is not None
        assert "translation" in result
        assert "method" in result
        assert "confidence" in result
    
    @pytest.mark.slow
    def test_smart_translate_auto_detect(self, translator):
        result = translator.smart_translate("Bonjour le monde", "auto", "en")
        assert result is not None
        assert result["source_lang"] == "fr"
