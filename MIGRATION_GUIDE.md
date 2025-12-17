# Migration Guide: Old → New Architecture

## 🎯 Quick Start

The refactoring is **backward compatible** through the runner script. You can start using the new architecture immediately:

```bash
# Old way (still works if you keep old files)
streamlit run ai_translator.py
python api_server.py
python batch_translator.py input.csv output.csv

# New way (recommended)
python run.py web
python run.py api
python run.py batch input.csv output.csv
```

## 📋 File Mapping

| Old File | New File(s) | Purpose |
|----------|-------------|---------|
| `ai_translator.py` | `app_streamlit.py` + `core/translator.py` + `core/history.py` + `core/audio.py` | Separated UI from logic |
| `api_server.py` | `app_api.py` + `core/translator.py` | API now only imports what it needs |
| `batch_translator.py` | `app_batch.py` + `core/translator.py` | Batch tool uses core library |

## 🔄 Step-by-Step Migration

### Step 1: Test New Structure
```bash
# Install dependencies (if needed)
python run.py install

# Test web app
python run.py web

# Test API (in another terminal)
python run.py api

# Test batch translation
python run.py batch test.csv output.csv --text-column "text"
```

### Step 2: Update Your Code

If you have custom scripts importing the old modules:

**Before:**
```python
from ai_translator import AITranslator

translator = AITranslator()
result = translator.smart_translate("Hello", "en", "es")
translator.save_translation_history("Hello", result)
translator.text_to_speech(result['translation'], "es")
```

**After:**
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

### Step 3: Update Imports in Custom Scripts

**Old imports:**
```python
from ai_translator import AITranslator
from api_server import app
from batch_translator import BatchTranslator
```

**New imports:**
```python
from core.translator import AITranslator
from core.history import HistoryManager
from core.audio import AudioManager
from app_api import app
from app_batch import BatchTranslator
```

### Step 4: Remove Old Files (Optional)

Once you've verified everything works:

```bash
# Backup old files first
mkdir old_backup
mv ai_translator.py old_backup/
mv api_server.py old_backup/
mv batch_translator.py old_backup/

# Or delete them
rm ai_translator.py api_server.py batch_translator.py
```

## 🆕 New Features

### 1. Shared Translator Instance

All apps now share the same core logic:

```python
# In app_streamlit.py
from core.translator import AITranslator
translator = AITranslator()

# In app_api.py
from core.translator import AITranslator
translator = AITranslator()  # Same implementation!
```

### 2. Independent History Management

```python
from core.history import HistoryManager

# Create history manager
history = HistoryManager()

# Add entry
history.add_entry(original_text, translation_result, target_lang)

# Get statistics
stats = history.get_stats()

# Export
json_data = history.export_history('json')
csv_data = history.export_history('csv')

# Clear
history.clear_history()
```

### 3. Standalone Audio Module

```python
from core.audio import AudioManager

audio = AudioManager()

# Generate TTS
audio_file, error = audio.generate_tts_audio("Hello", "en")

# Play audio
success, error = audio.play_audio(audio_file)

# Stop audio
audio.stop_audio()

# Complete workflow
success, error = audio.text_to_speech("Hello", "en")
```

### 4. Caching Utilities

```python
from core.caching import ModelCache

cache = ModelCache()

# Cache a model
cache.set_model("model_name", model_data)

# Get cached model
model = cache.get_model("model_name")

# Cache translation
cache.cache_translation(text, "en", "es", result)

# Get cached translation
cached = cache.get_cached_translation(text, "en", "es")
```

## 🐛 Troubleshooting

### Issue: Import errors

**Error:**
```
ModuleNotFoundError: No module named 'core'
```

**Solution:**
Make sure you're running from the project root directory:
```bash
cd /path/to/ai-language-translator
python run.py web
```

### Issue: Old files still being used

**Solution:**
Check which file is being run:
```bash
# Make sure you're using new files
python app_streamlit.py  # Not ai_translator.py
python app_api.py        # Not api_server.py
python app_batch.py      # Not batch_translator.py
```

### Issue: History not loading

**Solution:**
History files are compatible. They're stored in `translation_history/` and work with both old and new code.

### Issue: Audio not working

**Solution:**
Audio functionality is the same, just moved to `core/audio.py`. If it worked before, it will work now.

## ✅ Verification Checklist

- [ ] Web app runs: `python run.py web`
- [ ] API server runs: `python run.py api`
- [ ] Batch translation works: `python run.py batch test.csv output.csv --text-column "text"`
- [ ] History loads correctly
- [ ] Audio/TTS works
- [ ] No import errors
- [ ] All tests pass (if you have tests)

## 🎓 Learning the New Structure

### Core Library Philosophy

The `core/` directory contains **pure logic** with no UI dependencies:

```
core/
├── translator.py   # Translation algorithms
├── history.py      # Data persistence
├── audio.py        # Audio generation
└── caching.py      # Performance optimization
```

### Application Layer

Applications import from `core/` and add UI/API/CLI:

```
app_streamlit.py    # Streamlit UI
app_api.py          # Flask REST API
app_batch.py        # CLI tool
```

### Benefits

1. **Testability**: Test core logic without UI
2. **Reusability**: Use same logic in multiple apps
3. **Maintainability**: Change one place, affects all apps
4. **Performance**: Shared caches across apps
5. **Clarity**: Each file has one clear purpose

## 🚀 Next Steps

1. **Try the new structure** with your existing workflows
2. **Update any custom scripts** to use new imports
3. **Remove old files** once you're confident
4. **Enjoy cleaner, more maintainable code!**

## 📞 Need Help?

- Check `ARCHITECTURE.md` for detailed documentation
- Review `core/` modules for API reference
- Look at `app_*.py` files for usage examples
- Old files can be kept as reference during transition
