import streamlit as st
import torch
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from gtts import gTTS
import pygame
import os
import tempfile
from deep_translator import GoogleTranslator, MyMemoryTranslator
import time
import json
from datetime import datetime
import pandas as pd
import re
import threading
from pathlib import Path
import base64

class AITranslator:
    def __init__(self):
        self.translation_history = []
        self.model_cache = {}
        self.audio_playing = False
        self.current_audio_file = None
        self.supported_languages = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
            'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian',
            'fi': 'Finnish', 'pl': 'Polish', 'tr': 'Turkish', 'th': 'Thai'
        }
        
        # Initialize pygame mixer for audio
        self.init_audio()
        
        # Create history directory
        self.history_dir = Path("translation_history")
        self.history_dir.mkdir(exist_ok=True)
        
        # Create temp audio directory
        self.audio_dir = Path("temp_audio")
        self.audio_dir.mkdir(exist_ok=True)
    
    def init_audio(self):
        """Initialize audio system with better error handling"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.audio_available = True
        except Exception as e:
            st.warning(f"Audio system unavailable: {e}")
            self.audio_available = False
    
    @st.cache_resource
    def load_ai_model(_self, model_name):
        """Load and cache AI translation models"""
        try:
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            return tokenizer, model
        except Exception:
            return None, None
    
    def detect_language(self, text):
        """Enhanced language detection"""
        if not text or len(text.strip()) < 3:
            return 'en', 0.3
        
        try:
            clean_text = re.sub(r'[^\w\s]', ' ', text)
            clean_text = ' '.join(clean_text.split())
            
            detected = detect(clean_text if len(clean_text) > 10 else text)
            confidence = 0.95 if len(clean_text) > 10 else 0.7
            
            if detected not in self.supported_languages:
                return 'en', 0.5
                
            return detected, confidence
            
        except LangDetectException:
            # Character-based fallback detection
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'zh', 0.8
            elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
                return 'ja', 0.8
            elif any('\uac00' <= char <= '\ud7af' for char in text):
                return 'ko', 0.8
            elif any('\u0600' <= char <= '\u06ff' for char in text):
                return 'ar', 0.8
            elif any('\u0900' <= char <= '\u097f' for char in text):
                return 'hi', 0.8
            else:
                return 'en', 0.5
    
    def translate_with_ai(self, text, source_lang, target_lang):
        """AI translation with Marian models"""
        if not text.strip():
            return None, None
            
        model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        
        try:
            tokenizer, model = self.load_ai_model(model_name)
            if tokenizer and model:
                # Handle long text by chunking
                max_length = 400
                if len(text) > max_length:
                    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                    translated_chunks = []
                    
                    for chunk in chunks:
                        inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512)
                        with torch.no_grad():
                            outputs = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
                        chunk_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        translated_chunks.append(chunk_result)
                    
                    result = ' '.join(translated_chunks)
                else:
                    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                    with torch.no_grad():
                        outputs = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
                    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                return result, f"AI Model (Marian)"
        except Exception as e:
            pass
        
        return None, None
    
    def translate_with_google(self, text, source_lang, target_lang):
        """Google Translate with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if source_lang == 'auto':
                    detected_lang, _ = self.detect_language(text)
                    source_lang = detected_lang
                
                # Handle long text
                max_chunk_size = 4500
                if len(text) > max_chunk_size:
                    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
                    translated_chunks = []
                    
                    for chunk in chunks:
                        translator = GoogleTranslator(source=source_lang, target=target_lang)
                        chunk_result = translator.translate(chunk)
                        translated_chunks.append(chunk_result)
                        time.sleep(0.1)
                    
                    result = ' '.join(translated_chunks)
                else:
                    translator = GoogleTranslator(source=source_lang, target=target_lang)
                    result = translator.translate(text)
                
                return result, source_lang, "Google Translate"
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    break
        
        return None, None, None
    
    def translate_with_mymemory(self, text, source_lang, target_lang):
        """MyMemory translation"""
        try:
            max_chunk_size = 450
            if len(text) > max_chunk_size:
                chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
                translated_chunks = []
                
                for chunk in chunks:
                    translator = MyMemoryTranslator(source=source_lang, target=target_lang)
                    chunk_result = translator.translate(chunk)
                    translated_chunks.append(chunk_result)
                    time.sleep(0.2)
                
                result = ' '.join(translated_chunks)
            else:
                translator = MyMemoryTranslator(source=source_lang, target=target_lang)
                result = translator.translate(text)
            
            return result, "MyMemory"
            
        except Exception:
            return None, None
    
    def smart_translate(self, text, source_lang, target_lang):
        """Smart translation with fallback chain"""
        start_time = time.time()
        
        # Auto-detect language if needed
        if source_lang == 'auto':
            detected_lang, confidence = self.detect_language(text)
            source_lang = detected_lang
        
        # Try AI model first
        ai_result, ai_method = self.translate_with_ai(text, source_lang, target_lang)
        if ai_result:
            return {
                'translation': ai_result,
                'source_lang': source_lang,
                'method': ai_method,
                'time': time.time() - start_time,
                'confidence': 0.95
            }
        
        # Fallback to Google Translate
        google_result, detected_lang, google_method = self.translate_with_google(text, source_lang, target_lang)
        if google_result:
            return {
                'translation': google_result,
                'source_lang': detected_lang,
                'method': google_method,
                'time': time.time() - start_time,
                'confidence': 0.90
            }
        
        # Last resort: MyMemory
        mymemory_result, mymemory_method = self.translate_with_mymemory(text, source_lang, target_lang)
        if mymemory_result:
            return {
                'translation': mymemory_result,
                'source_lang': source_lang,
                'method': mymemory_method,
                'time': time.time() - start_time,
                'confidence': 0.80
            }
        
        return None
    
    def text_to_speech(self, text, language):
        """Enhanced text-to-speech that actually works"""
        if not self.audio_available:
            st.error("Audio system not available")
            return False
        
        # Stop current audio if playing
        if self.audio_playing:
            try:
                pygame.mixer.music.stop()
                self.audio_playing = False
                if self.current_audio_file and os.path.exists(self.current_audio_file):
                    os.remove(self.current_audio_file)
                return True
            except:
                pass
        
        try:
            # Validate and truncate text
            if len(text) > 1000:
                text = text[:1000] + "..."
                st.info("Text truncated to 1000 characters for audio")
            
            # Language mapping for gTTS
            tts_lang_map = {
                'zh': 'zh', 'ja': 'ja', 'ko': 'ko', 'ar': 'ar',
                'hi': 'hi', 'th': 'th', 'cs': 'cs', 'hu': 'hu',
                'ro': 'ro', 'bg': 'bg', 'hr': 'hr', 'sk': 'sk'
            }
            
            tts_lang = tts_lang_map.get(language, language)
            
            # Create TTS
            try:
                tts = gTTS(text=text, lang=tts_lang, slow=False)
            except Exception:
                # Fallback to English
                tts = gTTS(text=text, lang='en', slow=False)
                st.warning(f"Language {language} not supported for TTS, using English")
            
            # Create temporary audio file
            audio_file = self.audio_dir / f"tts_{int(time.time() * 1000)}.mp3"
            tts.save(str(audio_file))
            self.current_audio_file = str(audio_file)
            
            # Play audio
            def play_audio_thread():
                try:
                    pygame.mixer.music.load(str(audio_file))
                    pygame.mixer.music.play()
                    self.audio_playing = True
                    
                    # Wait for playback to finish
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    self.audio_playing = False
                    
                    # Clean up file
                    try:
                        if audio_file.exists():
                            audio_file.unlink()
                    except:
                        pass
                        
                except Exception as e:
                    self.audio_playing = False
                    st.error(f"Audio playback failed: {e}")
            
            # Start audio in background thread
            audio_thread = threading.Thread(target=play_audio_thread, daemon=True)
            audio_thread.start()
            
            return True
            
        except Exception as e:
            st.error(f"Text-to-speech failed: {e}")
            self.audio_playing = False
            return False
    
    def save_translation_history(self, original_text, translation_result):
        """Save translation to history"""
        try:
            history_entry = {
                'id': len(self.translation_history) + 1,
                'timestamp': datetime.now().isoformat(),
                'original_text': original_text[:500],
                'translated_text': translation_result['translation'][:500],
                'source_lang': translation_result['source_lang'],
                'target_lang': st.session_state.get('target_lang', 'en'),
                'method': translation_result['method'],
                'confidence': translation_result['confidence'],
                'time_taken': translation_result['time'],
                'text_length': len(original_text),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            self.translation_history.append(history_entry)
            
            # Save to file
            history_file = self.history_dir / 'translation_history.json'
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_history[-100:], f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            st.warning(f"Failed to save history: {e}")
    
    def load_translation_history(self):
        """Load translation history"""
        try:
            history_file = self.history_dir / 'translation_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.translation_history = json.load(f)
            else:
                self.translation_history = []
        except Exception:
            self.translation_history = []
    
    def get_translation_stats(self):
        """Get translation statistics"""
        if not self.translation_history:
            return None
        
        try:
            df = pd.DataFrame(self.translation_history)
            
            stats = {
                'total_translations': len(df),
                'avg_confidence': df['confidence'].mean() if 'confidence' in df.columns else 0,
                'avg_time': df['time_taken'].mean() if 'time_taken' in df.columns else 0,
                'most_used_source': df['source_lang'].mode().iloc[0] if not df['source_lang'].mode().empty else 'N/A',
                'most_used_target': df['target_lang'].mode().iloc[0] if not df['target_lang'].mode().empty else 'N/A',
                'methods_used': df['method'].value_counts().to_dict() if 'method' in df.columns else {},
                'languages_translated': len(df['source_lang'].unique()) if 'source_lang' in df.columns else 0,
                'today_translations': len(df[df['date'] == datetime.now().strftime('%Y-%m-%d')]) if 'date' in df.columns else 0,
                'high_confidence_translations': len(df[df['confidence'] > 0.9]) if 'confidence' in df.columns else 0
            }
            
            return stats
        except Exception:
            return None
    
    def export_history(self, format_type='json'):
        """Export history in different formats"""
        try:
            if not self.translation_history:
                return None
                
            if format_type == 'json':
                return json.dumps(self.translation_history, indent=2, ensure_ascii=False)
            elif format_type == 'csv':
                df = pd.DataFrame(self.translation_history)
                return df.to_csv(index=False)
        except Exception:
            return None
    
    def clear_history(self):
        """Clear translation history"""
        try:
            self.translation_history = []
            for file in self.history_dir.glob("*.json"):
                file.unlink()
            return True
        except Exception:
            return False
    
    def validate_input(self, text, source_lang, target_lang):
        """Validate input"""
        errors = []
        
        if not text or not text.strip():
            errors.append("Please enter some text to translate")
        
        if len(text) > 10000:
            errors.append("Text is too long (maximum 10,000 characters)")
        
        if source_lang == target_lang and source_lang != 'auto':
            errors.append("Source and target languages cannot be the same")
        
        return errors

def create_copy_button(text, button_id):
    """Create a working copy button with JavaScript"""
    button_html = f"""
    <button onclick="copyToClipboard{button_id}()" style="
        background: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 14px;
        margin: 5px 0;
    ">📋 Copy</button>
    
    <script>
    function copyToClipboard{button_id}() {{
        navigator.clipboard.writeText(`{text.replace('`', '\\`').replace('\\', '\\\\')}`).then(function() {{
            alert('Copied to clipboard!');
        }}).catch(function(err) {{
            console.error('Could not copy text: ', err);
        }});
    }}
    </script>
    """
    return button_html

def main():
    st.set_page_config(
        page_title="AI Language Translator",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .translation-box {
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background: #f8f9fa;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize translator
    if 'translator' not in st.session_state:
        with st.spinner("🚀 Initializing AI Translator..."):
            st.session_state.translator = AITranslator()
            st.session_state.translator.load_translation_history()
    
    translator = st.session_state.translator
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Language Translator</h1>
        <p>Advanced translation powered by multiple AI backends</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Language selection
        source_lang = st.selectbox(
            "Source Language",
            options=['auto'] + list(translator.supported_languages.keys()),
            format_func=lambda x: 'Auto Detect' if x == 'auto' else translator.supported_languages.get(x, x),
            key='source_lang'
        )
        
        target_lang = st.selectbox(
            "Target Language",
            options=list(translator.supported_languages.keys()),
            format_func=lambda x: translator.supported_languages.get(x, x),
            index=1,
            key='target_lang'
        )
        
        st.divider()
        
        # Options
        st.subheader("🎛️ Options")
        enable_tts = st.checkbox("Enable Text-to-Speech", value=True)
        save_history = st.checkbox("Save Translation History", value=True)
        show_confidence = st.checkbox("Show Confidence Scores", value=True)
        
        st.divider()
        
        # Statistics
        if st.button("📊 Show Statistics"):
            stats = translator.get_translation_stats()
            if stats:
                st.subheader("📈 Statistics")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total", stats['total_translations'])
                    st.metric("Today", stats['today_translations'])
                
                with col2:
                    st.metric("Confidence", f"{stats['avg_confidence']:.1%}")
                    st.metric("Avg Time", f"{stats['avg_time']:.2f}s")
                
                st.write("**Methods:**")
                for method, count in stats['methods_used'].items():
                    st.write(f"• {method}: {count}")
            else:
                st.info("No statistics available yet")
        
        st.divider()
        
        # History management
        st.subheader("📚 History")
        
        if st.button("📥 Export History"):
            if translator.translation_history:
                export_data = translator.export_history('json')
                if export_data:
                    st.download_button(
                        "Download JSON",
                        data=export_data,
                        file_name=f"translations_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
            else:
                st.info("No history to export")
        
        if st.button("🗑️ Clear History"):
            if translator.clear_history():
                st.success("History cleared!")
                st.rerun()
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Input Text")
        input_text = st.text_area(
            "Enter text to translate:",
            height=200,
            placeholder="Type or paste your text here...",
            key='input_text'
        )
        
        # Character count
        char_count = len(input_text)
        st.caption(f"Characters: {char_count}/10,000")
        
        # Translation button
        translate_btn = st.button(
            "🚀 Translate",
            type="primary",
            disabled=not input_text.strip()
        )
    
    with col2:
        st.subheader("🎯 Translation")
        
        if translate_btn and input_text.strip():
            # Validate input
            validation_errors = translator.validate_input(input_text.strip(), source_lang, target_lang)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                with st.spinner("🤖 Translating..."):
                    result = translator.smart_translate(
                        input_text.strip(),
                        source_lang,
                        target_lang
                    )
                    
                    if result:
                        # Store in session state
                        st.session_state.last_translation = result
                        st.session_state.last_input = input_text.strip()
                        
                        # Display translation
                        st.markdown('<div class="translation-box">', unsafe_allow_html=True)
                        translation_text = st.text_area(
                            "✨ Translation Result:",
                            value=result['translation'],
                            height=200,
                            key='output_text'
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Metadata
                        col_info1, col_info2, col_info3 = st.columns(3)
                        
                        with col_info1:
                            st.metric("🔧 Method", result['method'])
                        
                        with col_info2:
                            if show_confidence:
                                confidence_color = "🟢" if result['confidence'] > 0.9 else "🟡" if result['confidence'] > 0.7 else "🔴"
                                st.metric("📊 Confidence", f"{confidence_color} {result['confidence']:.1%}")
                        
                        with col_info3:
                            time_color = "🟢" if result['time'] < 1 else "🟡" if result['time'] < 3 else "🔴"
                            st.metric("⏱️ Time", f"{time_color} {result['time']:.2f}s")
                        
                        # Action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            # Copy button with JavaScript
                            copy_html = create_copy_button(result['translation'], "main")
                            st.components.v1.html(copy_html, height=50)
                        
                        with col_btn2:
                            if enable_tts and translator.audio_available:
                                tts_label = "🔊 Listen" if not translator.audio_playing else "⏹️ Stop"
                                if st.button(tts_label, key="tts_main"):
                                    success = translator.text_to_speech(result['translation'], target_lang)
                                    if success and not translator.audio_playing:
                                        st.success("🎵 Playing audio...")
                            elif enable_tts:
                                st.button("🔊 Audio Unavailable", disabled=True)
                        
                        with col_btn3:
                            if st.button("🔄 Swap Languages", key="swap_main"):
                                if source_lang != 'auto':
                                    # Swap languages and text
                                    st.session_state.source_lang = target_lang
                                    st.session_state.target_lang = source_lang
                                    st.session_state.input_text = result['translation']
                                    st.rerun()
                        
                        # Auto-save to history
                        if save_history:
                            translator.save_translation_history(input_text.strip(), result)
                            st.success("✅ Translation saved to history!")
                    
                    else:
                        st.error("❌ Translation failed. Please try again.")
    
    # Translation History
    if st.expander("📚 Translation History", expanded=False):
        if translator.translation_history:
            # Show recent translations
            st.write(f"📊 Showing last 10 of {len(translator.translation_history)} translations")
            
            for i, entry in enumerate(reversed(translator.translation_history[-10:])):
                with st.container():
                    # Header
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
                    st.write(f"**#{entry.get('id', i+1)}** - {timestamp}")
                    
                    # Languages and method
                    source_name = translator.supported_languages.get(entry['source_lang'], entry['source_lang'])
                    target_name = translator.supported_languages.get(entry['target_lang'], entry['target_lang'])
                    st.write(f"🔄 **{source_name} → {target_name}** | 🔧 {entry['method']}")
                    
                    # Text content
                    original_preview = entry['original_text'][:100] + "..." if len(entry['original_text']) > 100 else entry['original_text']
                    translation_preview = entry['translated_text'][:100] + "..." if len(entry['translated_text']) > 100 else entry['translated_text']
                    
                    st.write(f"**Original:** {original_preview}")
                    st.write(f"**Translation:** {translation_preview}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🔄 Reuse", key=f"reuse_{i}"):
                            st.session_state.input_text = entry['original_text']
                            st.session_state.source_lang = entry['source_lang']
                            st.session_state.target_lang = entry['target_lang']
                            st.rerun()
                    
                    with col2:
                        copy_html = create_copy_button(entry['translated_text'], f"hist_{i}")
                        st.components.v1.html(copy_html, height=40)
                    
                    with col3:
                        if enable_tts and translator.audio_available:
                            if st.button("🔊 Listen", key=f"tts_hist_{i}"):
                                translator.text_to_speech(entry['translated_text'], entry['target_lang'])
                    
                    st.divider()
        else:
            st.info("🔍 No translation history yet. Start translating!")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🤖 AI Language Translator**")
        st.markdown("Multiple AI backends")
    
    with col2:
        st.markdown("**🔧 Features**")
        st.markdown("• AI Models • Google • TTS • History")
    
    with col3:
        st.markdown("**📊 Status**")
        if translator.translation_history:
            st.markdown(f"• {len(translator.translation_history)} translations")
        st.markdown(f"• Audio: {'✅' if translator.audio_available else '❌'}")

if __name__ == "__main__":
    main()