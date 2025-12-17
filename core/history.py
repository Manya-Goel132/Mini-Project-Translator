"""
Translation history management with SQLite database
Thread-safe, scalable, and production-ready
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from contextlib import contextmanager
import threading


class HistoryManager:
    """
    Manages translation history using SQLite database
    Thread-safe with connection pooling and proper locking
    """
    
    def __init__(self, db_path="translator.db"):
        """
        Initialize history manager with SQLite database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # Initialize database schema
        self._init_database()
        
        # Migrate from JSON if exists
        self._migrate_from_json()
    
    @contextmanager
    def _get_connection(self):
        """
        Get thread-safe database connection
        Uses thread-local storage to ensure each thread has its own connection
        """
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10.0
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise e
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create translations table
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
                    time_taken REAL NOT NULL,
                    text_length INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    cached INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON translations(date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_target 
                ON translations(source_lang, target_lang)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON translations(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_method 
                ON translations(method)
            """)
            
            conn.commit()
    
    def _migrate_from_json(self):
        """Migrate existing JSON history to SQLite (one-time operation)"""
        json_file = Path("translation_history/translation_history.json")
        
        if not json_file.exists():
            return
        
        try:
            # Check if already migrated
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM translations")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Already has data, skip migration
                    return
            
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if not json_data:
                return
            
            # Migrate to SQLite
            print(f"🔄 Migrating {len(json_data)} entries from JSON to SQLite...")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for entry in json_data:
                    cursor.execute("""
                        INSERT INTO translations 
                        (timestamp, original_text, translated_text, source_lang, 
                         target_lang, method, confidence, time_taken, text_length, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.get('timestamp', datetime.now().isoformat()),
                        entry.get('original_text', ''),
                        entry.get('translated_text', ''),
                        entry.get('source_lang', 'unknown'),
                        entry.get('target_lang', 'unknown'),
                        entry.get('method', 'unknown'),
                        entry.get('confidence', 0.0),
                        entry.get('time_taken', 0.0),
                        entry.get('text_length', 0),
                        entry.get('date', datetime.now().strftime('%Y-%m-%d'))
                    ))
                
                conn.commit()
            
            print(f"✅ Migration complete! {len(json_data)} entries migrated.")
            
            # Backup and remove JSON file
            backup_file = json_file.with_suffix('.json.backup')
            json_file.rename(backup_file)
            print(f"📦 JSON file backed up to: {backup_file}")
            
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
    
    def add_entry(self, original_text, translation_result, target_lang):
        """
        Add a translation entry to database
        Thread-safe with automatic retry
        
        Args:
            original_text: Original text
            translation_result: Translation result dict
            target_lang: Target language code
        
        Returns:
            bool: Success status
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO translations 
                    (timestamp, original_text, translated_text, source_lang, 
                     target_lang, method, confidence, time_taken, text_length, 
                     date, cached)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    original_text[:5000],  # Increased limit
                    translation_result['translation'][:5000],
                    translation_result['source_lang'],
                    target_lang,
                    translation_result['method'],
                    translation_result['confidence'],
                    translation_result['time'],
                    len(original_text),
                    datetime.now().strftime('%Y-%m-%d'),
                    1 if translation_result.get('cached', False) else 0
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding history entry: {e}")
            return False
    
    def get_stats(self):
        """
        Get translation statistics using SQL aggregation
        Much faster than loading all data into memory
        
        Returns:
            dict: Statistics dictionary
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total translations
                cursor.execute("SELECT COUNT(*) FROM translations")
                total = cursor.fetchone()[0]
                
                if total == 0:
                    return None
                
                # Average confidence and time
                cursor.execute("""
                    SELECT 
                        AVG(confidence) as avg_confidence,
                        AVG(time_taken) as avg_time
                    FROM translations
                """)
                row = cursor.fetchone()
                avg_confidence = row[0] or 0
                avg_time = row[1] or 0
                
                # Most used languages
                cursor.execute("""
                    SELECT source_lang, COUNT(*) as count 
                    FROM translations 
                    GROUP BY source_lang 
                    ORDER BY count DESC 
                    LIMIT 1
                """)
                most_source = cursor.fetchone()
                most_used_source = most_source[0] if most_source else 'N/A'
                
                cursor.execute("""
                    SELECT target_lang, COUNT(*) as count 
                    FROM translations 
                    GROUP BY target_lang 
                    ORDER BY count DESC 
                    LIMIT 1
                """)
                most_target = cursor.fetchone()
                most_used_target = most_target[0] if most_target else 'N/A'
                
                # Methods used
                cursor.execute("""
                    SELECT method, COUNT(*) as count 
                    FROM translations 
                    GROUP BY method
                """)
                methods_used = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Unique languages
                cursor.execute("""
                    SELECT COUNT(DISTINCT source_lang) 
                    FROM translations
                """)
                languages_translated = cursor.fetchone()[0]
                
                # Today's translations
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM translations 
                    WHERE date = ?
                """, (today,))
                today_translations = cursor.fetchone()[0]
                
                # High confidence translations
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM translations 
                    WHERE confidence > 0.9
                """)
                high_confidence = cursor.fetchone()[0]
                
                # Cache hit rate
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) 
                    FROM translations
                """)
                cache_hit_rate = cursor.fetchone()[0] or 0
                
                return {
                    'total_translations': total,
                    'avg_confidence': avg_confidence,
                    'avg_time': avg_time,
                    'most_used_source': most_used_source,
                    'most_used_target': most_used_target,
                    'methods_used': methods_used,
                    'languages_translated': languages_translated,
                    'today_translations': today_translations,
                    'high_confidence_translations': high_confidence,
                    'cache_hit_rate': cache_hit_rate
                }
                
        except Exception as e:
            print(f"Error getting stats: {e}")
            return None
    
    def export_history(self, format_type='json', limit=None):
        """
        Export history in different formats
        
        Args:
            format_type: 'json' or 'csv'
            limit: Maximum number of records (None for all)
        
        Returns:
            str: Exported data
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM translations ORDER BY timestamp DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    return None
                
                if format_type == 'json':
                    return df.to_json(orient='records', indent=2)
                elif format_type == 'csv':
                    return df.to_csv(index=False)
                
        except Exception as e:
            print(f"Error exporting history: {e}")
            return None
    
    def clear_history(self):
        """
        Clear all translation history
        
        Returns:
            bool: Success status
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM translations")
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def get_recent(self, count=10):
        """
        Get recent translations
        
        Args:
            count: Number of recent entries
        
        Returns:
            list: List of translation dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM translations 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (count,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting recent history: {e}")
            return []
    
    def get_all(self):
        """
        Get all translation history
        WARNING: Can be slow for large databases
        
        Returns:
            list: List of all translation dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM translations ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting all history: {e}")
            return []
    
    def search(self, query, field='original_text', limit=100):
        """
        Search translations by text
        
        Args:
            query: Search query
            field: Field to search ('original_text' or 'translated_text')
            limit: Maximum results
        
        Returns:
            list: Matching translations
        """
        # Whitelist allowed fields to prevent SQL injection
        allowed_fields = {'original_text', 'translated_text'}
        if field not in allowed_fields:
            field = 'original_text'
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT * FROM translations 
                    WHERE {field} LIKE ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (f'%{query}%', limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error searching history: {e}")
            return []
    
    def get_by_language_pair(self, source_lang, target_lang, limit=100):
        """
        Get translations for specific language pair
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            limit: Maximum results
        
        Returns:
            list: Matching translations
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM translations 
                    WHERE source_lang = ? AND target_lang = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (source_lang, target_lang, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting language pair history: {e}")
            return []
    
    def get_database_size(self):
        """
        Get database file size
        
        Returns:
            dict: Size information
        """
        try:
            size_bytes = self.db_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM translations")
                count = cursor.fetchone()[0]
            
            return {
                'size_bytes': size_bytes,
                'size_mb': round(size_mb, 2),
                'size_human': f"{size_mb:.2f} MB" if size_mb > 1 else f"{size_bytes / 1024:.2f} KB",
                'record_count': count,
                'avg_size_per_record': round(size_bytes / count, 2) if count > 0 else 0
            }
            
        except Exception as e:
            print(f"Error getting database size: {e}")
            return None
    
    def vacuum(self):
        """
        Optimize database (reclaim space after deletions)
        
        Returns:
            bool: Success status
        """
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error vacuuming database: {e}")
            return False
