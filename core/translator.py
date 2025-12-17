"""
Core translation logic - handles AI models and translation APIs
"""

import torch
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator, MyMemoryTranslator
import time
import re


class AITranslator:
    """Core translator class - handles only translation logic"""
    
    def __init__(self, shared_cache=None):
        """
        Initialize translator with optional shared cache
        
        Args:
            shared_cache: ModelCache instance for shared caching (optional)
        """
        # Use shared cache if provided, otherwise create local cache
        if shared_cache:
            self.cache = shared_cache
        else:
            # Import here to avoid circular dependency
            from .caching import SharedModelCache
            self.cache = SharedModelCache.get_cache()
        
        self.supported_languages = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
            'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian',
            'fi': 'Finnish', 'pl': 'Polish', 'tr': 'Turkish', 'th': 'Thai'
        }
    
    def load_ai_model(self, model_name):
        """Load and cache AI translation models"""
        # Check cache first
        cached_model = self.cache.get_model(model_name)
        if cached_model:
            return cached_model
        
        try:
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            model_data = (tokenizer, model)
            self.cache.set_model(model_name, model_data)
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
                
                return result, "AI Model (Marian)"
        except Exception:
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
                
            except Exception:
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
        """Smart translation with fallback chain and caching"""
        start_time = time.time()
        
        # Auto-detect language if needed
        if source_lang == 'auto':
            detected_lang, confidence = self.detect_language(text)
            source_lang = detected_lang
        
        # Check cache first
        cached_result = self.cache.get_cached_translation(text, source_lang, target_lang)
        if cached_result:
            cached_result['time'] = time.time() - start_time
            cached_result['cached'] = True
            return cached_result
        
        # Try AI model first
        ai_result, ai_method = self.translate_with_ai(text, source_lang, target_lang)
        if ai_result:
            result = {
                'translation': ai_result,
                'source_lang': source_lang,
                'method': ai_method,
                'time': time.time() - start_time,
                'confidence': 0.95,
                'cached': False
            }
            # Cache the result
            self.cache.cache_translation(text, source_lang, target_lang, result)
            return result
        
        # Fallback to Google Translate
        google_result, detected_lang, google_method = self.translate_with_google(text, source_lang, target_lang)
        if google_result:
            result = {
                'translation': google_result,
                'source_lang': detected_lang,
                'method': google_method,
                'time': time.time() - start_time,
                'confidence': 0.90,
                'cached': False
            }
            # Cache the result
            self.cache.cache_translation(text, source_lang, target_lang, result)
            return result
        
        # Last resort: MyMemory
        mymemory_result, mymemory_method = self.translate_with_mymemory(text, source_lang, target_lang)
        if mymemory_result:
            result = {
                'translation': mymemory_result,
                'source_lang': source_lang,
                'method': mymemory_method,
                'time': time.time() - start_time,
                'confidence': 0.80,
                'cached': False
            }
            # Cache the result
            self.cache.cache_translation(text, source_lang, target_lang, result)
            return result
        
        return None
    
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
