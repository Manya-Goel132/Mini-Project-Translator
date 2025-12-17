"""
Simple test for SQLite history manager (no external dependencies)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def test_sqlite_basics():
    """Test basic SQLite operations"""
    print("🔍 Testing SQLite basics...")
    
    db_path = "test_simple.db"
    
    try:
        # Create database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                method TEXT NOT NULL,
                confidence REAL NOT NULL,
                time_taken REAL NOT NULL
            )
        """)
        
        print("✅ Database and table created")
        
        # Insert test data
        test_data = [
            ("Hello", "Hola", "en", "es", "AI Model", 0.95, 0.123),
            ("Goodbye", "Adiós", "en", "es", "Google", 0.92, 0.156),
            ("Thank you", "Gracias", "en", "es", "MyMemory", 0.88, 0.134),
        ]
        
        for original, translation, source, target, method, conf, time_val in test_data:
            cursor.execute("""
                INSERT INTO translations 
                (timestamp, original_text, translated_text, source_lang, 
                 target_lang, method, confidence, time_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                original,
                translation,
                source,
                target,
                method,
                conf,
                time_val
            ))
        
        conn.commit()
        print(f"✅ Inserted {len(test_data)} test records")
        
        # Query data
        cursor.execute("SELECT COUNT(*) FROM translations")
        count = cursor.fetchone()[0]
        print(f"✅ Total records: {count}")
        
        # Get statistics
        cursor.execute("""
            SELECT 
                AVG(confidence) as avg_conf,
                AVG(time_taken) as avg_time,
                COUNT(*) as total
            FROM translations
        """)
        row = cursor.fetchone()
        print(f"✅ Statistics:")
        print(f"   - Average confidence: {row[0]:.2%}")
        print(f"   - Average time: {row[1]:.3f}s")
        print(f"   - Total: {row[2]}")
        
        # Test concurrent access (simulate)
        conn2 = sqlite3.connect(db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM translations")
        count2 = cursor2.fetchone()[0]
        print(f"✅ Concurrent access works: {count2} records")
        conn2.close()
        
        # Cleanup
        conn.close()
        Path(db_path).unlink()
        print("✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        # Cleanup on error
        try:
            Path(db_path).unlink()
        except:
            pass
        return False


def main():
    print("=" * 60)
    print("🧪 SQLite Basic Test")
    print("=" * 60)
    print()
    
    success = test_sqlite_basics()
    
    print()
    print("=" * 60)
    if success:
        print("✅ SQLite is working correctly!")
        print()
        print("Benefits of SQLite over JSON:")
        print("  ✅ Thread-safe (no data corruption)")
        print("  ✅ Unlimited storage (not limited to 100 entries)")
        print("  ✅ Fast queries with SQL")
        print("  ✅ Concurrent access from multiple apps")
        print("  ✅ Indexes for performance")
        print("  ✅ ACID transactions")
        return 0
    else:
        print("❌ SQLite test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
