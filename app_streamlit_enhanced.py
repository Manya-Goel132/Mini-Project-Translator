"""
Enhanced Streamlit Web Application for AI Language Translator
With voice input, file upload, and advanced features
"""

import streamlit as st
import os
import sys
from datetime import datetime
import io
import base64

# Detect Streamlit Cloud environment
IS_STREAMLIT_CLOUD = os.getenv('STREAMLIT_SHARING_MODE') or 'streamlit.io' in os.getenv('HOSTNAME', '') or 'streamlit' in os.getenv('HOME', '')

# Configure for Streamlit Cloud
if IS_STREAMLIT_CLOUD:
    os.environ['OFFLINE_MODE'] = 'false'
    os.environ['USE_REDIS'] = 'false'
    os.environ['USE_CELERY'] = 'false'

# Import core modules with error handling
try:
    from core.translator import AITranslator
    TRANSLATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Translator module issue: {e}")
    TRANSLATOR_AVAILABLE = False

try:
    from core.history import HistoryManager
    HISTORY_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ History module issue: {e}")
    HISTORY_AVAILABLE = False

try:
    from core.audio_async import StreamlitAudioManager
    AUDIO_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Audio module issue: {e}")
    AUDIO_AVAILABLE = False

try:
    from core.user_auth import StreamlitAuth
    AUTH_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Authentication module issue: {e}")
    AUTH_AVAILABLE = False

CORE_MODULES_AVAILABLE = TRANSLATOR_AVAILABLE and HISTORY_AVAILABLE


def create_download_link(text, filename, link_text):
    """Create a download link for text"""
    b64 = base64.b64encode(text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'


def main():
    st.set_page_config(
        page_title="AI Language Translator",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check if core modules are available
    if not CORE_MODULES_AVAILABLE:
        st.error("❌ Some core modules not available. Running with limited functionality.")
        if not TRANSLATOR_AVAILABLE:
            st.error("Translation functionality unavailable")
        if not HISTORY_AVAILABLE:
            st.warning("History functionality unavailable")
        if not AUDIO_AVAILABLE:
            st.warning("Audio functionality unavailable")
        if not AUTH_AVAILABLE:
            st.warning("Authentication functionality unavailable")
    
    # Initialize authentication
    if AUTH_AVAILABLE:
        if 'auth' not in st.session_state:
            st.session_state.auth = StreamlitAuth()
        
        auth = st.session_state.auth
        
        # Show authentication UI if not authenticated
        if not auth.is_authenticated():
            st.markdown("## 🔐 Welcome to AI Language Translator")
            st.markdown("Please authenticate to access personalized features and history.")
            
            if auth.show_auth_ui():
                st.rerun()
            return
        
        # Show user info in sidebar
        auth.show_user_info()
        
        # Get current user ID for history filtering
        current_user_id = auth.get_user_id()
    else:
        current_user_id = None
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .translation-box {
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .feature-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize components
    if 'translator' not in st.session_state:
        with st.spinner("🚀 Initializing AI Translator..."):
            if TRANSLATOR_AVAILABLE:
                st.session_state.translator = AITranslator()
            else:
                st.session_state.translator = None
                
            if HISTORY_AVAILABLE:
                st.session_state.history_manager = HistoryManager()
            else:
                st.session_state.history_manager = None
                
            if AUDIO_AVAILABLE:
                st.session_state.audio_manager = StreamlitAudioManager()
            else:
                st.session_state.audio_manager = None
                
            st.session_state.voice_input = ""
    
    translator = st.session_state.translator
    history_manager = st.session_state.history_manager
    audio_manager = st.session_state.audio_manager
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌍 AI Language Translator</h1>
        <p style="font-size: 1.1em; margin-top: 0.5rem;">
            Advanced translation powered by multiple AI backends
        </p>
        <p style="font-size: 0.9em; opacity: 0.9;">
            ✨ Voice Input • 📁 File Upload • 🎵 Text-to-Speech • 📊 Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Language selection
        source_lang = st.selectbox(
            "🔤 Source Language",
            options=['auto'] + list(translator.supported_languages.keys()),
            format_func=lambda x: '🔍 Auto Detect' if x == 'auto' else f"{translator.supported_languages.get(x, x)}",
            key='source_lang'
        )
        
        target_lang = st.selectbox(
            "🎯 Target Language",
            options=list(translator.supported_languages.keys()),
            format_func=lambda x: translator.supported_languages.get(x, x),
            index=1,
            key='target_lang'
        )
        
        st.divider()
        
        # Options
        st.subheader("🎛️ Options")
        enable_tts = st.checkbox("🔊 Enable Text-to-Speech", value=True)
        save_history = st.checkbox("💾 Save Translation History", value=True)
        show_confidence = st.checkbox("📊 Show Confidence Scores", value=True)
        show_cache_status = st.checkbox("⚡ Show Cache Status", value=True)
        
        st.divider()
        
        # Statistics
        st.subheader("📈 Statistics")
        if st.button("📊 View Detailed Stats", use_container_width=True):
            stats = history_manager.get_stats(user_id=current_user_id)
            if stats:
                st.markdown("### 📊 Translation Statistics")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📝 Total", stats['total_translations'])
                    st.metric("📅 Today", stats['today_translations'])
                    st.metric("🎯 High Quality", stats['high_confidence_translations'])
                
                with col2:
                    st.metric("⭐ Avg Confidence", f"{stats['avg_confidence']:.1%}")
                    st.metric("⚡ Avg Time", f"{stats['avg_time']:.2f}s")
                    st.metric("🌐 Languages", stats['languages_translated'])
                
                if 'cache_hit_rate' in stats:
                    st.metric("💾 Cache Hit Rate", f"{stats['cache_hit_rate']:.1f}%")
                
                st.markdown("**🔧 Methods Used:**")
                for method, count in stats['methods_used'].items():
                    percentage = (count / stats['total_translations']) * 100
                    st.write(f"• {method}: {count} ({percentage:.1f}%)")
            else:
                st.info("📊 No statistics available yet. Start translating!")
        
        st.divider()
        
        # History management
        st.subheader("📚 History")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export", use_container_width=True):
                # Export user-specific history
                if current_user_id:
                    # Get user-specific data for export
                    user_history = history_manager.get_all(user_id=current_user_id)
                    if user_history:
                        import json
                        history_data = json.dumps(user_history, indent=2)
                    else:
                        history_data = None
                else:
                    history_data = history_manager.export_history('json', limit=1000)
                
                if history_data:
                    st.download_button(
                        "💾 Download JSON",
                        data=history_data,
                        file_name=f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    st.info("No history to export")
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                if st.session_state.get('confirm_clear', False):
                    if current_user_id:
                        # Clear only user-specific history
                        with st.session_state.history_manager._get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM translations WHERE user_id = ?", (current_user_id,))
                            conn.commit()
                    else:
                        history_manager.clear_history()
                    st.session_state.confirm_clear = False
                    st.success("✅ History cleared!")
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("⚠️ Click again to confirm")
        
        # Database info
        db_size = history_manager.get_database_size()
        if db_size:
            if current_user_id:
                user_count = len(history_manager.get_all(user_id=current_user_id))
                st.caption(f"💾 Your history: {user_count} records")
            else:
                st.caption(f"💾 Database: {db_size['size_human']} ({db_size['record_count']} records)")
    
    # Main interface with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Translate", "🎤 Voice Input", "📁 File Upload", "📚 History"])
    
    # Tab 1: Text Translation
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Input Text")
            input_text = st.text_area(
                "Enter text to translate:",
                height=250,
                placeholder="Type or paste your text here...\n\nTip: You can also use voice input or upload a file!",
                key='input_text',
                help="Maximum 10,000 characters"
            )
            
            # Character count with color coding
            char_count = len(input_text)
            char_color = "🟢" if char_count < 5000 else "🟡" if char_count < 8000 else "🔴"
            st.caption(f"{char_color} Characters: {char_count:,}/10,000")
            
            # Quick actions
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("🗑️ Clear", key="clear_input", use_container_width=True):
                    st.session_state.input_text = ""
                    st.rerun()
            with col_btn2:
                if st.button("📋 Paste", key="paste_input", use_container_width=True):
                    st.info("Use Ctrl+V to paste")
            with col_btn3:
                translate_btn = st.button(
                    "🚀 Translate",
                    type="primary",
                    disabled=not input_text.strip(),
                    use_container_width=True
                )
        
        with col2:
            st.subheader("🎯 Translation")
            
            if translate_btn and input_text.strip():
                # Validate input
                validation_errors = translator.validate_input(input_text.strip(), source_lang, target_lang)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(f"❌ {error}")
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
                                height=250,
                                key='output_text'
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Metadata in columns
                            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                            
                            with col_info1:
                                st.metric("🔧 Method", result['method'])
                            
                            with col_info2:
                                if show_confidence:
                                    confidence_color = "🟢" if result['confidence'] > 0.9 else "🟡" if result['confidence'] > 0.7 else "🔴"
                                    st.metric("📊 Confidence", f"{confidence_color} {result['confidence']:.1%}")
                            
                            with col_info3:
                                time_color = "🟢" if result['time'] < 1 else "🟡" if result['time'] < 3 else "🔴"
                                st.metric("⚡ Time", f"{time_color} {result['time']:.2f}s")
                            
                            with col_info4:
                                if show_cache_status:
                                    cached = result.get('cached', False)
                                    cache_icon = "💾" if cached else "🔄"
                                    cache_text = "Cached" if cached else "Fresh"
                                    st.metric(f"{cache_icon} Status", cache_text)
                            
                            # Action buttons
                            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                            
                            with col_btn1:
                                if st.button("📋 Copy", key="copy_main", use_container_width=True):
                                    st.code(result['translation'], language=None)
                                    st.success("✅ Ready to copy!")
                            
                            with col_btn2:
                                if enable_tts:
                                    if st.button("🔊 Listen", key="tts_main", use_container_width=True):
                                        with st.spinner("🎵 Generating audio..."):
                                            success, error, audio_bytes = audio_manager.text_to_speech(
                                                result['translation'],
                                                target_lang
                                            )
                                            if success:
                                                st.audio(audio_bytes, format='audio/mp3')
                                            else:
                                                st.error(f"❌ {error}")
                            
                            with col_btn3:
                                if st.button("🔄 Swap", key="swap_main", use_container_width=True):
                                    if source_lang != 'auto':
                                        st.session_state.source_lang = target_lang
                                        st.session_state.target_lang = source_lang
                                        st.session_state.input_text = result['translation']
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Can't swap with auto-detect")
                            
                            with col_btn4:
                                # Download button
                                download_text = f"Original ({source_lang}):\n{input_text.strip()}\n\nTranslation ({target_lang}):\n{result['translation']}"
                                st.download_button(
                                    "💾 Save",
                                    data=download_text,
                                    file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            
                            # Auto-save to history
                            if save_history:
                                history_manager.add_entry(input_text.strip(), result, target_lang, user_id=current_user_id)
                                st.success("✅ Translation saved to history!")
                        
                        else:
                            st.error("❌ Translation failed. Please try again.")
            
            elif not input_text.strip():
                st.info("👈 Enter text in the input box to translate")
    
    # Tab 2: Voice Input
    with tab2:
        st.subheader("🎤 Voice Input")
        
        # Import speech recognizer with fallback
        try:
            from core.speech_recognition_async import StreamlitSpeechRecognizer
            speech_recognizer = StreamlitSpeechRecognizer()
            speech_available = True
        except ImportError:
            speech_available = False
            speech_recognizer = None
        
        if not speech_available:
            st.warning("⚠️ Speech recognition not available. Install with: `pip install SpeechRecognition pydub`")
            st.markdown("""
            ### 📝 Alternative: Use your device's voice typing
            - **Windows**: Press `Win + H`
            - **Mac**: Press `Fn` twice or enable Dictation in System Preferences
            - **Mobile**: Use your keyboard's microphone button
            """)
        else:
            # Initialize session state for voice transcription
            if 'voice_transcription' not in st.session_state:
                st.session_state.voice_transcription = ""
            if 'voice_translation_result' not in st.session_state:
                st.session_state.voice_translation_result = None
            
            # Settings row
            col_settings1, col_settings2, col_settings3 = st.columns(3)
            
            with col_settings1:
                # Language names for display
                lang_display = {
                    'en': '🇺🇸 English (US)', 'en-gb': '🇬🇧 English (UK)',
                    'es': '🇪🇸 Spanish', 'es-mx': '🇲🇽 Spanish (Mexico)',
                    'fr': '🇫🇷 French', 'de': '🇩🇪 German',
                    'it': '🇮🇹 Italian', 'pt': '🇵🇹 Portuguese',
                    'pt-br': '🇧🇷 Portuguese (Brazil)', 'ru': '🇷🇺 Russian',
                    'ja': '🇯🇵 Japanese', 'ko': '🇰🇷 Korean',
                    'zh': '🇨🇳 Chinese (Simplified)', 'zh-tw': '🇹🇼 Chinese (Traditional)',
                    'ar': '🇸🇦 Arabic', 'hi': '🇮🇳 Hindi',
                    'nl': '🇳🇱 Dutch', 'sv': '🇸🇪 Swedish',
                    'da': '🇩🇰 Danish', 'no': '🇳🇴 Norwegian',
                    'fi': '🇫🇮 Finnish', 'pl': '🇵🇱 Polish',
                    'tr': '🇹🇷 Turkish', 'th': '🇹🇭 Thai',
                    'vi': '🇻🇳 Vietnamese', 'id': '🇮🇩 Indonesian'
                }
                supported_langs = list(speech_recognizer.get_supported_languages().keys())
                voice_lang = st.selectbox(
                    "🌐 Speech Language",
                    options=supported_langs,
                    format_func=lambda x: lang_display.get(x, translator.supported_languages.get(x, x)),
                    index=0,
                    key="voice_lang"
                )
            
            with col_settings2:
                voice_target = st.selectbox(
                    "🎯 Translate to",
                    options=list(translator.supported_languages.keys()),
                    format_func=lambda x: translator.supported_languages.get(x, x),
                    index=1,
                    key="voice_target_lang"
                )
            
            with col_settings3:
                auto_translate = st.checkbox("🔄 Auto-translate after transcription", value=True)
            
            st.markdown("---")
            
            # Audio input
            st.markdown("**🎙️ Record your voice or upload an audio file:**")
            audio_value = st.audio_input("Click to record", key="voice_recorder")
            
            if audio_value:
                # Show audio player
                st.audio(audio_value, format="audio/wav")
                
                # Transcribe button
                if st.button("🎧 Transcribe Audio", type="primary", use_container_width=True):
                    with st.spinner("🔄 Processing audio..."):
                        try:
                            # Read audio bytes
                            audio_bytes = audio_value.read()
                            
                            # Perform transcription
                            success, text, error = speech_recognizer.recognize_from_file(
                                audio_bytes,
                                language=voice_lang,
                                engine="google"
                            )
                            
                            if success and text:
                                st.session_state.voice_transcription = text
                                st.success(f"✅ Transcription complete!")
                                
                                # Auto-translate if enabled
                                if auto_translate and voice_lang != voice_target:
                                    with st.spinner("🤖 Translating..."):
                                        result = translator.smart_translate(text, voice_lang, voice_target)
                                        if result:
                                            st.session_state.voice_translation_result = result
                            else:
                                st.error(f"❌ {error or 'Could not transcribe audio'}")
                                st.session_state.voice_transcription = ""
                                st.session_state.voice_translation_result = None
                                
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            # Display results
            if st.session_state.voice_transcription:
                st.markdown("---")
                
                col_result1, col_result2 = st.columns(2)
                
                with col_result1:
                    st.markdown("**📝 Transcribed Text:**")
                    transcribed = st.text_area(
                        "Edit if needed:",
                        value=st.session_state.voice_transcription,
                        height=150,
                        key="transcribed_display"
                    )
                    
                    # Manual translate button
                    if st.button("🚀 Translate", key="manual_translate_voice", use_container_width=True):
                        with st.spinner("🤖 Translating..."):
                            result = translator.smart_translate(transcribed, voice_lang, voice_target)
                            if result:
                                st.session_state.voice_translation_result = result
                                st.rerun()
                            else:
                                st.error("❌ Translation failed")
                
                with col_result2:
                    st.markdown("**🎯 Translation:**")
                    if st.session_state.voice_translation_result:
                        result = st.session_state.voice_translation_result
                        st.text_area(
                            "Result:",
                            value=result['translation'],
                            height=150,
                            key="voice_translation_display"
                        )
                        
                        # Info and actions
                        st.caption(f"🔧 {result['method']} • ⭐ {result['confidence']:.0%}")
                        
                        col_action1, col_action2 = st.columns(2)
                        with col_action1:
                            if enable_tts:
                                if st.button("🔊 Listen", key="tts_voice", use_container_width=True):
                                    success, error, audio_bytes = audio_manager.text_to_speech(
                                        result['translation'], voice_target
                                    )
                                    if success:
                                        st.audio(audio_bytes, format='audio/mp3')
                                    else:
                                        st.error(f"❌ {error}")
                        
                        with col_action2:
                            if st.button("💾 Save to History", key="save_voice", use_container_width=True):
                                history_manager.add_entry(
                                    st.session_state.voice_transcription,
                                    result,
                                    voice_target,
                                    user_id=current_user_id
                                )
                                st.success("✅ Saved!")
                    else:
                        st.info("👈 Click 'Translate' to translate the transcribed text")
                
                # Clear button
                if st.button("🗑️ Clear Results", key="clear_voice", use_container_width=True):
                    st.session_state.voice_transcription = ""
                    st.session_state.voice_translation_result = None
                    st.rerun()
            
            elif not audio_value:
                st.info("👆 Click the microphone button to start recording")
            
            # Tips section
            st.markdown("---")
            with st.expander("💡 Tips for better recognition"):
                st.markdown("""
                **For best results:**
                - 🎙️ Speak clearly at a moderate pace
                - 🔇 Minimize background noise
                - 📏 Keep recordings between 2-30 seconds
                - 🌐 Select the correct speech language before recording
                - 🔊 Speak at a consistent volume
                
                **Supported audio formats:**
                - WAV, WebM, MP3, OGG, FLAC, M4A
                
                **Troubleshooting:**
                - If transcription fails, try recording again with less background noise
                - For long texts, break them into shorter recordings
                - Ensure your microphone is working properly
                """)
    
    # Tab 3: File Upload
    with tab3:
        st.subheader("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Upload a text file to translate",
            type=['txt', 'md', 'csv'],
            help="Supported formats: TXT, MD, CSV"
        )
        
        if uploaded_file:
            try:
                # Read file content
                file_content = uploaded_file.read().decode('utf-8')
                
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                st.caption(f"📊 Size: {len(file_content):,} characters")
                
                # Preview
                with st.expander("👁️ Preview file content"):
                    st.text_area("File content:", value=file_content[:1000], height=200, disabled=True)
                    if len(file_content) > 1000:
                        st.caption("... (showing first 1000 characters)")
                
                # Translate button
                if st.button("🚀 Translate File", type="primary", use_container_width=True):
                    if len(file_content) > 10000:
                        st.warning("⚠️ File is large. This may take a while...")
                    
                    with st.spinner("🤖 Translating file..."):
                        result = translator.smart_translate(
                            file_content,
                            source_lang,
                            target_lang
                        )
                        
                        if result:
                            st.success("✅ Translation complete!")
                            
                            # Show result
                            st.text_area(
                                "Translation:",
                                value=result['translation'],
                                height=300
                            )
                            
                            # Download button
                            output_filename = f"translated_{uploaded_file.name}"
                            st.download_button(
                                "💾 Download Translation",
                                data=result['translation'],
                                file_name=output_filename,
                                mime="text/plain",
                                use_container_width=True
                            )
                            
                            # Save to history
                            if save_history:
                                history_manager.add_entry(file_content, result, target_lang, user_id=current_user_id)
                        else:
                            st.error("❌ Translation failed")
            
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
        
        else:
            st.info("📤 Upload a file to get started")
    
    # Tab 4: History
    with tab4:
        st.subheader("📚 Translation History")
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input("🔍 Search history", placeholder="Search by text...")
        with col2:
            history_limit = st.selectbox("📊 Show", [10, 25, 50, 100], index=0)
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Get history
        if search_query:
            recent_history = history_manager.search(search_query, limit=history_limit, user_id=current_user_id)
            st.caption(f"🔍 Found {len(recent_history)} results")
        else:
            recent_history = history_manager.get_recent(history_limit, user_id=current_user_id)
            total_count = len(history_manager.get_all(user_id=current_user_id))
            st.caption(f"📊 Showing last {min(history_limit, total_count)} of {total_count:,} translations")
        
        if recent_history:
            for i, entry in enumerate(recent_history):
                with st.container():
                    # Header
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        st.markdown(f"**#{entry.get('id', i+1)}** • {timestamp}")
                    with col_h2:
                        source_name = translator.supported_languages.get(entry['source_lang'], entry['source_lang'])
                        target_name = translator.supported_languages.get(entry['target_lang'], entry['target_lang'])
                        st.markdown(f"**{source_name} → {target_name}**")
                    
                    # Content
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.markdown("**Original:**")
                        original_preview = entry['original_text'][:150] + "..." if len(entry['original_text']) > 150 else entry['original_text']
                        st.text(original_preview)
                    with col_c2:
                        st.markdown("**Translation:**")
                        translation_preview = entry['translated_text'][:150] + "..." if len(entry['translated_text']) > 150 else entry['translated_text']
                        st.text(translation_preview)
                    
                    # Metadata
                    st.caption(f"🔧 {entry['method']} • ⭐ {entry['confidence']:.1%} • ⚡ {entry['time_taken']:.2f}s")
                    
                    # Actions
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("🔄 Reuse", key=f"reuse_{i}", use_container_width=True):
                            st.session_state.input_text = entry['original_text']
                            st.session_state.source_lang = entry['source_lang']
                            st.session_state.target_lang = entry['target_lang']
                            st.rerun()
                    with col2:
                        if st.button("📋 Copy", key=f"copy_{i}", use_container_width=True):
                            st.code(entry['translated_text'], language=None)
                    with col3:
                        if enable_tts:
                            if st.button("🔊 Listen", key=f"tts_{i}", use_container_width=True):
                                success, error, audio_bytes = audio_manager.text_to_speech(
                                    entry['translated_text'],
                                    entry['target_lang']
                                )
                                if success:
                                    st.audio(audio_bytes, format='audio/mp3')
                    with col4:
                        download_text = f"Original:\n{entry['original_text']}\n\nTranslation:\n{entry['translated_text']}"
                        st.download_button(
                            "💾 Save",
                            data=download_text,
                            file_name=f"translation_{entry.get('id', i)}.txt",
                            key=f"download_{i}",
                            use_container_width=True
                        )
                    
                    st.divider()
        else:
            st.info("🔍 No translation history yet. Start translating!")
    
    # Footer
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**🤖 AI Translator**")
        st.caption("v3.0 Enhanced")
    
    with col2:
        st.markdown("**🔧 Features**")
        st.caption("AI • Voice • Files • TTS")
    
    with col3:
        st.markdown("**📊 Status**")
        if current_user_id:
            total = len(history_manager.get_all(user_id=current_user_id))
            st.caption(f"{total:,} your translations")
        else:
            total = len(history_manager.get_all())
            st.caption(f"{total:,} translations")
    
    with col4:
        st.markdown("**💾 Cache**")
        from core.caching import SharedModelCache
        cache = SharedModelCache.get_cache()
        stats = cache.get_cache_stats()
        redis_status = "✅" if stats.get('redis_connected') else "❌"
        st.caption(f"Redis: {redis_status}")


if __name__ == "__main__":
    main()
