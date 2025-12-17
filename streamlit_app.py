"""
Streamlit Cloud entry point
This file is automatically detected by Streamlit Cloud
"""

import streamlit as st

try:
    # Try to import the full enhanced app
    from app_streamlit_enhanced import main
    main()
except ImportError as e:
    st.error(f"❌ Enhanced app not available: {e}")
    st.info("🔄 Loading fallback version...")
    
    try:
        # Fallback to simple version
        from streamlit_fallback import main as fallback_main
        fallback_main()
    except ImportError:
        # Ultimate fallback - basic interface
        st.title("🌍 AI Language Translator")
        st.error("❌ Unable to load translator modules")
        st.info("💡 Please check the deployment logs and try refreshing the page")
        
        # Basic translation interface
        text = st.text_area("Enter text:")
        if st.button("Translate") and text:
            try:
                import requests
                # Use a simple API call as last resort
                st.info("Translation service temporarily unavailable")
            except:
                st.error("All translation services unavailable")