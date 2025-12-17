"""Unit tests for speech recognition module"""

import pytest
from pathlib import Path


# Check if speech recognition is available
try:
    from core.speech_recognition_async import AsyncSpeechRecognizer, StreamlitSpeechRecognizer
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False


@pytest.mark.skipif(not SPEECH_AVAILABLE, reason="SpeechRecognition not installed")
class TestAsyncSpeechRecognizer:
    """Tests for AsyncSpeechRecognizer"""
    
    @pytest.fixture
    def recognizer(self):
        return AsyncSpeechRecognizer()
    
    def test_init(self, recognizer):
        assert recognizer is not None
        assert recognizer.recognizer is not None
    
    def test_supported_languages(self, recognizer):
        langs = recognizer.supported_languages
        assert len(langs) > 0
        assert 'en' in langs
        assert 'es' in langs
        assert 'fr' in langs
        assert langs['en'] == 'en-US'
    
    def test_recognizer_settings(self, recognizer):
        """Test that recognizer has optimized settings"""
        assert recognizer.recognizer.energy_threshold > 0
        assert recognizer.recognizer.dynamic_energy_threshold is True
        assert recognizer.recognizer.pause_threshold > 0
    
    def test_convert_audio_empty(self, recognizer):
        """Test audio conversion with empty bytes"""
        result = recognizer._convert_audio_to_wav(b'')
        # Should return original bytes if conversion fails
        assert result == b''
    
    def test_recognize_empty_audio(self, recognizer):
        """Test recognition with empty audio"""
        text, error = recognizer.recognize_from_audio_bytes_sync(b'', 'en', 'google')
        assert text is None
        assert error is not None


@pytest.mark.skipif(not SPEECH_AVAILABLE, reason="SpeechRecognition not installed")
class TestStreamlitSpeechRecognizer:
    """Tests for StreamlitSpeechRecognizer"""
    
    @pytest.fixture
    def recognizer(self):
        return StreamlitSpeechRecognizer()
    
    def test_init(self, recognizer):
        assert recognizer is not None
        assert recognizer.async_recognizer is not None
    
    def test_get_supported_languages(self, recognizer):
        langs = recognizer.get_supported_languages()
        assert isinstance(langs, dict)
        assert len(langs) > 20
        assert 'en' in langs
    
    def test_get_supported_engines(self, recognizer):
        engines = recognizer.get_supported_engines()
        assert isinstance(engines, list)
        assert 'google' in engines
        assert 'sphinx' in engines
    
    def test_get_engine_info(self, recognizer):
        info = recognizer.get_engine_info()
        assert isinstance(info, dict)
        assert 'google' in info
        assert 'name' in info['google']
        assert 'requires_key' in info['google']
    
    def test_recognize_no_audio(self, recognizer):
        """Test recognition with no audio data"""
        success, text, error = recognizer.recognize_from_file(None, 'en', 'google')
        assert success is False
        assert text is None
        assert error is not None
    
    def test_recognize_short_audio(self, recognizer):
        """Test recognition with too short audio"""
        success, text, error = recognizer.recognize_from_file(b'short', 'en', 'google')
        assert success is False
        assert "too short" in error.lower()


@pytest.mark.skipif(not SPEECH_AVAILABLE, reason="SpeechRecognition not installed")
class TestAudioConversion:
    """Tests for audio format conversion"""
    
    @pytest.fixture
    def recognizer(self):
        return AsyncSpeechRecognizer()
    
    def test_wav_passthrough(self, recognizer):
        """Test that valid WAV audio is processed"""
        # Create a minimal WAV header (44 bytes) + some audio data
        wav_header = b'RIFF' + b'\x00' * 4 + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00'
        wav_header += b'\x01\x00\x01\x00'  # PCM, mono
        wav_header += b'\x80\x3e\x00\x00'  # 16000 Hz
        wav_header += b'\x00\x7d\x00\x00'  # byte rate
        wav_header += b'\x02\x00\x10\x00'  # block align, bits per sample
        wav_header += b'data' + b'\x00' * 4
        
        # This should attempt conversion
        result = recognizer._convert_audio_to_wav(wav_header + b'\x00' * 1000)
        assert result is not None
