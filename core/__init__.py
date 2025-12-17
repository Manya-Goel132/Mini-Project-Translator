"""
AI Language Translator - Core Library
Provides translation, history management, audio, and caching functionality
"""

from .translator import AITranslator
from .history import HistoryManager
from .audio import AudioManager
from .audio_async import AsyncAudioManager, StreamlitAudioManager
from .caching import ModelCache, SharedModelCache

# Optional speech recognition (requires SpeechRecognition package)
try:
    from .speech_recognition_async import AsyncSpeechRecognizer, StreamlitSpeechRecognizer
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    AsyncSpeechRecognizer = None
    StreamlitSpeechRecognizer = None

__all__ = [
    'AITranslator', 
    'HistoryManager', 
    'AudioManager',
    'AsyncAudioManager',
    'StreamlitAudioManager', 
    'ModelCache',
    'SharedModelCache',
    'AsyncSpeechRecognizer',
    'StreamlitSpeechRecognizer',
    'SPEECH_AVAILABLE'
]
__version__ = '2.0.0'
