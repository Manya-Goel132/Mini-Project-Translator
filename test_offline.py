#!/usr/bin/env python3
"""
Test script for offline functionality
"""

import os
import sys
from pathlib import Path


def test_offline_translation():
    """Test offline translation capabilities"""
    print("🔍 Testing offline translation...")
    
    try:
        from core.offline_translator import OfflineTranslator
        
        # Force offline mode
        translator = OfflineTranslator(offline_mode=True)
        
        # Test basic translation
        result = translator.smart_translate("Hello world", "en", "es")
        
        if result:
            print(f"✅ Translation: '{result['translation']}'")
            print(f"   Method: {result['method']}")
            print(f"   Offline: {result.get('offline', False)}")
            print(f"   Time: {result['time']:.2f}s")
            return True
        else:
            print("❌ Translation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_offline_tts():
    """Test offline text-to-speech"""
    print("\n🔍 Testing offline TTS...")
    
    try:
        from core.offline_tts import OfflineTTSManager
        
        tts = OfflineTTSManager()
        
        print(f"Available engines: {list(tts.available_engines.keys())}")
        print(f"Preferred engine: {tts.preferred_engine}")
        
        if tts.preferred_engine:
            print("✅ Offline TTS available")
            return True
        else:
            print("❌ No offline TTS engines available")
            print("💡 Install: pip install pyttsx3")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_offline_stt():
    """Test offline speech recognition"""
    print("\n🔍 Testing offline STT...")
    
    try:
        from core.offline_stt import OfflineSTTManager
        
        stt = OfflineSTTManager()
        
        if stt.sphinx_available:
            print("✅ Offline STT (Sphinx) available")
            return True
        else:
            print("❌ Offline STT not available")
            print("💡 Install: pip install pocketsphinx")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_language_detection():
    """Test offline language detection"""
    print("\n🔍 Testing language detection...")
    
    try:
        from core.translator import AITranslator
        
        translator = AITranslator()
        
        # Test various languages
        test_texts = [
            ("Hello world", "en"),
            ("Bonjour le monde", "fr"),
            ("Hola mundo", "es"),
            ("Guten Tag", "de"),
            ("こんにちは", "ja")
        ]
        
        all_passed = True
        for text, expected in test_texts:
            detected, confidence = translator.detect_language(text)
            if detected == expected:
                print(f"✅ '{text}' → {detected} ({confidence:.1%})")
            else:
                print(f"❌ '{text}' → {detected} (expected {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_caching():
    """Test offline caching"""
    print("\n🔍 Testing caching...")
    
    try:
        from core.caching import ModelCache
        
        cache = ModelCache(use_redis=False)  # Force disk cache
        
        # Test translation cache
        test_result = {
            'translation': 'Hola mundo',
            'method': 'Test',
            'confidence': 0.95,
            'time': 0.1
        }
        
        cache.cache_translation("Hello world", "en", "es", test_result)
        cached = cache.get_cached_translation("Hello world", "en", "es")
        
        if cached and cached['translation'] == 'Hola mundo':
            print("✅ Disk caching works")
            return True
        else:
            print("❌ Disk caching failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def setup_offline_mode():
    """Set up offline mode configuration"""
    print("\n🔧 Setting up offline mode...")
    
    env_content = """# Offline Mode Configuration
OFFLINE_MODE=true
USE_AI_MODELS=true
USE_GOOGLE_TRANSLATE=false
USE_MYMEMORY=false
USE_GOOGLE_TTS=false
USE_GOOGLE_STT=false
USE_SPHINX_STT=true
USE_LOCAL_TTS=true
"""
    
    try:
        with open('.env.offline', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env.offline configuration")
        print("💡 To use: cp .env.offline .env")
        return True
        
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return False


def download_models():
    """Download common AI models for offline use"""
    print("\n📥 Downloading AI models...")
    
    try:
        from core.offline_translator import OfflineTranslator
        
        translator = OfflineTranslator(offline_mode=True)
        
        # Common language pairs to preload
        common_pairs = [
            ('en', 'es'), ('es', 'en'),
            ('en', 'fr'), ('fr', 'en'),
            ('en', 'de'), ('de', 'en')
        ]
        
        print("Downloading models (this may take a while)...")
        results = translator.preload_models(common_pairs)
        
        print(f"✅ Loaded {len(results['loaded'])} models")
        for source, target, model_name in results['loaded']:
            print(f"   - {source} → {target}")
        
        if results['errors']:
            print(f"❌ {len(results['errors'])} errors:")
            for source, target, error in results['errors']:
                print(f"   - {source} → {target}: {error}")
        
        return len(results['loaded']) > 0
        
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        return False


def check_disk_space():
    """Check available disk space for models"""
    print("\n💾 Checking disk space...")
    
    try:
        import shutil
        
        total, used, free = shutil.disk_usage('.')
        free_gb = free / (1024**3)
        
        print(f"Free space: {free_gb:.1f} GB")
        
        if free_gb < 2:
            print("⚠️  Warning: Less than 2GB free space")
            print("   AI models require significant storage")
            return False
        elif free_gb < 5:
            print("⚠️  Caution: Less than 5GB free space")
            print("   Consider freeing up space for more models")
            return True
        else:
            print("✅ Sufficient disk space available")
            return True
            
    except Exception as e:
        print(f"❌ Error checking disk space: {e}")
        return False


def main():
    """Run all offline tests"""
    print("🔌 AI Language Translator - Offline Mode Test")
    print("=" * 50)
    
    # Check disk space first
    space_ok = check_disk_space()
    
    # Run tests
    tests = [
        ("Language Detection", test_language_detection),
        ("Caching", test_caching),
        ("Offline Translation", test_offline_translation),
        ("Offline TTS", test_offline_tts),
        ("Offline STT", test_offline_stt),
    ]
    
    results = {}
    for name, test_func in tests:
        results[name] = test_func()
    
    # Setup
    setup_ok = setup_offline_mode()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    if setup_ok:
        print("✅ PASS - Configuration Setup")
    
    # Overall status
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Offline mode is ready.")
        
        if space_ok:
            download = input("\n📥 Download AI models now? (y/N): ").lower().strip()
            if download == 'y':
                download_models()
        
        print("\n💡 To enable offline mode:")
        print("   cp .env.offline .env")
        print("   python3 app_streamlit_enhanced.py")
        
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        print("\n💡 Install missing dependencies:")
        print("   pip install pyttsx3 pocketsphinx")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)