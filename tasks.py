"""
Celery tasks for distributed translation processing
"""

from celery_config import celery_app
from core.translator import AITranslator
from core.caching import SharedModelCache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize shared translator (uses shared cache)
translator = AITranslator()


@celery_app.task(bind=True, name='tasks.translate_text')
def translate_text(self, text, source_lang='auto', target_lang='en'):
    """
    Celery task for translating a single text
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
    
    Returns:
        dict: Translation result
    """
    try:
        logger.info(f"Task {self.request.id}: Translating {len(text)} chars from {source_lang} to {target_lang}")
        
        result = translator.smart_translate(text, source_lang, target_lang)
        
        if result:
            logger.info(f"Task {self.request.id}: Success via {result['method']}")
            return {
                'success': True,
                'task_id': self.request.id,
                'original_text': text,
                'translation': result['translation'],
                'source_lang': result['source_lang'],
                'target_lang': target_lang,
                'method': result['method'],
                'confidence': result['confidence'],
                'time': result['time'],
                'cached': result.get('cached', False)
            }
        else:
            logger.error(f"Task {self.request.id}: Translation failed")
            return {
                'success': False,
                'task_id': self.request.id,
                'error': 'Translation failed'
            }
    
    except Exception as e:
        logger.error(f"Task {self.request.id}: Exception - {e}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@celery_app.task(bind=True, name='tasks.translate_batch')
def translate_batch(self, texts, source_lang='auto', target_lang='en'):
    """
    Celery task for batch translation
    
    Args:
        texts: List of texts to translate
        source_lang: Source language code
        target_lang: Target language code
    
    Returns:
        dict: Batch translation results
    """
    try:
        logger.info(f"Task {self.request.id}: Batch translating {len(texts)} texts")
        
        results = []
        for idx, text in enumerate(texts):
            if not text or not text.strip():
                results.append({
                    'success': False,
                    'index': idx,
                    'error': 'Empty text'
                })
                continue
            
            result = translator.smart_translate(text.strip(), source_lang, target_lang)
            
            if result:
                results.append({
                    'success': True,
                    'index': idx,
                    'original_text': text,
                    'translation': result['translation'],
                    'method': result['method'],
                    'confidence': result['confidence'],
                    'cached': result.get('cached', False)
                })
            else:
                results.append({
                    'success': False,
                    'index': idx,
                    'original_text': text,
                    'error': 'Translation failed'
                })
            
            # Update task progress
            self.update_state(
                state='PROGRESS',
                meta={'current': idx + 1, 'total': len(texts)}
            )
        
        logger.info(f"Task {self.request.id}: Batch complete - {len(results)} results")
        
        return {
            'success': True,
            'task_id': self.request.id,
            'total': len(texts),
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Task {self.request.id}: Batch exception - {e}")
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e)
        }


@celery_app.task(name='tasks.clear_cache')
def clear_cache():
    """Task to clear translation cache"""
    try:
        cache = SharedModelCache.get_cache()
        cache.clear_translations()
        logger.info("Cache cleared successfully")
        return {'success': True, 'message': 'Cache cleared'}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='tasks.get_cache_stats')
def get_cache_stats():
    """Task to get cache statistics"""
    try:
        cache = SharedModelCache.get_cache()
        stats = cache.get_cache_stats()
        return {'success': True, 'stats': stats}
    except Exception as e:
        logger.error(f"Get cache stats failed: {e}")
        return {'success': False, 'error': str(e)}
