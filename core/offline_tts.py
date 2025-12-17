"""
Offline Text-to-Speech functionality
Supports multiple offline TTS engines
"""

import os
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import asyncio


class OfflineTTSManager:
    """
    Offline Text-to-Speech manager
    Supports pyttsx3, eSpeak, and system TTS
    """
    
    def __init__(self):
        """Initialize offline TTS with available engines"""
        self.available_engines = self._detect_engines()
        self.preferred_engine = self._get_preferred_engine()
    
    def _detect_engines(self) -> dict:
        """Detect available offline TTS engines"""
        engines = {}
        
        # Test pyttsx3
        try:
            import pyttsx3
            engines['pyttsx3'] = True
        except ImportError:
            engines['pyttsx3'] = False
        
        # Test eSpeak
        try:
            result = subprocess.run(['espeak', '--version'], 
                                  capture_output=True, timeout=5)
            engines['espeak'] = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            engines['espeak'] = False
        
        # Test system TTS
        if os.name == 'nt':  # Windows
            engines['sapi'] = True  # Windows Speech API
        elif os.uname().sysname == 'Darwin':  # macOS
            engines['say'] = True
        else:
            engines['festival'] = self._test_festival()
        
        return engines
    
    def _test_festival(self) -> bool:
        """Test if Festival TTS is available"""
        try:
            result = subprocess.run(['festival', '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_preferred_engine(self) -> str:
        """Get the best available engine"""
        if self.available_engines.get('pyttsx3'):
            return 'pyttsx3'
        elif self.available_engines.get('say'):  # macOS
            return 'say'
        elif self.available_engines.get('sapi'):  # Windows
            return 'sapi'
        elif self.available_engines.get('espeak'):
            return 'espeak'
        elif self.available_engines.get('festival'):
            return 'festival'
        else:
            return None
    
    async def generate_audio_bytes(
        self,
        text: str,
        language: str = 'en',
        engine: str = None
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate TTS audio bytes offline
        
        Args:
            text: Text to convert
            language: Language code
            engine: Specific engine to use
        
        Returns:
            Tuple of (audio_bytes, error_message)
        """
        if not engine:
            engine = self.preferred_engine
        
        if not engine:
            return None, "No offline TTS engines available"
        
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None,
                self._generate_sync,
                text,
                language,
                engine
            )
            return audio_bytes, None
        except Exception as e:
            return None, f"Offline TTS failed: {str(e)}"
    
    def _generate_sync(self, text: str, language: str, engine: str) -> bytes:
        """Synchronous TTS generation"""
        if engine == 'pyttsx3':
            return self._generate_pyttsx3(text, language)
        elif engine == 'espeak':
            return self._generate_espeak(text, language)
        elif engine == 'say':
            return self._generate_say(text)
        elif engine == 'sapi':
            return self._generate_sapi(text)
        elif engine == 'festival':
            return self._generate_festival(text)
        else:
            raise Exception(f"Unknown engine: {engine}")
    
    def _generate_pyttsx3(self, text: str, language: str) -> bytes:
        """Generate audio using pyttsx3"""
        import pyttsx3
        
        engine = pyttsx3.init()
        
        # Configure voice
        voices = engine.getProperty('voices')
        if voices:
            # Try to find voice for language
            for voice in voices:
                if language in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
        
        # Configure rate and volume
        engine.setProperty('rate', 150)  # Speed
        engine.setProperty('volume', 0.9)  # Volume
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read the generated file
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _generate_espeak(self, text: str, language: str) -> bytes:
        """Generate audio using eSpeak"""
        # Map language codes to eSpeak voices
        espeak_voices = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'pt': 'pt',
            'ru': 'ru',
            'zh': 'zh',
            'ja': 'ja',
            'ko': 'ko'
        }
        
        voice = espeak_voices.get(language, 'en')
        
        # Generate audio to stdout
        result = subprocess.run([
            'espeak',
            '-v', voice,
            '-s', '150',  # Speed
            '--stdout',
            text
        ], capture_output=True, check=True)
        
        return result.stdout
    
    def _generate_say(self, text: str) -> bytes:
        """Generate audio using macOS 'say' command"""
        with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Use 'say' to generate audio file
            subprocess.run([
                'say',
                '-o', temp_path,
                text
            ], check=True)
            
            # Read the generated file
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _generate_sapi(self, text: str) -> bytes:
        """Generate audio using Windows SAPI"""
        # This would require additional Windows-specific implementation
        # For now, fall back to pyttsx3 if available
        if self.available_engines.get('pyttsx3'):
            return self._generate_pyttsx3(text, 'en')
        else:
            raise Exception("Windows SAPI not implemented, install pyttsx3")
    
    def _generate_festival(self, text: str) -> bytes:
        """Generate audio using Festival TTS"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Use Festival to generate audio
            process = subprocess.Popen([
                'festival', '--tts'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            
            process.communicate(input=text.encode())
            
            # Festival outputs to default audio, need to capture differently
            # This is a simplified implementation
            raise Exception("Festival TTS requires additional setup")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def get_engine_info(self) -> dict:
        """Get information about available engines"""
        return {
            'pyttsx3': {
                'available': self.available_engines.get('pyttsx3', False),
                'description': 'Cross-platform TTS library',
                'languages': 'System dependent',
                'quality': 'Good'
            },
            'espeak': {
                'available': self.available_engines.get('espeak', False),
                'description': 'Compact open source TTS',
                'languages': '50+ languages',
                'quality': 'Basic'
            },
            'say': {
                'available': self.available_engines.get('say', False),
                'description': 'macOS built-in TTS',
                'languages': 'System voices',
                'quality': 'Excellent'
            },
            'sapi': {
                'available': self.available_engines.get('sapi', False),
                'description': 'Windows Speech API',
                'languages': 'System voices',
                'quality': 'Good'
            }
        }


class OfflineAudioManager:
    """
    Audio manager that prefers offline TTS but falls back to online
    """
    
    def __init__(self):
        self.offline_tts = OfflineTTSManager()
        
        # Import online TTS as fallback
        try:
            from .audio_async import AsyncAudioManager
            self.online_tts = AsyncAudioManager()
        except ImportError:
            self.online_tts = None
    
    async def generate_audio_bytes(
        self,
        text: str,
        language: str = 'en',
        prefer_offline: bool = True
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate audio bytes with offline preference
        
        Args:
            text: Text to convert
            language: Language code
            prefer_offline: Try offline first
        
        Returns:
            Tuple of (audio_bytes, error_message)
        """
        if prefer_offline and self.offline_tts.preferred_engine:
            # Try offline first
            audio_bytes, error = await self.offline_tts.generate_audio_bytes(
                text, language
            )
            if audio_bytes:
                return audio_bytes, None
        
        # Fall back to online TTS
        if self.online_tts:
            return await self.online_tts.generate_audio_bytes(text, language)
        
        return None, "No TTS engines available"