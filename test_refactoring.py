#!/usr/bin/env python3
"""
Quick test script to verify the refactored architecture works correctly
"""

import sys


def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from core.translator import AITranslator
        print("  ✅ core.translator imported")
    except ImportError as e:
        print(f"  ❌ Failed to import core.translator: {e}")
        return False
    
    try:
        from core.history import HistoryManager
        print("  ✅ core.history imported")
    except ImportError as e:
        print(f"  ❌ Failed to import core.history: {e}")
        return False
    
    try:
        from core.audio import AudioManager
        print("  ✅ core.audio imported")
    except ImportError as e:
        print(f"  ❌ Failed to import core.audio: {e}")
        return False
    
    try:
        from core.caching import ModelCache
        print("  ✅ core.caching imported")
    except ImportError as e:
        print(f"  ❌ Failed to import core.caching: {e}")
        return False
    
    return True


def test_translator():
    """Test translator functionality"""
    print("\n🧪 Testing translator...")
    
    try:
        from core.translator import AITranslator
        
        translator = AITranslator()
        print("  ✅ AITranslator instantiated")
        
        # Test language detection
        lang, confidence = translator.detect_language("Hello world")
        print(f"  ✅ Language detection works: {lang} ({confidence:.2f})")
        
        # Test supported languages
        assert len(translator.supported_languages) > 0
        print(f"  ✅ Supported languages loaded: {len(translator.supported_languages)} languages")
        
        # Test validation
        errors = translator.validate_input("Hello", "en", "es")
        assert len(errors) == 0
        print("  ✅ Input validation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Translator test failed: {e}")
        return False


def test_history():
    """Test history manager"""
    print("\n🧪 Testing history manager...")
    
    try:
        from core.history import HistoryManager
        
        history = HistoryManager(history_dir="test_history")
        print("  ✅ HistoryManager instantiated")
        
        # Test adding entry
        mock_result = {
            'translation': 'Hola',
            'source_lang': 'en',
            'method': 'Test',
            'confidence': 0.95,
            'time': 0.1
        }
        
        success = history.add_entry("Hello", mock_result, "es")
        assert success
        print("  ✅ Entry added to history")
        
        # Test getting history
        all_history = history.get_all()
        assert len(all_history) > 0
        print(f"  ✅ History retrieved: {len(all_history)} entries")
        
        # Test stats
        stats = history.get_stats()
        assert stats is not None
        print("  ✅ Statistics calculated")
        
        # Clean up
        history.clear_history()
        print("  ✅ History cleared")
        
        return True
        
    except Exception as e:
        print(f"  ❌ History test failed: {e}")
        return False


def test_audio():
    """Test audio manager"""
    print("\n🧪 Testing audio manager...")
    
    try:
        from core.audio import AudioManager
        
        audio = AudioManager(audio_dir="test_audio")
        print("  ✅ AudioManager instantiated")
        
        if audio.audio_available:
            print("  ✅ Audio system available")
        else:
            print("  ⚠️  Audio system not available (this is OK)")
        
        # Test language mapping
        assert len(audio.tts_lang_map) > 0
        print("  ✅ TTS language mapping loaded")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Audio test failed: {e}")
        return False


def test_caching():
    """Test caching utilities"""
    print("\n🧪 Testing caching...")
    
    try:
        from core.caching import ModelCache
        
        cache = ModelCache(cache_dir="test_cache")
        print("  ✅ ModelCache instantiated")
        
        # Test model caching
        cache.set_model("test_model", {"data": "test"})
        model = cache.get_model("test_model")
        assert model is not None
        print("  ✅ Model caching works")
        
        # Test translation caching
        cache.cache_translation("Hello", "en", "es", {"translation": "Hola"})
        cached = cache.get_cached_translation("Hello", "en", "es")
        assert cached is not None
        print("  ✅ Translation caching works")
        
        # Test stats
        stats = cache.get_cache_stats()
        assert stats['models_cached'] == 1
        assert stats['translations_cached'] == 1
        print("  ✅ Cache statistics work")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Caching test failed: {e}")
        return False


def test_integration():
    """Test integration between modules"""
    print("\n🧪 Testing integration...")
    
    try:
        from core.translator import AITranslator
        from core.history import HistoryManager
        from core.audio import AudioManager
        from core.caching import ModelCache
        
        # Create instances
        translator = AITranslator()
        history = HistoryManager(history_dir="test_history")
        audio = AudioManager(audio_dir="test_audio")
        cache = ModelCache(cache_dir="test_cache")
        
        print("  ✅ All modules instantiated together")
        
        # Simulate a translation workflow
        text = "Hello"
        source_lang = "en"
        target_lang = "es"
        
        # Detect language
        detected, conf = translator.detect_language(text)
        print(f"  ✅ Language detected: {detected}")
        
        # Validate
        errors = translator.validate_input(text, source_lang, target_lang)
        assert len(errors) == 0
        print("  ✅ Input validated")
        
        # Mock translation result
        mock_result = {
            'translation': 'Hola',
            'source_lang': source_lang,
            'method': 'Test',
            'confidence': 0.95,
            'time': 0.1
        }
        
        # Save to history
        history.add_entry(text, mock_result, target_lang)
        print("  ✅ Translation saved to history")
        
        # Cache result
        cache.cache_translation(text, source_lang, target_lang, mock_result)
        print("  ✅ Translation cached")
        
        # Clean up
        history.clear_history()
        cache.clear_translations()
        print("  ✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 AI Language Translator - Refactoring Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Translator", test_translator),
        ("History", test_history),
        ("Audio", test_audio),
        ("Caching", test_caching),
        ("Integration", test_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring successful!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
