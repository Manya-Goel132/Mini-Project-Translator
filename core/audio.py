"""
Text-to-Speech audio management
"""

from gtts import gTTS
import pygame
import os
import time
import threading
from pathlib import Path


class AudioManager:
    """Manages text-to-speech functionality"""
    
    def __init__(self, audio_dir="temp_audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        self.audio_playing = False
        self.current_audio_file = None
        self.audio_available = self._init_audio()
        
        # Language mapping for gTTS
        self.tts_lang_map = {
            'zh': 'zh', 'ja': 'ja', 'ko': 'ko', 'ar': 'ar',
            'hi': 'hi', 'th': 'th', 'cs': 'cs', 'hu': 'hu',
            'ro': 'ro', 'bg': 'bg', 'hr': 'hr', 'sk': 'sk'
        }
    
    def _init_audio(self):
        """Initialize audio system with error handling"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            return True
        except Exception:
            return False
    
    def generate_tts_audio(self, text, language, max_length=1000):
        """Generate TTS audio file"""
        if not self.audio_available:
            return None, "Audio system not available"
        
        try:
            # Validate and truncate text
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Map language for gTTS
            tts_lang = self.tts_lang_map.get(language, language)
            
            # Create TTS
            try:
                tts = gTTS(text=text, lang=tts_lang, slow=False)
            except Exception:
                # Fallback to English
                tts = gTTS(text=text, lang='en', slow=False)
            
            # Create temporary audio file
            audio_file = self.audio_dir / f"tts_{int(time.time() * 1000)}.mp3"
            tts.save(str(audio_file))
            
            return str(audio_file), None
            
        except Exception as e:
            return None, f"TTS generation failed: {e}"
    
    def play_audio(self, audio_file):
        """Play audio file"""
        if not self.audio_available:
            return False, "Audio system not available"
        
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            self.audio_playing = True
            self.current_audio_file = audio_file
            return True, None
        except Exception as e:
            return False, f"Audio playback failed: {e}"
    
    def stop_audio(self):
        """Stop current audio playback"""
        if not self.audio_playing:
            return True
        
        try:
            pygame.mixer.music.stop()
            self.audio_playing = False
            
            # Clean up file
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                os.remove(self.current_audio_file)
            
            return True
        except Exception:
            return False
    
    def text_to_speech(self, text, language):
        """Complete TTS workflow - generate and play"""
        # Stop current audio if playing
        if self.audio_playing:
            self.stop_audio()
            return True, "Audio stopped"
        
        # Generate audio
        audio_file, error = self.generate_tts_audio(text, language)
        if error:
            return False, error
        
        # Play audio in background thread
        def play_audio_thread():
            try:
                success, error = self.play_audio(audio_file)
                if not success:
                    return
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                self.audio_playing = False
                
                # Clean up file
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                except:
                    pass
                    
            except Exception:
                self.audio_playing = False
        
        # Start audio in background thread
        audio_thread = threading.Thread(target=play_audio_thread, daemon=True)
        audio_thread.start()
        
        return True, None
    
    def is_playing(self):
        """Check if audio is currently playing"""
        return self.audio_playing
    
    def cleanup(self):
        """Clean up temporary audio files"""
        try:
            for file in self.audio_dir.glob("*.mp3"):
                file.unlink()
            return True
        except Exception:
            return False
