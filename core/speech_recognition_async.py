"""
Async Speech-to-Text (STT) functionality
Supports multiple recognition engines with improved accuracy
"""

import speech_recognition as sr
import io
import asyncio
from typing import Optional, Tuple, List
from pathlib import Path
import tempfile
import os


class AsyncSpeechRecognizer:
    """
    Async speech recognition manager
    Supports multiple engines: Google, Sphinx, Wit.ai, etc.
    """
    
    def __init__(self):
        """Initialize speech recognizer with optimized settings"""
        self.recognizer = sr.Recognizer()
        
        # Optimize recognizer settings for better accuracy
        self.recognizer.energy_threshold = 300  # Minimum audio energy to consider for recording
        self.recognizer.dynamic_energy_threshold = True  # Automatically adjust for ambient noise
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # Seconds of silence before phrase is complete
        self.recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking before phrase starts
        self.recognizer.non_speaking_duration = 0.5  # Seconds of silence to keep before/after phrase
        
        # Supported languages for Google Speech Recognition
        self.supported_languages = {
            'en': 'en-US',
            'en-gb': 'en-GB',
            'en-au': 'en-AU',
            'es': 'es-ES',
            'es-mx': 'es-MX',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'pt-br': 'pt-BR',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'zh': 'zh-CN',
            'zh-tw': 'zh-TW',
            'ar': 'ar-SA',
            'hi': 'hi-IN',
            'nl': 'nl-NL',
            'sv': 'sv-SE',
            'da': 'da-DK',
            'no': 'no-NO',
            'fi': 'fi-FI',
            'pl': 'pl-PL',
            'tr': 'tr-TR',
            'th': 'th-TH',
            'vi': 'vi-VN',
            'id': 'id-ID',
            'ms': 'ms-MY',
            'uk': 'uk-UA',
            'cs': 'cs-CZ',
            'el': 'el-GR',
            'he': 'he-IL',
            'hu': 'hu-HU',
            'ro': 'ro-RO'
        }
    
    def _convert_audio_to_wav(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio to WAV format using pydub for better compatibility
        
        Args:
            audio_bytes: Raw audio bytes (any format)
        
        Returns:
            WAV format audio bytes
        """
        try:
            from pydub import AudioSegment
            
            # Try to detect format and convert
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
                # Last resort: try auto-detection
                audio_buffer.seek(0)
                audio = AudioSegment.from_file(audio_buffer)
            
            # Convert to optimal format for speech recognition
            # 16kHz mono 16-bit PCM WAV is ideal
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export to WAV
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format='wav')
            output_buffer.seek(0)
            return output_buffer.read()
            
        except Exception as e:
            # If conversion fails, return original bytes
            print(f"Audio conversion warning: {e}")
            return audio_bytes
    
    async def recognize_from_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        engine: str = 'google',
        show_all: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech from audio bytes (async)
        
        Args:
            audio_bytes: Audio file bytes (WAV, MP3, WebM, etc.)
            language: Language code
            engine: Recognition engine ('google', 'google_cloud', 'sphinx', 'wit')
            show_all: Return all possible transcriptions (Google only)
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        try:
            # Run recognition in thread pool (speech_recognition is blocking)
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                self._recognize_sync,
                audio_bytes,
                language,
                engine,
                show_all
            )
            
            return text, None
            
        except Exception as e:
            return None, f"Speech recognition failed: {str(e)}"
    
    def _recognize_sync(
        self,
        audio_bytes: bytes,
        language: str,
        engine: str,
        show_all: bool = False
    ) -> str:
        """
        Synchronous speech recognition (called in thread pool)
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
            engine: Recognition engine
            show_all: Return all transcriptions
        
        Returns:
            Recognized text
        """
        # Convert audio to WAV for better compatibility
        wav_bytes = self._convert_audio_to_wav(audio_bytes)
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(wav_bytes)
            temp_path = temp_file.name
        
        try:
            # Load audio file
            with sr.AudioFile(temp_path) as source:
                # Adjust for ambient noise (shorter duration for converted audio)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Record entire audio
                audio_data = self.recognizer.record(source)
            
            # Map language code
            lang_code = self.supported_languages.get(language, 'en-US')
            
            # Recognize based on engine
            if engine == 'google':
                result = self.recognizer.recognize_google(
                    audio_data, 
                    language=lang_code,
                    show_all=show_all
                )
                if show_all and isinstance(result, dict):
                    # Return best transcription
                    alternatives = result.get('alternative', [])
                    if alternatives:
                        return alternatives[0].get('transcript', '')
                return result
                
            elif engine == 'google_cloud':
                # Requires GOOGLE_APPLICATION_CREDENTIALS env var
                credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if credentials_json:
                    return self.recognizer.recognize_google_cloud(
                        audio_data,
                        language=lang_code,
                        credentials_json=credentials_json
                    )
                else:
                    # Fall back to free Google API
                    return self.recognizer.recognize_google(audio_data, language=lang_code)
                    
            elif engine == 'sphinx':
                # Offline recognition (English only, less accurate)
                return self.recognizer.recognize_sphinx(audio_data)
                
            elif engine == 'wit':
                # Requires WIT_AI_KEY environment variable
                wit_key = os.environ.get('WIT_AI_KEY')
                if wit_key:
                    return self.recognizer.recognize_wit(audio_data, key=wit_key)
                else:
                    raise Exception("WIT_AI_KEY environment variable not set")
            else:
                # Default to Google
                return self.recognizer.recognize_google(audio_data, language=lang_code)
            
        except sr.UnknownValueError:
            raise Exception("Could not understand audio. Please speak clearly and try again.")
        except sr.RequestError as e:
            raise Exception(f"Recognition service error: {e}")
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    def recognize_from_audio_bytes_sync(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        engine: str = 'google'
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Synchronous version for non-async contexts (e.g., Streamlit)
        
        Args:
            audio_bytes: Audio file bytes
            language: Language code
            engine: Recognition engine
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        try:
            text = self._recognize_sync(audio_bytes, language, engine)
            return text, None
        except Exception as e:
            return None, str(e)
    
    async def recognize_from_microphone(
        self,
        language: str = 'en',
        engine: str = 'google',
        timeout: int = 10,
        phrase_time_limit: int = 30
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech from microphone (async)
        
        Args:
            language: Language code
            engine: Recognition engine
            timeout: Max seconds to wait for speech to start
            phrase_time_limit: Max seconds for the phrase
        
        Returns:
            Tuple of (recognized_text, error_message)
        """
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                self._recognize_from_mic_sync,
                language,
                engine,
                timeout,
                phrase_time_limit
            )
            
            return text, None
            
        except Exception as e:
            return None, f"Microphone recognition failed: {str(e)}"
    
    def _recognize_from_mic_sync(
        self,
        language: str,
        engine: str,
        timeout: int,
        phrase_time_limit: int
    ) -> str:
        """
        Synchronous microphone recognition
        
        Args:
            language: Language code
            engine: Recognition engine
            timeout: Recording timeout
            phrase_time_limit: Max phrase duration
        
        Returns:
            Recognized text
        """
        with sr.Microphone() as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Listen for audio with timeout
            audio_data = self.recognizer.listen(
                source, 
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
        
        # Map language code
        lang_code = self.supported_languages.get(language, 'en-US')
        
        # Recognize based on engine
        if engine == 'google':
            return self.recognizer.recognize_google(audio_data, language=lang_code)
        elif engine == 'sphinx':
            return self.recognizer.recognize_sphinx(audio_data)
        elif engine == 'wit':
            wit_key = os.environ.get('WIT_AI_KEY')
            if wit_key:
                return self.recognizer.recognize_wit(audio_data, key=wit_key)
            raise Exception("WIT_AI_KEY not set")
        else:
            return self.recognizer.recognize_google(audio_data, language=lang_code)


class StreamlitSpeechRecognizer:
    """
    Wrapper for Streamlit that handles audio file uploads
    Optimized for browser-recorded audio (WebM format)
    """
    
    def __init__(self):
        """Initialize Streamlit speech recognizer"""
        self.async_recognizer = AsyncSpeechRecognizer()
    
    def recognize_from_file(
        self,
        audio_bytes: bytes,
        language: str = 'en',
        engine: str = 'google'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Recognize speech from uploaded audio file
        
        Args:
            audio_bytes: Audio file bytes (supports WAV, WebM, MP3, etc.)
            language: Language code
            engine: Recognition engine
        
        Returns:
            Tuple of (success, recognized_text, error_message)
        """
        if not audio_bytes:
            return False, None, "No audio data provided"
        
        if len(audio_bytes) < 1000:
            return False, None, "Audio too short. Please record at least 1 second."
        
        text, error = self.async_recognizer.recognize_from_audio_bytes_sync(
            audio_bytes, language, engine
        )
        
        if error:
            return False, None, error
        
        if not text or not text.strip():
            return False, None, "No speech detected in audio"
        
        return True, text.strip(), None
    
    def get_supported_languages(self) -> dict:
        """Get supported languages"""
        return self.async_recognizer.supported_languages
    
    def get_supported_engines(self) -> List[str]:
        """Get supported recognition engines"""
        return ['google', 'google_cloud', 'sphinx', 'wit']
    
    def get_engine_info(self) -> dict:
        """Get information about available engines"""
        return {
            'google': {
                'name': 'Google Speech Recognition',
                'description': 'Free, accurate, requires internet',
                'languages': 'All supported languages',
                'requires_key': False
            },
            'google_cloud': {
                'name': 'Google Cloud Speech-to-Text',
                'description': 'Premium accuracy, requires API key',
                'languages': 'All supported languages',
                'requires_key': True,
                'env_var': 'GOOGLE_APPLICATION_CREDENTIALS'
            },
            'sphinx': {
                'name': 'CMU Sphinx',
                'description': 'Offline, English only, less accurate',
                'languages': 'English only',
                'requires_key': False
            },
            'wit': {
                'name': 'Wit.ai',
                'description': 'Facebook/Meta service, requires API key',
                'languages': 'Multiple languages',
                'requires_key': True,
                'env_var': 'WIT_AI_KEY'
            }
        }
