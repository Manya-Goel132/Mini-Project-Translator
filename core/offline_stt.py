"""
Offline Speech-to-Text functionality
Uses CMU PocketSphinx for offline recognition
"""

import speech_recognition as sr
import io
import asyncio
from typing import Optional, Tuple
import tempfile
from pathlib import Path


class OfflineSTTManager:
    """
    Offline speech recognition using PocketSphinx
    """
    
    def __init__(self):
        """Initialize offline speech recognizer"""
        self.recognizer = sr.Recognizer()
        
        # Optimize for offline recognition
        self.recognizer.energy_threshold = 400  # Higher threshold for offline
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0  # Longer pause for offline
        self.recognizer.phrase_threshold = 0.5
        
        self.sphinx_available = self._test_sphinx()
    
    def _test_sphinx(self) -> bool:
        """Test if PocketSphinx is available"""
        try:
            # Try to create a simple recognition
            r = sr.Recognizer()
            # This will fail if sphinx is not installed
            r.recognize_sphinx(sr.AudioData(b'\x00' * 1000, 16000, 2))
            return True
        except (sr.UnknownValueError, sr.RequestError):
            # These are expected for empty audio
            return True
        except Exception:
            # This indicates sphinx is not available
            return False
    
    async def recognize_from_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str = 'en'
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech from audio bytes offline
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code (only 'en' supported offline)
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        if not self.sphinx_available:
            return None, "PocketSphinx not available. Install with: pip install pocketsphinx"
        
        if language != 'en':
            return None, "Offline speech recognition only supports English"
        
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                self._recognize_sync,
                audio_bytes
            )
            return text, None
        except Exception as e:
            return None, f"Offline speech recognition failed: {str(e)}"
    
    def _recognize_sync(self, audio_bytes: bytes) -> str:
        """
        Synchronous offline speech recognition
        
        Args:
            audio_bytes: Audio file bytes
        
        Returns:
            Recognized text
        """
        # Convert audio to WAV if needed
        wav_bytes = self._convert_to_wav(audio_bytes)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(wav_bytes)
            temp_path = temp_file.name
        
        try:
            # Load audio file
            with sr.AudioFile(temp_path) as source:
                # Adjust for ambient noise (longer for offline)
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Record audio
                audio_data = self.recognizer.record(source)
            
            # Recognize using Sphinx (offline)
            text = self.recognizer.recognize_sphinx(audio_data)
            return text
            
        except sr.UnknownValueError:
            raise Exception("Could not understand audio. Try speaking more clearly.")
        except sr.RequestError as e:
            raise Exception(f"Sphinx error: {e}")
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio to WAV format for Sphinx
        
        Args:
            audio_bytes: Raw audio bytes
        
        Returns:
            WAV format audio bytes
        """
        try:
            from pydub import AudioSegment
            
            # Try to load audio
            audio_buffer = io.BytesIO(audio_bytes)
            
            # Try different formats
            for fmt in ['wav', 'webm', 'ogg', 'mp3', 'flac', 'm4a']:
                try:
                    audio_buffer.seek(0)
                    audio = AudioSegment.from_file(audio_buffer, format=fmt)
                    break
                except Exception:
                    continue
            else:
                # Auto-detect format
                audio_buffer.seek(0)
                audio = AudioSegment.from_file(audio_buffer)
            
            # Convert to optimal format for Sphinx
            # 16kHz mono 16-bit PCM WAV
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export to WAV
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format='wav')
            output_buffer.seek(0)
            return output_buffer.read()
            
        except Exception:
            # If conversion fails, assume it's already WAV
            return audio_bytes
    
    def recognize_from_audio_bytes_sync(
        self,
        audio_bytes: bytes,
        language: str = 'en'
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Synchronous version for non-async contexts
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        if not self.sphinx_available:
            return None, "PocketSphinx not available"
        
        if language != 'en':
            return None, "Offline recognition only supports English"
        
        try:
            text = self._recognize_sync(audio_bytes)
            return text, None
        except Exception as e:
            return None, str(e)


class HybridSTTManager:
    """
    Speech recognition that tries offline first, then online
    """
    
    def __init__(self):
        self.offline_stt = OfflineSTTManager()
        
        # Import online STT as fallback
        try:
            from .speech_recognition_async import AsyncSpeechRecognizer
            self.online_stt = AsyncSpeechRecognizer()
        except ImportError:
            self.online_stt = None
    
    async def recognize_from_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        prefer_offline: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech with offline preference
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
            prefer_offline: Try offline first
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        if prefer_offline and language == 'en' and self.offline_stt.sphinx_available:
            # Try offline first for English
            text, error = await self.offline_stt.recognize_from_audio_bytes(
                audio_bytes, language
            )
            if text:
                return text, None
        
        # Fall back to online recognition
        if self.online_stt:
            return await self.online_stt.recognize_from_audio_bytes(
                audio_bytes, language, 'google'
            )
        
        return None, "No speech recognition engines available"
    
    def recognize_from_audio_bytes_sync(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        prefer_offline: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Synchronous version with offline preference
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
            prefer_offline: Try offline first
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        if prefer_offline and language == 'en' and self.offline_stt.sphinx_available:
            # Try offline first
            text, error = self.offline_stt.recognize_from_audio_bytes_sync(
                audio_bytes, language
            )
            if text:
                return text, None
        
        # Fall back to online
        if self.online_stt:
            return self.online_stt.recognize_from_audio_bytes_sync(
                audio_bytes, language, 'google'
            )
        
        return None, "No speech recognition engines available"
    
    def get_engine_info(self) -> dict:
        """Get information about available engines"""
        info = {
            'offline_sphinx': {
                'available': self.offline_stt.sphinx_available,
                'description': 'CMU PocketSphinx (offline)',
                'languages': 'English only',
                'quality': 'Basic',
                'privacy': 'Excellent (local only)'
            }
        }
        
        if self.online_stt:
            online_info = {
                'online_google': {
                    'available': True,
                    'description': 'Google Speech Recognition (online)',
                    'languages': '100+ languages',
                    'quality': 'Excellent',
                    'privacy': 'Limited (sent to Google)'
                }
            }
            info.update(online_info)
        
        return info


class OfflineStreamlitSTT:
    """
    Streamlit wrapper for offline speech recognition
    """
    
    def __init__(self):
        self.hybrid_stt = HybridSTTManager()
    
    def recognize_from_file(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        engine: str = 'auto'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Recognize speech from uploaded audio file
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
            engine: 'offline', 'online', or 'auto'
        
        Returns:
            Tuple of (success, recognized_text, error_message)
        """
        if not audio_bytes:
            return False, None, "No audio data provided"
        
        if len(audio_bytes) < 1000:
            return False, None, "Audio too short"
        
        prefer_offline = engine in ['offline', 'auto']
        
        text, error = self.hybrid_stt.recognize_from_audio_bytes_sync(
            audio_bytes, language, prefer_offline
        )
        
        if error:
            return False, None, error
        
        if not text or not text.strip():
            return False, None, "No speech detected"
        
        return True, text.strip(), None
    
    def get_supported_languages(self) -> dict:
        """Get supported languages"""
        return {
            'en': 'en-US'  # Only English for offline
        }
    
    def get_supported_engines(self) -> list:
        """Get supported engines"""
        engines = ['auto']
        if self.hybrid_stt.offline_stt.sphinx_available:
            engines.append('offline')
        if self.hybrid_stt.online_stt:
            engines.append('online')
        return engines
    
    def get_engine_info(self) -> dict:
        """Get engine information"""
        return self.hybrid_stt.get_engine_info()