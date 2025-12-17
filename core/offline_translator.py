"""
Offline-capable translator that prioritizes local AI models
"""

import os
from typing import Optional, Dict, Any
from .translator import AITranslator


class OfflineTranslator(AITranslator):
    """
    Translator that works offline using cached AI models
    Falls back to online services when offline models unavailable
    """
    
    def __init__(self, offline_mode: bool = None):
        """
        Initialize offline translator
        
        Args:
            offline_mode: Force offline mode (None = auto-detect from env)
        """
        super().__init__()
        
        # Determine offline mode
        if offline_mode is None:
            offline_mode = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
        
        self.offline_mode = offline_mode
        self.use_ai_models = os.getenv('USE_AI_MODELS', 'true').lower() == 'true'
        self.use_google_translate = os.getenv('USE_GOOGLE_TRANSLATE', 'true').lower() == 'true'
        self.use_mymemory = os.getenv('USE_MYMEMORY', 'true').lower() == 'true'
        
        # Available offline language pairs (Marian MT models)
        self.offline_pairs = {
            # English to other languages
            ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
            ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
            ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
            ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
            ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
            ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
            ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
            ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-jap',
            ('en', 'ko'): 'Helsinki-NLP/opus-mt-en-ko',
            ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
            ('en', 'hi'): 'Helsinki-NLP/opus-mt-en-hi',
            ('en', 'nl'): 'Helsinki-NLP/opus-mt-en-nl',
            ('en', 'sv'): 'Helsinki-NLP/opus-mt-en-sv',
            ('en', 'da'): 'Helsinki-NLP/opus-mt-en-da',
            ('en', 'no'): 'Helsinki-NLP/opus-mt-en-no',
            ('en', 'fi'): 'Helsinki-NLP/opus-mt-en-fi',
            ('en', 'pl'): 'Helsinki-NLP/opus-mt-en-pl',
            ('en', 'tr'): 'Helsinki-NLP/opus-mt-en-tr',
            
            # Other languages to English
            ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
            ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
            ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
            ('it', 'en'): 'Helsinki-NLP/opus-mt-it-en',
            ('pt', 'en'): 'Helsinki-NLP/opus-mt-pt-en',
            ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
            ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
            ('ja', 'en'): 'Helsinki-NLP/opus-mt-jap-en',
            ('ko', 'en'): 'Helsinki-NLP/opus-mt-ko-en',
            ('ar', 'en'): 'Helsinki-NLP/opus-mt-ar-en',
            ('hi', 'en'): 'Helsinki-NLP/opus-mt-hi-en',
            ('nl', 'en'): 'Helsinki-NLP/opus-mt-nl-en',
            ('sv', 'en'): 'Helsinki-NLP/opus-mt-sv-en',
            ('da', 'en'): 'Helsinki-NLP/opus-mt-da-en',
            ('no', 'en'): 'Helsinki-NLP/opus-mt-no-en',
            ('fi', 'en'): 'Helsinki-NLP/opus-mt-fi-en',
            ('pl', 'en'): 'Helsinki-NLP/opus-mt-pl-en',
            ('tr', 'en'): 'Helsinki-NLP/opus-mt-tr-en',
            
            # Romance languages (via English pivot)
            ('es', 'fr'): 'Helsinki-NLP/opus-mt-es-fr',
            ('fr', 'es'): 'Helsinki-NLP/opus-mt-fr-es',
            ('es', 'it'): 'Helsinki-NLP/opus-mt-es-it',
            ('it', 'es'): 'Helsinki-NLP/opus-mt-it-es',
            ('fr', 'de'): 'Helsinki-NLP/opus-mt-fr-de',
            ('de', 'fr'): 'Helsinki-NLP/opus-mt-de-fr',
        }
    
    def is_offline_available(self, source_lang: str, target_lang: str) -> bool:
        """
        Check if offline translation is available for language pair
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            True if offline model available
        """
        return (source_lang, target_lang) in self.offline_pairs
    
    def smart_translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict[str, Any]]:
        """
        Smart translation with offline preference
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Translation result dictionary
        """
        start_time = __import__('time').time()
        
        # Auto-detect language if needed
        if source_lang == 'auto':
            detected_lang, confidence = self.detect_language(text)
            source_lang = detected_lang
        
        # Check cache first (works offline)
        cached_result = self.cache.get_cached_translation(text, source_lang, target_lang)
        if cached_result:
            cached_result['time'] = __import__('time').time() - start_time
            cached_result['cached'] = True
            return cached_result
        
        # Try offline AI model first if available
        if self.use_ai_models and self.is_offline_available(source_lang, target_lang):
            ai_result, ai_method = self.translate_with_ai(text, source_lang, target_lang)
            if ai_result:
                result = {
                    'translation': ai_result,
                    'source_lang': source_lang,
                    'method': f"{ai_method} (Offline)",
                    'time': __import__('time').time() - start_time,
                    'confidence': 0.92,  # AI models are quite good
                    'cached': False,
                    'offline': True
                }
                # Cache the result
                self.cache.cache_translation(text, source_lang, target_lang, result)
                return result
        
        # If offline mode is forced, don't try online services
        if self.offline_mode:
            # Try English pivot for unsupported pairs
            if source_lang != 'en' and target_lang != 'en':
                pivot_result = self._translate_via_english_pivot(text, source_lang, target_lang)
                if pivot_result:
                    return pivot_result
            
            # Return fallback result
            return {
                'translation': text,  # Return original text
                'source_lang': source_lang,
                'method': 'Offline Fallback',
                'time': __import__('time').time() - start_time,
                'confidence': 0.1,
                'cached': False,
                'offline': True,
                'error': f'No offline model available for {source_lang} → {target_lang}'
            }
        
        # Fall back to online services
        if self.use_google_translate:
            google_result, detected_lang, google_method = self.translate_with_google(text, source_lang, target_lang)
            if google_result:
                result = {
                    'translation': google_result,
                    'source_lang': detected_lang,
                    'method': f"{google_method} (Online)",
                    'time': __import__('time').time() - start_time,
                    'confidence': 0.90,
                    'cached': False,
                    'offline': False
                }
                self.cache.cache_translation(text, source_lang, target_lang, result)
                return result
        
        if self.use_mymemory:
            mymemory_result, mymemory_method = self.translate_with_mymemory(text, source_lang, target_lang)
            if mymemory_result:
                result = {
                    'translation': mymemory_result,
                    'source_lang': source_lang,
                    'method': f"{mymemory_method} (Online)",
                    'time': __import__('time').time() - start_time,
                    'confidence': 0.80,
                    'cached': False,
                    'offline': False
                }
                self.cache.cache_translation(text, source_lang, target_lang, result)
                return result
        
        # All methods failed
        return None
    
    def _translate_via_english_pivot(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict[str, Any]]:
        """
        Translate via English pivot for unsupported language pairs
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
        
        Returns:
            Translation result or None
        """
        start_time = __import__('time').time()
        
        # Step 1: Translate to English
        if self.is_offline_available(source_lang, 'en'):
            english_result, method1 = self.translate_with_ai(text, source_lang, 'en')
            if not english_result:
                return None
        else:
            return None
        
        # Step 2: Translate from English to target
        if self.is_offline_available('en', target_lang):
            final_result, method2 = self.translate_with_ai(english_result, 'en', target_lang)
            if not final_result:
                return None
        else:
            return None
        
        # Return combined result
        result = {
            'translation': final_result,
            'source_lang': source_lang,
            'method': f"AI Model via English Pivot (Offline)",
            'time': __import__('time').time() - start_time,
            'confidence': 0.85,  # Slightly lower due to pivot
            'cached': False,
            'offline': True,
            'pivot': True
        }
        
        # Cache the final result
        self.cache.cache_translation(text, source_lang, target_lang, result)
        return result
    
    def get_offline_language_pairs(self) -> list:
        """
        Get list of supported offline language pairs
        
        Returns:
            List of (source, target) tuples
        """
        return list(self.offline_pairs.keys())
    
    def get_offline_languages(self) -> set:
        """
        Get set of languages supported offline
        
        Returns:
            Set of language codes
        """
        languages = set()
        for source, target in self.offline_pairs.keys():
            languages.add(source)
            languages.add(target)
        return languages
    
    def preload_models(self, language_pairs: list = None) -> dict:
        """
        Preload AI models for faster translation
        
        Args:
            language_pairs: List of (source, target) pairs to preload
                          If None, preloads common pairs
        
        Returns:
            Dictionary of loaded models and any errors
        """
        if language_pairs is None:
            # Preload common pairs
            language_pairs = [
                ('en', 'es'), ('es', 'en'),
                ('en', 'fr'), ('fr', 'en'),
                ('en', 'de'), ('de', 'en'),
                ('en', 'it'), ('it', 'en'),
                ('en', 'pt'), ('pt', 'en')
            ]
        
        results = {'loaded': [], 'errors': []}
        
        for source, target in language_pairs:
            if (source, target) in self.offline_pairs:
                model_name = self.offline_pairs[(source, target)]
                try:
                    tokenizer, model = self.load_ai_model(model_name)
                    if tokenizer and model:
                        results['loaded'].append((source, target, model_name))
                    else:
                        results['errors'].append((source, target, "Failed to load model"))
                except Exception as e:
                    results['errors'].append((source, target, str(e)))
        
        return results
    
    def get_status(self) -> dict:
        """
        Get offline translator status
        
        Returns:
            Status dictionary
        """
        return {
            'offline_mode': self.offline_mode,
            'use_ai_models': self.use_ai_models,
            'use_google_translate': self.use_google_translate,
            'use_mymemory': self.use_mymemory,
            'offline_pairs_available': len(self.offline_pairs),
            'offline_languages': len(self.get_offline_languages()),
            'cache_stats': self.cache.get_cache_stats()
        }