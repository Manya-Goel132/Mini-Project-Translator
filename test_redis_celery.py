"""
Test script to verify Redis and Celery setup
"""

import sys
import time
from core.caching import SharedModelCache
from tasks import translate_text, translate_batch, get_cache_stats
from celery.result import AsyncResult


def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    try:
        cache = SharedModelCache.get_cache()
        stats = cache.get_cache_stats()
        
        if stats['redis_connected']:
            print("✅ Redis is connected")
            print(f"   - Redis enabled: {stats['redis_enabled']}")
            print(f"   - Models cached: {stats['models_cached']}")
            return True
        else:
            print("❌ Redis is not connected")
            print("   Using disk cache fallback")
            return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_cache_operations():
    """Test cache read/write"""
    print("\n🔍 Testing cache operations...")
    try:
        cache = SharedModelCache.get_cache()
        
        # Test translation cache
        test_result = {
            'translation': 'Hola mundo',
            'method': 'Test',
            'confidence': 0.95,
            'time': 0.1
        }
        
        cache.cache_translation("Hello world", "en", "es", test_result)
        print("✅ Cache write successful")
        
        cached = cache.get_cached_translation("Hello world", "en", "es")
        if cached and cached['translation'] == 'Hola mundo':
            print("✅ Cache read successful")
            return True
        else:
            print("❌ Cache read failed")
            return False
    except Exception as e:
        print(f"❌ Cache operations failed: {e}")
        return False


def test_celery_worker():
    """Test if Celery worker is running"""
    print("\n🔍 Testing Celery worker...")
    try:
        from celery_config import celery_app
        
        # Check active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Celery worker is running")
            print(f"   - Active workers: {len(active_workers)}")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
            return True
        else:
            print("❌ No Celery workers found")
            print("   Start worker with: celery -A tasks worker --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Celery worker check failed: {e}")
        return False


def test_simple_task():
    """Test a simple translation task"""
    print("\n🔍 Testing simple translation task...")
    try:
        # Queue a task
        task = translate_text.delay("Hello world", "en", "es")
        print(f"✅ Task queued: {task.id}")
        
        # Wait for result (with timeout)
        print("   Waiting for result...")
        result = task.get(timeout=30)
        
        if result['success']:
            print(f"✅ Translation successful")
            print(f"   - Original: Hello world")
            print(f"   - Translation: {result['translation']}")
            print(f"   - Method: {result['method']}")
            print(f"   - Cached: {result.get('cached', False)}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        return False


def test_batch_task():
    """Test batch translation task"""
    print("\n🔍 Testing batch translation task...")
    try:
        texts = ["Hello", "World", "How are you?"]
        
        # Queue batch task
        task = translate_batch.delay(texts, "en", "es")
        print(f"✅ Batch task queued: {task.id}")
        
        # Wait for result
        print("   Waiting for result...")
        result = task.get(timeout=60)
        
        if result['success']:
            print(f"✅ Batch translation successful")
            print(f"   - Total texts: {result['total']}")
            
            successful = sum(1 for r in result['results'] if r['success'])
            print(f"   - Successful: {successful}/{result['total']}")
            
            # Show first result
            if result['results']:
                first = result['results'][0]
                if first['success']:
                    print(f"   - Example: '{first['original_text']}' → '{first['translation']}'")
            
            return True
        else:
            print(f"❌ Batch translation failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Batch task execution failed: {e}")
        return False


def test_cache_stats_task():
    """Test cache stats task"""
    print("\n🔍 Testing cache stats task...")
    try:
        task = get_cache_stats.delay()
        result = task.get(timeout=10)
        
        if result['success']:
            print("✅ Cache stats retrieved")
            stats = result['stats']
            print(f"   - Models cached: {stats.get('models_cached', 0)}")
            print(f"   - Redis connected: {stats.get('redis_connected', False)}")
            if 'translations_cached_redis' in stats:
                print(f"   - Translations in Redis: {stats['translations_cached_redis']}")
            if 'translations_cached_disk' in stats:
                print(f"   - Translations on disk: {stats['translations_cached_disk']}")
            return True
        else:
            print(f"❌ Cache stats failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Cache stats task failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Redis & Celery Setup Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Redis connection
    results['redis'] = test_redis_connection()
    
    # Test 2: Cache operations
    results['cache'] = test_cache_operations()
    
    # Test 3: Celery worker
    results['worker'] = test_celery_worker()
    
    # Only run task tests if worker is available
    if results['worker']:
        # Test 4: Simple task
        results['simple_task'] = test_simple_task()
        
        # Test 5: Batch task
        results['batch_task'] = test_batch_task()
        
        # Test 6: Cache stats task
        results['stats_task'] = test_cache_stats_task()
    else:
        print("\n⚠️  Skipping task tests (no worker available)")
        results['simple_task'] = None
        results['batch_task'] = None
        results['stats_task'] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        
        print(f"{status} - {test_name}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    if failed > 0:
        print("\n❌ Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("  - Redis not running: redis-server")
        print("  - Celery worker not running: celery -A tasks worker --loglevel=info")
        print("  - Dependencies not installed: pip install -r requirements.txt")
        return 1
    elif passed == 0:
        print("\n⚠️  No tests passed. Please check your setup.")
        return 1
    else:
        print("\n✅ All tests passed! Your setup is working correctly.")
        print("\nYou can now:")
        print("  - Start all services: ./start_services.sh")
        print("  - Use the Streamlit app: streamlit run app_streamlit.py")
        print("  - Use the API: python api_server.py")
        print("  - Run batch jobs: python app_batch_celery.py input.csv output.csv --text-column text")
        return 0


if __name__ == "__main__":
    sys.exit(main())
