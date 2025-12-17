"""
Async Text-to-Speech audio management
No temp files, no pygame dependency, streaming audio bytes
"""

from gtts import gTTS
import io
from pathlib import Path
import asyncio
from typing import Optional, Tuple


class AsyncAudioManager:
    """
    Async audio manager that generates TTS audio in-memory
    No temp files, no pygame, perfect for web APIs
    """
    
    def __init__(self):
        """Initialize async audio manager"""
        self.tts_lang_map = {
            'zh': 'zh-CN', 'ja': 'ja', 'ko': 'ko', 'ar': 'ar',
            'hi': 'hi', 'th': 'th', 'cs': 'cs', 'hu': 'hu',
            'ro': 'ro', 'bg': 'bg', 'hr': 'hr', 'sk': 'sk',
            'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de',
            'it': 'it', 'pt': 'pt', 'ru': 'ru', 'nl': 'nl',
            'sv': 'sv', 'da': 'da', 'no': 'no', 'fi': 'fi',
            'pl': 'pl', 'tr': 'tr'
        }
    
    async def generate_audio_bytes(
        self, 
        text: str, 
        language: str = 'en',
        max_length: int = 1000,
        slow: bool = False
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate TTS audio as bytes (in-memory, no temp files)
        
        Args:
            text: Text to convert to speech
            language: Language code
            max_length: Maximum text length
            slow: Slow speech rate
        
        Returns:
            Tuple of (audio_bytes, error_message)
        """
        try:
            # Validate and truncate text
            if not text or not text.strip():
                return None, "Text cannot be empty"
            
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Map language for gTTS
            tts_lang = self.tts_lang_map.get(language, 'en')
            
            # Generate TTS in thread pool (gTTS is blocking)
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None,
                self._generate_tts_sync,
                text,
                tts_lang,
                slow
            )
            
            return audio_bytes, None
            
        except Exception as e:
            return None, f"TTS generation failed: {str(e)}"
    
    def _generate_tts_sync(self, text: str, language: str, slow: bool) -> bytes:
        """
        Synchronous TTS generation (called in thread pool)
        
        Args:
            text: Text to convert
            language: Language code
            slow: Slow speech rate
        
        Returns:
            Audio bytes
        """
        try:
            # Create TTS object
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # Write to in-memory buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            
            # Get bytes
            audio_buffer.seek(0)
            return audio_buffer.read()
            
        except Exception as e:
            # Fallback to English
            try:
                tts = gTTS(text=text, lang='en', slow=slow)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                return audio_buffer.read()
            except:
                raise e
    
    def generate_audio_bytes_sync(
        self,
        text: str,
        language: str = 'en',
        max_length: int = 1000,
        slow: bool = False
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Synchronous version for non-async contexts (e.g., Streamlit)
        
        Args:
            text: Text to convert to speech
            language: Language code
            max_length: Maximum text length
            slow: Slow speech rate
        
        Returns:
            Tuple of (audio_bytes, error_message)
        """
        try:
            # Validate and truncate text
            if not text or not text.strip():
                return None, "Text cannot be empty"
            
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Map language for gTTS
            tts_lang = self.tts_lang_map.get(language, 'en')
            
            # Generate TTS
            audio_bytes = self._generate_tts_sync(text, tts_lang, slow)
            
            return audio_bytes, None
            
        except Exception as e:
            return None, f"TTS generation failed: {str(e)}"


# Backward compatibility wrapper for Streamlit
class StreamlitAudioManager:
    """
    Wrapper for Streamlit that provides audio bytes for st.audio()
    No temp files, no pygame
    """
    
    def __init__(self):
        """Initialize Streamlit audio manager"""
        self.async_manager = AsyncAudioManager()
        self.audio_available = True  # Always available (no pygame dependency)
    
    def text_to_speech(
        self,
        text: str,
        language: str,
        max_length: int = 1000
    ) -> Tuple[bool, Optional[str], Optional[bytes]]:
        """
        Generate TTS audio for Streamlit
        
        Args:
            text: Text to convert
            language: Language code
            max_length: Maximum text length
        
        Returns:
            Tuple of (success, error_message, audio_bytes)
        """
        audio_bytes, error = self.async_manager.generate_audio_bytes_sync(
            text, language, max_length
        )
        
        if error:
            return False, error, None
        
        return True, None, audio_bytes
    
    def is_playing(self) -> bool:
        """Compatibility method (not used with st.audio)"""
        return False
    
    def cleanup(self) -> bool:
        """Compatibility method (no cleanup needed)"""
        return True
