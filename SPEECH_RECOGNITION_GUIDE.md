# 🎤 Speech Recognition Guide

## Overview

The AI Translator now includes **Speech-to-Text (STT)** functionality, allowing you to:
- Upload audio files and convert them to text
- Use microphone input (Streamlit)
- Support multiple languages
- Multiple recognition engines (Google, Sphinx, Wit.ai)

---

## Features

### ✅ What's Included

- **Audio File Recognition**: Upload WAV, MP3, FLAC, etc.
- **Multiple Engines**: Google (default), Sphinx (offline), Wit.ai
- **20+ Languages**: Same languages as translation
- **Async Support**: Non-blocking recognition in FastAPI
- **Streamlit Integration**: Easy audio upload widget

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies:
- `SpeechRecognition>=3.10.0` - Speech recognition library
- `pydub>=0.25.1` - Audio processing

### 2. Test Speech Recognition

```bash
# Start FastAPI server
uvicorn api_server_fastapi:app --port 8000

# Test with audio file
curl -X POST http://localhost:8000/api/stt \
  -H "Content-Type: audio/wav" \
  --data-binary @test_audio.wav

# Response:
{
  "success": true,
  "text": "Hello world",
  "language": "en",
  "engine": "google"
}
```

---

## API Usage

### FastAPI Endpoint

**POST /api/stt**

Upload audio file and get recognized text.

**Request**:
```bash
curl -X POST http://localhost:8000/api/stt \
  -H "Content-Type: audio/wav" \
  --data-binary @audio.wav \
  -G \
  -d "language=en" \
  -d "engine=google"
```

**Response**:
```json
{
  "success": true,
  "text": "Hello world, this is a test",
  "language": "en",
  "engine": "google"
}
```

**Parameters**:
- `audio` (required): Audio file bytes
- `language` (optional): Language code (default: "en")
- `engine` (optional): Recognition engine (default: "google")

**Supported Formats**:
- WAV (recommended)
- MP3
- FLAC
- OGG
- And more...

---

## Python Usage

### Async (FastAPI)

```python
from core.speech_recognition_async import AsyncSpeechRecognizer

recognizer = AsyncSpeechRecognizer()

# From audio bytes
with open('audio.wav', 'rb') as f:
    audio_bytes = f.read()

text, error = await recognizer.recognize_from_audio_bytes(
    audio_bytes,
    language='en',
    engine='google'
)

if text:
    print(f"Recognized: {text}")
else:
    print(f"Error: {error}")
```

### Sync (Streamlit)

```python
from core.speech_recognition_async import StreamlitSpeechRecognizer
import streamlit as st

recognizer = StreamlitSpeechRecognizer()

# Audio file uploader
audio_file = st.file_uploader("Upload audio", type=['wav', 'mp3', 'flac'])

if audio_file:
    audio_bytes = audio_file.read()
    
    success, text, error = recognizer.recognize_from_file(
        audio_bytes,
        language='en',
        engine='google'
    )
    
    if success:
        st.success(f"Recognized: {text}")
    else:
        st.error(f"Error: {error}")
```

---

## Supported Languages

Same as translation:

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | es | Spanish |
| fr | French | de | German |
| it | Italian | pt | Portuguese |
| ru | Russian | ja | Japanese |
| ko | Korean | zh | Chinese |
| ar | Arabic | hi | Hindi |
| nl | Dutch | sv | Swedish |
| da | Danish | no | Norwegian |
| fi | Finnish | pl | Polish |
| tr | Turkish | th | Thai |

---

## Recognition Engines

### 1. Google Speech Recognition (Default)

**Pros**:
- ✅ High accuracy
- ✅ 100+ languages
- ✅ Free (with limits)
- ✅ No API key needed

**Cons**:
- ❌ Requires internet
- ❌ Rate limited

**Usage**:
```python
text, error = await recognizer.recognize_from_audio_bytes(
    audio_bytes,
    language='en',
    engine='google'  # Default
)
```

### 2. CMU Sphinx (Offline)

**Pros**:
- ✅ Works offline
- ✅ No rate limits
- ✅ Free

**Cons**:
- ❌ Lower accuracy
- ❌ Limited languages
- ❌ Requires installation

**Installation**:
```bash
# macOS
brew install swig portaudio
pip install pocketsphinx

# Linux
sudo apt-get install swig libpulse-dev
pip install pocketsphinx
```

**Usage**:
```python
text, error = await recognizer.recognize_from_audio_bytes(
    audio_bytes,
    language='en',
    engine='sphinx'
)
```

### 3. Wit.ai

**Pros**:
- ✅ Good accuracy
- ✅ Free
- ✅ Multiple languages

**Cons**:
- ❌ Requires API key
- ❌ Requires internet

**Setup**:
```bash
# Get API key from https://wit.ai
export WIT_AI_KEY="your_key_here"
```

**Usage**:
```python
text, error = await recognizer.recognize_from_audio_bytes(
    audio_bytes,
    language='en',
    engine='wit'
)
```

---

## Complete Workflow Example

### Voice Translation Pipeline

```python
from core.speech_recognition_async import AsyncSpeechRecognizer
from core.translator import AITranslator
from core.audio_async import AsyncAudioManager

# Initialize components
stt = AsyncSpeechRecognizer()
translator = AITranslator()
tts = AsyncAudioManager()

# 1. Speech to Text
with open('input_audio.wav', 'rb') as f:
    audio_bytes = f.read()

text, error = await stt.recognize_from_audio_bytes(audio_bytes, language='en')
print(f"Recognized: {text}")

# 2. Translate
result = translator.smart_translate(text, 'en', 'es')
print(f"Translated: {result['translation']}")

# 3. Text to Speech
audio_bytes, error = await tts.generate_audio_bytes(
    result['translation'],
    language='es'
)

# 4. Save output
with open('output_audio.mp3', 'wb') as f:
    f.write(audio_bytes)

print("Voice translation complete!")
```

---

## Streamlit Integration

### Complete Voice Translation App

```python
import streamlit as st
from core.speech_recognition_async import StreamlitSpeechRecognizer
from core.translator import AITranslator
from core.audio_async import StreamlitAudioManager

st.title("🎤 Voice Translator")

# Initialize
stt = StreamlitSpeechRecognizer()
translator = AITranslator()
tts = StreamlitAudioManager()

# Language selection
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("Source Language", ['en', 'es', 'fr', 'de'])
with col2:
    target_lang = st.selectbox("Target Language", ['en', 'es', 'fr', 'de'])

# Audio upload
audio_file = st.file_uploader("Upload audio", type=['wav', 'mp3', 'flac'])

if audio_file:
    # Show original audio
    st.audio(audio_file, format='audio/wav')
    
    # Recognize speech
    with st.spinner("Recognizing speech..."):
        audio_bytes = audio_file.read()
        success, text, error = stt.recognize_from_file(
            audio_bytes,
            language=source_lang
        )
    
    if success:
        st.success(f"Recognized: {text}")
        
        # Translate
        with st.spinner("Translating..."):
            result = translator.smart_translate(text, source_lang, target_lang)
        
        if result:
            st.success(f"Translation: {result['translation']}")
            
            # Generate audio
            with st.spinner("Generating audio..."):
                success, error, audio_bytes = tts.text_to_speech(
                    result['translation'],
                    target_lang
                )
            
            if success:
                st.audio(audio_bytes, format='audio/mp3')
            else:
                st.error(error)
    else:
        st.error(error)
```

---

## Audio Format Requirements

### Recommended Format

**WAV (PCM)**:
- Sample rate: 16000 Hz or 44100 Hz
- Channels: Mono (1 channel)
- Bit depth: 16-bit
- Format: PCM

### Converting Audio

**Using ffmpeg**:
```bash
# Convert to WAV
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav

# Convert to optimal format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

**Using pydub (Python)**:
```python
from pydub import AudioSegment

# Load audio
audio = AudioSegment.from_file("input.mp3")

# Convert to mono, 16kHz
audio = audio.set_channels(1)
audio = audio.set_frame_rate(16000)

# Export as WAV
audio.export("output.wav", format="wav")
```

---

## Error Handling

### Common Errors

**1. "Could not understand audio"**
- Audio quality is poor
- Background noise
- Wrong language selected

**Solution**:
```python
try:
    text, error = await recognizer.recognize_from_audio_bytes(...)
    if error:
        # Try different engine
        text, error = await recognizer.recognize_from_audio_bytes(
            audio_bytes,
            language='en',
            engine='sphinx'  # Try offline engine
        )
except Exception as e:
    print(f"Recognition failed: {e}")
```

**2. "Recognition service error"**
- No internet connection (Google, Wit.ai)
- Rate limit exceeded
- API key invalid (Wit.ai)

**Solution**:
```python
# Use offline engine
text, error = await recognizer.recognize_from_audio_bytes(
    audio_bytes,
    language='en',
    engine='sphinx'  # Works offline
)
```

**3. "Audio format not supported"**
- Unsupported audio format
- Corrupted file

**Solution**:
```python
# Convert to WAV first
from pydub import AudioSegment

audio = AudioSegment.from_file("input.mp3")
audio.export("temp.wav", format="wav")

with open("temp.wav", "rb") as f:
    audio_bytes = f.read()
```

---

## Performance Tips

### 1. Audio Quality

- Use WAV format for best results
- 16kHz sample rate is optimal
- Mono channel is sufficient
- Minimize background noise

### 2. Recognition Speed

| Engine | Speed | Accuracy |
|--------|-------|----------|
| Google | Fast (1-2s) | High |
| Sphinx | Very Fast (<1s) | Medium |
| Wit.ai | Fast (1-2s) | High |

### 3. Batch Processing

```python
# Process multiple audio files
audio_files = ['audio1.wav', 'audio2.wav', 'audio3.wav']

results = []
for audio_file in audio_files:
    with open(audio_file, 'rb') as f:
        audio_bytes = f.read()
    
    text, error = await recognizer.recognize_from_audio_bytes(
        audio_bytes,
        language='en'
    )
    
    results.append({
        'file': audio_file,
        'text': text,
        'error': error
    })
```

---

## Testing

### Test Audio Files

Create test audio:
```bash
# macOS - Record audio
say "Hello world, this is a test" -o test.aiff
ffmpeg -i test.aiff -ar 16000 -ac 1 test.wav

# Linux - Record from microphone
arecord -d 5 -f cd -t wav test.wav
```

### Test Script

```python
import asyncio
from core.speech_recognition_async import AsyncSpeechRecognizer

async def test_stt():
    recognizer = AsyncSpeechRecognizer()
    
    # Test with audio file
    with open('test.wav', 'rb') as f:
        audio_bytes = f.read()
    
    # Test Google
    text, error = await recognizer.recognize_from_audio_bytes(
        audio_bytes,
        language='en',
        engine='google'
    )
    
    print(f"Google: {text if text else error}")
    
    # Test Sphinx (if installed)
    try:
        text, error = await recognizer.recognize_from_audio_bytes(
            audio_bytes,
            language='en',
            engine='sphinx'
        )
        print(f"Sphinx: {text if text else error}")
    except:
        print("Sphinx not available")

# Run test
asyncio.run(test_stt())
```

---

## Troubleshooting

### Installation Issues

**PyAudio not installing**:
```bash
# macOS
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

**Sphinx not working**:
```bash
# Install dependencies
pip install pocketsphinx

# Download language models
python -m speech_recognition
```

### Runtime Issues

**"No module named 'speech_recognition'"**:
```bash
pip install SpeechRecognition
```

**"Could not find PyAudio"**:
```bash
# Not required for file-based recognition
# Only needed for microphone input
```

---

## Summary

### What You Get

- ✅ **Speech-to-Text**: Convert audio to text
- ✅ **Multiple Engines**: Google, Sphinx, Wit.ai
- ✅ **20+ Languages**: Same as translation
- ✅ **Async Support**: Non-blocking in FastAPI
- ✅ **Streamlit Ready**: Easy integration
- ✅ **Complete Pipeline**: STT → Translate → TTS

### Use Cases

1. **Voice Translation**: Speak in one language, hear in another
2. **Audio Transcription**: Convert audio files to text
3. **Accessibility**: Voice input for translation
4. **Multilingual Support**: Recognize 20+ languages

### Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Test API: `curl -X POST http://localhost:8000/api/stt --data-binary @audio.wav`
3. Try Streamlit: Add audio uploader to your app
4. Build voice translation: Combine STT + Translation + TTS

**Your translator now supports voice input! 🎤✨**
