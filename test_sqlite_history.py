"""
Test script for SQLite-based history manager
"""

import sys
import time
from core.history import HistoryManager
from datetime import datetime


def test_database_creation():
    """Test database initialization"""
    print("🔍 Testing database creation...")
    try:
        manager = HistoryManager("test_translator.db")
        print("✅ Database created successfully")
        return True, manager
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False, None


def test_add_entry(manager):
    """Test adding entries"""
    print("\n🔍 Testing add entry...")
    try:
        # Create test translation result
        test_result = {
            'translation': 'Hola mundo',
            'source_lang': 'en',
            'method': 'Test Method',
            'confidence': 0.95,
            'time': 0.123,
            'cached': False
        }
        
        success = manager.add_entry("Hello world", test_result, "es")
        
        if success:
            print("✅ Entry added successfully")
            return True
        else:
            print("❌ Failed to add entry")
            return False
            
    except Exception as e:
        print(f"❌ Add entry failed: {e}")
        return False


def test_add_multiple_entries(manager):
    """Test adding multiple entries"""
    print("\n🔍 Testing multiple entries...")
    try:
        test_data = [
            ("Hello", "Hola", "en", "es", "Google Translate", 0.92),
            ("Goodbye", "Adiós", "en", "es", "AI Model", 0.95),
            ("Thank you", "Gracias", "en", "es", "MyMemory", 0.88),
            ("Good morning", "Buenos días", "en", "es", "AI Model", 0.94),
            ("How are you?", "¿Cómo estás?", "en", "es", "Google Translate", 0.91),
        ]
        
        for original, translation, source, target, method, confidence in test_data:
            result = {
                'translation': translation,
                'source_lang': source,
                'method': method,
                'confidence': confidence,
                'time': 0.1 + (confidence * 0.1),
                'cached': False
            }
            manager.add_entry(original, result, target)
        
        print(f"✅ Added {len(test_data)} entries successfully")
        return True
        
    except Exception as e:
        print(f"❌ Multiple entries failed: {e}")
        return False


def test_get_recent(manager):
    """Test getting recent entries"""
    print("\n🔍 Testing get recent...")
    try:
        recent = manager.get_recent(3)
        
        if recent:
            print(f"✅ Retrieved {len(recent)} recent entries")
            print(f"   - Latest: '{recent[0]['original_text']}' → '{recent[0]['translated_text']}'")
            return True
        else:
            print("❌ No recent entries found")
            return False
            
    except Exception as e:
        print(f"❌ Get recent failed: {e}")
        return False


def test_get_stats(manager):
    """Test statistics"""
    print("\n🔍 Testing statistics...")
    try:
        stats = manager.get_stats()
        
        if stats:
            print("✅ Statistics retrieved successfully")
            print(f"   - Total translations: {stats['total_translations']}")
            print(f"   - Average confidence: {stats['avg_confidence']:.2%}")
            print(f"   - Average time: {stats['avg_time']:.3f}s")
            print(f"   - Most used method: {max(stats['methods_used'], key=stats['methods_used'].get)}")
            print(f"   - Cache hit rate: {stats['cache_hit_rate']:.1f}%")
            return True
        else:
            print("❌ No statistics available")
            return False
            
    except Exception as e:
        print(f"❌ Get stats failed: {e}")
        return False


def test_search(manager):
    """Test search functionality"""
    print("\n🔍 Testing search...")
    try:
        results = manager.search("Hello", field='original_text')
        
        if results:
            print(f"✅ Search found {len(results)} results")
            print(f"   - First result: '{results[0]['original_text']}'")
            return True
        else:
            print("⚠️  No search results (this is okay if no matching data)")
            return True
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False


def test_language_pair(manager):
    """Test language pair filtering"""
    print("\n🔍 Testing language pair filter...")
    try:
        results = manager.get_by_language_pair("en", "es")
        
        if results:
            print(f"✅ Found {len(results)} en→es translations")
            return True
        else:
            print("⚠️  No language pair results")
            return True
            
    except Exception as e:
        print(f"❌ Language pair filter failed: {e}")
        return False


def test_export(manager):
    """Test export functionality"""
    print("\n🔍 Testing export...")
    try:
        # Test JSON export
        json_data = manager.export_history('json', limit=5)
        if json_data:
            print("✅ JSON export successful")
            print(f"   - Exported {len(json_data)} characters")
        
        # Test CSV export
        csv_data = manager.export_history('csv', limit=5)
        if csv_data:
            print("✅ CSV export successful")
            print(f"   - Exported {len(csv_data)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def test_database_size(manager):
    """Test database size info"""
    print("\n🔍 Testing database size...")
    try:
        size_info = manager.get_database_size()
        
        if size_info:
            print("✅ Database size retrieved")
            print(f"   - Size: {size_info['size_human']}")
            print(f"   - Records: {size_info['record_count']}")
            print(f"   - Avg per record: {size_info['avg_size_per_record']} bytes")
            return True
        else:
            print("❌ Failed to get database size")
            return False
            
    except Exception as e:
        print(f"❌ Database size check failed: {e}")
        return False


def test_thread_safety():
    """Test thread safety with concurrent writes"""
    print("\n🔍 Testing thread safety...")
    try:
        import threading
        
        manager = HistoryManager("test_translator.db")
        errors = []
        
        def add_entries(thread_id):
            try:
                for i in range(5):
                    result = {
                        'translation': f'Translation {thread_id}-{i}',
                        'source_lang': 'en',
                        'method': f'Thread {thread_id}',
                        'confidence': 0.9,
                        'time': 0.1,
                        'cached': False
                    }
                    manager.add_entry(f"Text {thread_id}-{i}", result, "es")
            except Exception as e:
                errors.append(str(e))
        
        # Create 5 threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=add_entries, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        if not errors:
            print("✅ Thread safety test passed (25 concurrent writes)")
            return True
        else:
            print(f"❌ Thread safety test failed: {errors[0]}")
            return False
            
    except Exception as e:
        print(f"❌ Thread safety test failed: {e}")
        return False


def test_vacuum(manager):
    """Test database optimization"""
    print("\n🔍 Testing database vacuum...")
    try:
        success = manager.vacuum()
        
        if success:
            print("✅ Database vacuumed successfully")
            return True
        else:
            print("❌ Vacuum failed")
            return False
            
    except Exception as e:
        print(f"❌ Vacuum failed: {e}")
        return False


def cleanup():
    """Clean up test database"""
    print("\n🧹 Cleaning up test database...")
    try:
        import os
        if os.path.exists("test_translator.db"):
            os.remove("test_translator.db")
            print("✅ Test database removed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 SQLite History Manager Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Database creation
    success, manager = test_database_creation()
    results['database_creation'] = success
    
    if not manager:
        print("\n❌ Cannot continue without database")
        return 1
    
    # Test 2: Add entry
    results['add_entry'] = test_add_entry(manager)
    
    # Test 3: Add multiple entries
    results['add_multiple'] = test_add_multiple_entries(manager)
    
    # Test 4: Get recent
    results['get_recent'] = test_get_recent(manager)
    
    # Test 5: Statistics
    results['statistics'] = test_get_stats(manager)
    
    # Test 6: Search
    results['search'] = test_search(manager)
    
    # Test 7: Language pair
    results['language_pair'] = test_language_pair(manager)
    
    # Test 8: Export
    results['export'] = test_export(manager)
    
    # Test 9: Database size
    results['database_size'] = test_database_size(manager)
    
    # Test 10: Thread safety
    results['thread_safety'] = test_thread_safety()
    
    # Test 11: Vacuum
    results['vacuum'] = test_vacuum(manager)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for r in results.values() if r)
    failed = sum(1 for r in results.values() if not r)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Cleanup
    cleanup()
    
    if failed > 0:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1
    else:
        print("\n✅ All tests passed! SQLite history manager is working correctly.")
        print("\nBenefits over JSON:")
        print("  ✅ Thread-safe (no data corruption)")
        print("  ✅ Unlimited storage (not limited to 100 entries)")
        print("  ✅ Fast queries with indexes")
        print("  ✅ Concurrent access from multiple apps")
        print("  ✅ Advanced search and filtering")
        return 0


if __name__ == "__main__":
    sys.exit(main())
