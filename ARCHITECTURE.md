# Architecture Documentation

## 🏛️ Project Structure

The AI Language Translator has been refactored into a clean, modular architecture with proper separation of concerns.

```
ai-language-translator/
├── 📚 core/                    # Core library (reusable logic)
│   ├── __init__.py            # Package initialization
│   ├── translator.py          # Translation logic (AI models, APIs)
│   ├── history.py             # History management
│   ├── audio.py               # Text-to-Speech functionality
│   └── caching.py             # Model and result caching
│
├── 🤖 app_streamlit.py        # Streamlit web application
├── 🔌 app_api.py              # Flask REST API server
├── 📊 app_batch.py            # Batch translation CLI tool
├── 🚀 run.py                  # Main runner script
├── 📦 requirements.txt        # Python dependencies
│
├── 📁 translation_history/    # Translation history storage
├── 📁 temp_audio/             # Temporary audio files
└── 📄 ARCHITECTURE.md         # This file

```

## 🎯 Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **core/translator.py**: Translation logic only
- **core/history.py**: History management only
- **core/audio.py**: TTS functionality only
- **core/caching.py**: Caching utilities only

### 2. Reusability
The `core/` library can be imported by any application:
```python
from core.translator import AITranslator
from core.history import HistoryManager
from core.audio import AudioManager
```

### 3. No Circular Dependencies
- Core modules don't depend on application code
- Applications depend on core modules
- Clean dependency flow: Apps → Core → External Libraries

### 4. Shared State
All applications can now share the same translator instance and caches, improving performance and consistency.

## 📦 Core Modules

### core/translator.py
**Purpose**: Pure translation logic

**Key Methods**:
- `detect_language(text)` - Language detection
- `translate_with_ai(text, source, target)` - AI model translation
- `translate_with_google(text, source, target)` - Google Translate
- `translate_with_mymemory(text, source, target)` - MyMemory translation
- `smart_translate(text, source, target)` - Smart fallback chain
- `validate_input(text, source, target)` - Input validation

**No Dependencies On**: Streamlit, Flask, pygame (moved to audio.py)

### core/history.py
**Purpose**: Translation history management

**Key Methods**:
- `add_entry(original, result, target_lang)` - Add translation to history
- `load_history()` - Load from JSON file
- `save_history()` - Save to JSON file
- `get_stats()` - Calculate statistics
- `export_history(format)` - Export as JSON/CSV
- `clear_history()` - Clear all history
- `get_recent(count)` - Get recent translations

**Storage**: JSON files in `translation_history/` directory

### core/audio.py
**Purpose**: Text-to-Speech functionality

**Key Methods**:
- `generate_tts_audio(text, language)` - Generate audio file
- `play_audio(audio_file)` - Play audio
- `stop_audio()` - Stop playback
- `text_to_speech(text, language)` - Complete TTS workflow
- `is_playing()` - Check playback status
- `cleanup()` - Clean temporary files

**Dependencies**: gTTS, pygame (isolated here)

### core/caching.py
**Purpose**: Model and translation caching

**Key Methods**:
- `get_model(model_name)` - Get cached model
- `set_model(model_name, model_data)` - Cache model
- `cache_translation(text, source, target, result)` - Cache translation
- `get_cached_translation(text, source, target)` - Get cached result
- `get_cache_stats()` - Cache statistics

## 🚀 Applications

### app_streamlit.py
**Purpose**: Interactive web UI

**Features**:
- Real-time translation interface
- Language selection
- TTS playback
- History viewing
- Statistics dashboard

**Dependencies**: 
- streamlit
- core.translator
- core.history
- core.audio

**Run**: `python run.py web` or `streamlit run app_streamlit.py`

### app_api.py
**Purpose**: REST API server

**Endpoints**:
- `POST /api/translate` - Translate text
- `POST /api/detect` - Detect language
- `GET /api/languages` - List supported languages
- `POST /api/batch` - Batch translation
- `GET /health` - Health check

**Dependencies**:
- flask, flask_cors
- core.translator (only!)

**Run**: `python run.py api` or `python app_api.py`

**Note**: API server doesn't need streamlit or pygame!

### app_batch.py
**Purpose**: Batch file translation

**Supported Formats**:
- CSV files (with column selection)
- JSON files (with field selection)
- Plain text files

**Dependencies**:
- pandas
- core.translator (only!)

**Run**: `python run.py batch input.csv output.csv --text-column "text"`

## 🔄 Migration Guide

### Old Code
```python
from ai_translator import AITranslator

translator = AITranslator()
result = translator.smart_translate("Hello", "en", "es")
translator.save_translation_history("Hello", result)
translator.text_to_speech(result['translation'], "es")
```

### New Code
```python
from core.translator import AITranslator
from core.history import HistoryManager
from core.audio import AudioManager

translator = AITranslator()
history = HistoryManager()
audio = AudioManager()

result = translator.smart_translate("Hello", "en", "es")
history.add_entry("Hello", result, "es")
audio.text_to_speech(result['translation'], "es")
```

## ✅ Benefits

### Before Refactoring
- ❌ Monolithic 600+ line file
- ❌ API server imports Streamlit (unnecessary)
- ❌ Batch tool imports pygame (unnecessary)
- ❌ No code reuse between apps
- ❌ Difficult to test individual components
- ❌ Tight coupling between UI and logic

### After Refactoring
- ✅ Modular, focused files (100-200 lines each)
- ✅ API server only imports what it needs
- ✅ Batch tool is lightweight
- ✅ Core library reusable across all apps
- ✅ Easy to test each module independently
- ✅ Clean separation of concerns
- ✅ Professional software architecture

## 🧪 Testing

Each core module can now be tested independently:

```python
# Test translator
from core.translator import AITranslator
translator = AITranslator()
result = translator.smart_translate("Hello", "en", "es")
assert result is not None

# Test history
from core.history import HistoryManager
history = HistoryManager()
history.add_entry("Hello", result, "es")
assert len(history.get_all()) > 0

# Test audio
from core.audio import AudioManager
audio = AudioManager()
audio_file, error = audio.generate_tts_audio("Hola", "es")
assert error is None
```

## 🔮 Future Enhancements

With this architecture, you can easily:

1. **Add new applications** (e.g., CLI tool, desktop app) by importing core modules
2. **Swap implementations** (e.g., different TTS engine) by modifying only core/audio.py
3. **Add database support** by updating core/history.py without touching apps
4. **Implement caching** using core/caching.py across all apps
5. **Create unit tests** for each module independently
6. **Deploy API separately** without Streamlit dependencies

## 📝 Notes

- Old files (`ai_translator.py`, `api_server.py`, `batch_translator.py`) can be kept for reference or removed
- All apps now use the same core logic, ensuring consistency
- The `run.py` script has been updated to use new file names
- No changes to `requirements.txt` needed - same dependencies, better organization
