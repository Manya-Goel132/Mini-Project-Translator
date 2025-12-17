"""
Fallback Streamlit app for when dependencies are missing
"""

import streamlit as st
import requests
import json
from datetime import datetime

def simple_translate(text, source_lang, target_lang):
    """Simple translation using Google Translate API fallback"""
    try:
        # Use a simple translation service
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)
        return result
    except Exception as e:
        return f"Translation error: {str(e)}"

def main():
    st.set_page_config(
        page_title="AI Language Translator (Fallback)",
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 AI Language Translator")
    st.info("⚠️ Running in fallback mode with limited features")
    
    # Simple translation interface
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input")
        text = st.text_area("Enter text to translate:", height=200)
        
        source_lang = st.selectbox("From:", 
            options=['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'],
            format_func=lambda x: {
                'auto': 'Auto Detect',
                'en': 'English', 'es': 'Spanish', 'fr': 'French',
                'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese'
            }.get(x, x)
        )
        
        target_lang = st.selectbox("To:",
            options=['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'],
            format_func=lambda x: {
                'en': 'English', 'es': 'Spanish', 'fr': 'French',
                'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese'
            }.get(x, x),
            index=1
        )
    
    with col2:
        st.subheader("Translation")
        
        if st.button("🚀 Translate", type="primary"):
            if text.strip():
                with st.spinner("Translating..."):
                    try:
                        result = simple_translate(text, source_lang, target_lang)
                        st.text_area("Result:", value=result, height=200)
                        st.success("✅ Translation complete!")
                    except Exception as e:
                        st.error(f"❌ Translation failed: {str(e)}")
            else:
                st.warning("Please enter some text to translate")
    
    st.markdown("---")
    st.info("💡 This is a simplified version. The full app includes voice input, file upload, offline mode, and more features.")

if __name__ == "__main__":
    main()