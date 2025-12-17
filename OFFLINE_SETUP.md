# 🔌 Offline Setup Guide

This guide shows how to run the AI Language Translator completely offline with reduced functionality.

## 🌐 Online vs Offline Capabilities

### Online Features (Require Internet)
- **Translation**: Google Translate API, MyMemory API
- **Speech Recognition**: Google Speech Recognition, Wit.ai
- **Text-to-Speech**: Google TTS (gTTS)

### Offline Features (No Internet Required)
- **Translation**: AI Models (Marian MT) - Downloaded once, cached locally
- **Speech Recognition**: CMU Sphinx (English only)
- **Text-to-Speech**: Local TTS engines (OS-dependent)
- **Language Detection**: langdetect library (works offline)
- **History Management**: SQLite database (local)
- **Caching**: Redis (local) or disk cache

## 🚀 Quick Offline Setup

### 1. Install Offline Dependencies

```bash
# Core offline packages
pip install torch transformers sentence-transformers
pip install pocketsphinx  # For offline speech recognition
pip install espeak-ng    # For offline TTS (Linux/macOS)

# Windows TTS (if on Windows)
pip install pyttsx3
```

### 2. Download AI Models (One-time)

```bash
# Start the app once to download models
python3 -c "
from core.translator import AITranslator
translator = AITranslator()
# This will download and cache common language models
translator.translate_with_ai('Hello world', 'en', 'es')
translator.translate_with_ai('Bonjour', 'fr', 'en')
translator.translate_with_ai('Hola', 'es', 'en')
print('Models downloaded and cached!')
"
```

### 3. Configure for Offline Mode

Create `.env` file:
```bash
# Disable online services
OFFLINE_MODE=true
USE_GOOGLE_TRANSLATE=false
USE_MYMEMORY=false
USE_GOOGLE_TTS=false
USE_GOOGLE_STT=false

# Use local services
USE_AI_MODELS=true
USE_SPHINX_STT=true
USE_LOCAL_TTS=true
```

## 📦 Detailed Offline Components

### 1. Offline Translation (AI Models)

The system uses **Marian MT models** from Hugging Face:

```python
# These models work offline once downloaded
model_examples = {
    'en-es': 'Helsinki-NLP/opus-mt-en-es',
    'es-en': 'Helsinki-NLP/opus-mt-es-en', 
    'en-fr': 'Helsinki-NLP/opus-mt-en-fr',
    'fr-en': 'Helsinki-NLP/opus-mt-fr-en',
    'en-de': 'Helsinki-NLP/opus-mt-en-de',
    # ... 100+ language pairs available
}
```

**Advantages:**
- ✅ Works completely offline
- ✅ Good quality for major languages
- ✅ Fast after initial download
- ✅ Privacy-friendly (no data sent online)

**Limitations:**
- ❌ Large download size (500MB-2GB per model)
- ❌ Limited language pairs compared to online services
- ❌ Requires significant disk space

### 2. Offline Speech Recognition (Sphinx)

Uses **CMU PocketSphinx** for offline speech recognition:

```python
# Enable offline speech recognition
speech_recognizer.recognize_from_file(
    audio_bytes, 
    language='en',  # English only
    engine='sphinx'  # Offline engine
)
```

**Advantages:**
- ✅ Completely offline
- ✅ No API limits
- ✅ Privacy-friendly

**Limitations:**
- ❌ English only
- ❌ Lower accuracy than Google
- ❌ Requires quiet environment

### 3. Offline Text-to-Speech

Multiple offline TTS options:

#### Option A: eSpeak-NG (Linux/macOS)
```bash
# Install eSpeak
sudo apt install espeak-ng  # Ubuntu/Debian
brew install espeak        # macOS

# Use in Python
import subprocess
subprocess.run(['espeak', 'Hello world'])
```

#### Option B: pyttsx3 (Cross-platform)
```python
import pyttsx3
engine = pyttsx3.init()
engine.say('Hello world')
engine.runAndWait()
```

#### Option C: System TTS (macOS/Windows)
```bash
# macOS
say "Hello world"

# Windows
powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('Hello world')"
```

## 🛠️ Implementation: Offline Mode

Let me create an offline-capable version:

### Enhanced Translator with Offline Mode

```python
class OfflineTranslator(AITranslator):
    def __init__(self, offline_mode=False):
        super().__init__()
        self.offline_mode = offline_mode or os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
    
    def smart_translate(self, text, source_lang, target_lang):
        if self.offline_mode:
            # Try AI model first (offline)
            result = self.translate_with_ai(text, source_lang, target_lang)
            if result:
                return result
            else:
                return {
                    'translation': text,  # Fallback: return original
                    'method': 'Offline Fallback',
                    'confidence': 0.1,
                    'error': 'No offline model available for this language pair'
                }
        else:
            # Use normal online fallback chain
            return super().smart_translate(text, source_lang, target_lang)
```

## 📱 Offline Usage Examples

### 1. Streamlit App (Offline)
```bash
# Set offline mode
export OFFLINE_MODE=true
streamlit run app_streamlit_enhanced.py
```

### 2. API Server (Offline)
```bash
# Start offline API
export OFFLINE_MODE=true
uvicorn api_server_fastapi:app --port 8000
```

### 3. Command Line (Offline)
```python
from core.translator import AITranslator

# Force offline mode
translator = AITranslator()
result = translator.translate_with_ai("Hello world", "en", "es")
print(result)  # Uses cached Marian model
```

## 💾 Storage Requirements

### Disk Space Needed:
- **Base system**: ~500MB
- **AI models** (per language pair): ~300-500MB
- **Speech models**: ~100MB
- **Cache data**: ~50-200MB

### For 10 common language pairs: ~5GB total

## 🔧 Offline Configuration

### 1. Pre-download Models
```bash
python3 scripts/download_offline_models.py
```

### 2. Configure Offline Services
```bash
# Copy example config
cp .env.example .env.offline

# Edit for offline mode
echo "OFFLINE_MODE=true" >> .env.offline
echo "USE_AI_MODELS=true" >> .env.offline
echo "USE_SPHINX_STT=true" >> .env.offline
```

### 3. Test Offline Mode
```bash
# Disconnect internet and test
python3 test_offline.py
```

## 🌟 Hybrid Mode (Best of Both)

For the best experience, use **hybrid mode**:

```python
class HybridTranslator:
    def smart_translate(self, text, source_lang, target_lang):
        # Try offline first (fast, private)
        offline_result = self.translate_with_ai(text, source_lang, target_lang)
        if offline_result and offline_result['confidence'] > 0.8:
            return offline_result
        
        # Fallback to online (better quality)
        try:
            online_result = self.translate_with_google(text, source_lang, target_lang)
            return online_result
        except:
            # Return offline result if online fails
            return offline_result or {'translation': text, 'method': 'Fallback'}
```

## 📊 Performance Comparison

| Feature | Online | Offline | Hybrid |
|---------|--------|---------|--------|
| **Speed** | 2-5s | 0.5-2s | 0.5-5s |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Privacy** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Languages** | 100+ | 50+ | 100+ |
| **Reliability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🚨 Limitations of Offline Mode

1. **Language Coverage**: Fewer language pairs available
2. **Model Size**: Requires significant disk space
3. **Quality**: Slightly lower than premium online services
4. **Speech Recognition**: English-only with Sphinx
5. **Updates**: Models need manual updates

## 🎯 Recommended Setup

For most users, I recommend **hybrid mode**:
1. Install offline models for your most-used languages
2. Keep online services as fallback
3. Use offline for privacy-sensitive content
4. Use online for rare language pairs

This gives you the best of both worlds: speed, privacy, and comprehensive language support.