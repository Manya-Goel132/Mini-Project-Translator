#!/usr/bin/env python3
"""
Demo script showing offline capabilities
"""

import os
import asyncio


async def demo_offline_tts():
    """Demo offline text-to-speech"""
    print("🔊 Testing Offline Text-to-Speech")
    print("-" * 40)
    
    try:
        from core.offline_tts import OfflineTTSManager
        
        tts = OfflineTTSManager()
        print(f"Available engines: {list(tts.available_engines.keys())}")
        print(f"Preferred engine: {tts.preferred_engine}")
        
        if tts.preferred_engine:
            print("\nGenerating audio for 'Hello, this is offline TTS!'...")
            audio_bytes, error = await tts.generate_audio_bytes(
                "Hello, this is offline TTS!",
                language="en"
            )
            
            if audio_bytes:
                print(f"✅ Generated {len(audio_bytes)} bytes of audio")
                
                # Save to file for testing
                with open("demo_tts.wav", "wb") as f:
                    f.write(audio_bytes)
                print("💾 Saved as demo_tts.wav")
                
                # Try to play on macOS
                if os.uname().sysname == 'Darwin':
                    os.system("afplay demo_tts.wav")
                    print("🎵 Played audio")
            else:
                print(f"❌ Error: {error}")
        else:
            print("❌ No offline TTS engines available")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_offline_stt():
    """Demo offline speech recognition"""
    print("\n🎤 Testing Offline Speech Recognition")
    print("-" * 40)
    
    try:
        from core.offline_stt import OfflineSTTManager
        
        stt = OfflineSTTManager()
        
        if stt.sphinx_available:
            print("✅ PocketSphinx available for offline recognition")
            print("📝 Note: Only English is supported offline")
            print("💡 To test: Record audio and save as 'test_audio.wav'")
            
            # Check if test audio exists
            if os.path.exists("test_audio.wav"):
                print("\nFound test_audio.wav, transcribing...")
                with open("test_audio.wav", "rb") as f:
                    audio_bytes = f.read()
                
                text, error = stt.recognize_from_audio_bytes_sync(audio_bytes, "en")
                
                if text:
                    print(f"✅ Transcription: '{text}'")
                else:
                    print(f"❌ Error: {error}")
            else:
                print("💡 Create test_audio.wav to test transcription")
        else:
            print("❌ PocketSphinx not available")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_offline_translation():
    """Demo offline translation"""
    print("\n🌍 Testing Offline Translation")
    print("-" * 40)
    
    try:
        from core.offline_translator import OfflineTranslator
        
        # Force offline mode
        translator = OfflineTranslator(offline_mode=True)
        
        print("Available offline language pairs:")
        pairs = translator.get_offline_language_pairs()
        for i, (source, target) in enumerate(pairs[:10]):  # Show first 10
            print(f"  {source} → {target}")
        print(f"  ... and {len(pairs) - 10} more")
        
        print(f"\nSupported offline languages: {sorted(translator.get_offline_languages())}")
        
        # Test translation
        test_cases = [
            ("Hello world", "en", "es"),
            ("Good morning", "en", "fr"),
            ("Thank you", "en", "de")
        ]
        
        print("\nTesting translations:")
        for text, source, target in test_cases:
            if translator.is_offline_available(source, target):
                print(f"\n📝 '{text}' ({source} → {target})")
                result = translator.smart_translate(text, source, target)
                
                if result:
                    print(f"✅ Translation: '{result['translation']}'")
                    print(f"   Method: {result['method']}")
                    print(f"   Offline: {result.get('offline', False)}")
                    print(f"   Time: {result['time']:.2f}s")
                else:
                    print("❌ Translation failed")
            else:
                print(f"\n❌ '{text}' ({source} → {target}) - No offline model")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_language_detection():
    """Demo offline language detection"""
    print("\n🔍 Testing Language Detection (Offline)")
    print("-" * 40)
    
    try:
        from core.translator import AITranslator
        
        translator = AITranslator()
        
        test_texts = [
            "Hello, how are you today?",
            "Bonjour, comment allez-vous?",
            "Hola, ¿cómo estás?",
            "Guten Tag, wie geht es Ihnen?",
            "Buongiorno, come stai?",
            "こんにちは、元気ですか？",
            "안녕하세요, 어떻게 지내세요?",
            "Привет, как дела?"
        ]
        
        for text in test_texts:
            lang, confidence = translator.detect_language(text)
            lang_name = translator.supported_languages.get(lang, lang)
            print(f"'{text[:30]}...' → {lang} ({lang_name}) {confidence:.0%}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run offline demos"""
    print("🔌 AI Language Translator - Offline Demo")
    print("=" * 50)
    
    # Language detection (always works offline)
    demo_language_detection()
    
    # Translation (works offline with cached models)
    demo_offline_translation()
    
    # TTS (works offline with system engines)
    await demo_offline_tts()
    
    # STT (works offline with Sphinx)
    demo_offline_stt()
    
    print("\n" + "=" * 50)
    print("🎉 Offline Demo Complete!")
    print("\n💡 To enable offline mode:")
    print("   cp .env.offline .env")
    print("   export OFFLINE_MODE=true")
    print("   streamlit run app_streamlit_enhanced.py")


if __name__ == "__main__":
    asyncio.run(main())