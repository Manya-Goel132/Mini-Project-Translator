# Quick Reference Card

## 🚀 Running Applications

```bash
# Web Application
python run.py web

# API Server
python run.py api

# Batch Translation
python run.py batch input.csv output.csv --text-column "text" --target-lang "es"

# Install Dependencies
python run.py install

# Check Dependencies
python run.py check

# Run Tests
python test_refactoring.py
```

## 📚 Core Library Imports

```python
# Translation
from core.translator import AITranslator

# History Management
from core.history import HistoryManager

# Audio/TTS
from core.audio import AudioManager

# Caching
from core.caching import ModelCache
```

## 🔧 Common Usage Patterns

### Basic Translation
```python
from core.translator import AITranslator

translator = AITranslator()
result = translator.smart_translate("Hello", "en", "es")
print(result['translation'])  # "Hola"
```

### With History
```python
from core.translator import AITranslator
from core.history import HistoryManager

translator = AITranslator()
history = HistoryManager()

result = translator.smart_translate("Hello", "en", "es")
history.add_entry("Hello", result, "es")
```

### With Audio
```python
from core.translator import AITranslator
from core.audio import AudioManager

translator = AITranslator()
audio = AudioManager()

result = translator.smart_translate("Hello", "en", "es")
audio.text_to_speech(result['translation'], "es")
```

### Complete Workflow
```python
from core.translator import AITranslator
from core.history import HistoryManager
from core.audio import AudioManager

# Initialize
translator = AITranslator()
history = HistoryManager()
audio = AudioManager()

# Translate
result = translator.smart_translate("Hello world", "en", "es")

# Save to history
history.add_entry("Hello world", result, "es")

# Play audio
audio.text_to_speech(result['translation'], "es")

# Get statistics
stats = history.get_stats()
print(f"Total translations: {stats['total_translations']}")
```

## 📖 API Endpoints

```bash
# Translate text
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_lang": "en", "target_lang": "es"}'

# Detect language
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour"}'

# Get supported languages
curl http://localhost:5000/api/languages

# Batch translate
curl -X POST http://localhost:5000/api/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello", "World"], "target_lang": "es"}'

# Health check
curl http://localhost:5000/health
```

## 🗂️ File Structure

```
core/
├── translator.py    # Translation logic
├── history.py       # History management
├── audio.py         # TTS functionality
└── caching.py       # Caching utilities

app_streamlit.py     # Web UI
app_api.py           # REST API
app_batch.py         # Batch tool
run.py               # Runner script
```

## 🧪 Testing

```python
# Run all tests
python test_refactoring.py

# Test specific module
from core.translator import AITranslator
translator = AITranslator()
assert translator.detect_language("Hello")[0] == "en"
```

## 📊 Batch Translation Examples

```bash
# CSV file
python run.py batch data.csv output.csv \
  --text-column "description" \
  --target-lang "es"

# JSON file
python run.py batch content.json output.json \
  --text-fields "title" "body" \
  --target-lang "fr"

# Text file
python run.py batch document.txt translated.txt \
  --source-lang "en" \
  --target-lang "de"
```

## 🌍 Supported Languages

```
en - English      es - Spanish      fr - French
de - German       it - Italian      pt - Portuguese
ru - Russian      ja - Japanese     ko - Korean
zh - Chinese      ar - Arabic       hi - Hindi
nl - Dutch        sv - Swedish      da - Danish
no - Norwegian    fi - Finnish      pl - Polish
tr - Turkish      th - Thai
```

## 🔍 Troubleshooting

```bash
# Import errors
# Make sure you're in the project root directory

# Audio not working
# Check if pygame is installed: pip install pygame

# API not starting
# Check if port 5000 is available

# Tests failing
# Run: python run.py install
```

## 📚 Documentation Files

- `ARCHITECTURE.md` - Detailed architecture
- `MIGRATION_GUIDE.md` - Migration instructions
- `REFACTORING_SUMMARY.md` - Summary of changes
- `BEFORE_AFTER.md` - Visual comparison
- `QUICK_REFERENCE.md` - This file

## 💡 Tips

1. Use `run.py` for all operations
2. Import from `core/` in custom scripts
3. Check `test_refactoring.py` for examples
4. Read `ARCHITECTURE.md` for deep dive
5. See `MIGRATION_GUIDE.md` for migration help

## 🎯 Common Tasks

### Add New Translation Method
Edit `core/translator.py` → Add method → All apps benefit

### Change History Storage
Edit `core/history.py` → Modify save/load → All apps benefit

### Update TTS Engine
Edit `core/audio.py` → Change implementation → All apps benefit

### Add New Application
Create `app_new.py` → Import from `core/` → Done!

---

**Keep this file handy for quick reference!** 📌
