"""
Streamlit Web Application for AI Language Translator
"""

import streamlit as st
from datetime import datetime
from core.translator import AITranslator
from core.history import HistoryManager
from core.audio import AudioManager


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
    
    # Initialize components
    if 'translator' not in st.session_state:
        with st.spinner("🚀 Initializing AI Translator..."):
            st.session_state.translator = AITranslator()
            st.session_state.history_manager = HistoryManager()
            st.session_state.audio_manager = AudioManager()
    
    translator = st.session_state.translator
    history_manager = st.session_state.history_manager
    audio_manager = st.session_state.audio_manager
    
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
            stats = history_manager.get_stats()
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
            history_data = history_manager.get_all()
            if history_data:
                export_data = history_manager.export_history('json')
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
            if history_manager.clear_history():
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
                            copy_html = create_copy_button(result['translation'], "main")
                            st.components.v1.html(copy_html, height=50)
                        
                        with col_btn2:
                            if enable_tts and audio_manager.audio_available:
                                tts_label = "🔊 Listen" if not audio_manager.audio_playing else "⏹️ Stop"
                                if st.button(tts_label, key="tts_main"):
                                    success, error = audio_manager.text_to_speech(result['translation'], target_lang)
                                    if success and not audio_manager.audio_playing:
                                        st.success("🎵 Playing audio...")
                                    elif error:
                                        st.error(error)
                            elif enable_tts:
                                st.button("🔊 Audio Unavailable", disabled=True)
                        
                        with col_btn3:
                            if st.button("🔄 Swap Languages", key="swap_main"):
                                if source_lang != 'auto':
                                    st.session_state.source_lang = target_lang
                                    st.session_state.target_lang = source_lang
                                    st.session_state.input_text = result['translation']
                                    st.rerun()
                        
                        # Auto-save to history
                        if save_history:
                            history_manager.add_entry(input_text.strip(), result, target_lang)
                            st.success("✅ Translation saved to history!")
                    
                    else:
                        st.error("❌ Translation failed. Please try again.")
    
    # Translation History
    if st.expander("📚 Translation History", expanded=False):
        recent_history = history_manager.get_recent(10)
        if recent_history:
            st.write(f"📊 Showing last 10 of {len(history_manager.get_all())} translations")
            
            for i, entry in enumerate(recent_history):
                with st.container():
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
                    st.write(f"**#{entry.get('id', i+1)}** - {timestamp}")
                    
                    source_name = translator.supported_languages.get(entry['source_lang'], entry['source_lang'])
                    target_name = translator.supported_languages.get(entry['target_lang'], entry['target_lang'])
                    st.write(f"🔄 **{source_name} → {target_name}** | 🔧 {entry['method']}")
                    
                    original_preview = entry['original_text'][:100] + "..." if len(entry['original_text']) > 100 else entry['original_text']
                    translation_preview = entry['translated_text'][:100] + "..." if len(entry['translated_text']) > 100 else entry['translated_text']
                    
                    st.write(f"**Original:** {original_preview}")
                    st.write(f"**Translation:** {translation_preview}")
                    
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
                        if enable_tts and audio_manager.audio_available:
                            if st.button("🔊 Listen", key=f"tts_hist_{i}"):
                                audio_manager.text_to_speech(entry['translated_text'], entry['target_lang'])
                    
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
        total_translations = len(history_manager.get_all())
        if total_translations:
            st.markdown(f"• {total_translations} translations")
        st.markdown(f"• Audio: {'✅' if audio_manager.audio_available else '❌'}")


if __name__ == "__main__":
    main()
