#!/usr/bin/env python3
"""
Test script for user authentication system
"""

import os
import sys
from pathlib import Path

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from user_auth import UserManager, StreamlitAuth
from history import HistoryManager

def test_user_manager():
    """Test UserManager functionality"""
    print("🧪 Testing UserManager...")
    
    # Use test database
    user_manager = UserManager("test_users.db")
    
    # Test user registration
    print("\n1. Testing user registration...")
    result = user_manager.register_user("testuser", "password123", "test@example.com")
    print(f"Registration result: {result}")
    
    # Test duplicate registration
    print("\n2. Testing duplicate registration...")
    result = user_manager.register_user("testuser", "password456", "test2@example.com")
    print(f"Duplicate registration result: {result}")
    
    # Test user login
    print("\n3. Testing user login...")
    result = user_manager.login_user("testuser", "password123")
    print(f"Login result: {result}")
    
    if result["success"]:
        session_token = result["session_token"]
        user_id = result["user_id"]
        
        # Test session verification
        print("\n4. Testing session verification...")
        verify_result = user_manager.verify_session(session_token=session_token)
        print(f"Session verification: {verify_result}")
        
        # Test logout
        print("\n5. Testing logout...")
        logout_result = user_manager.logout_user(session_token=session_token)
        print(f"Logout result: {logout_result}")
    
    # Test guest session
    print("\n6. Testing guest session...")
    guest_result = user_manager.create_guest_session("Test Device")
    print(f"Guest session result: {guest_result}")
    
    if guest_result["success"]:
        device_id = guest_result["device_id"]
        
        # Test guest verification
        print("\n7. Testing guest verification...")
        guest_verify = user_manager.verify_session(device_id=device_id)
        print(f"Guest verification: {guest_verify}")
    
    print("\n✅ UserManager tests completed!")

def test_history_integration():
    """Test history integration with user authentication"""
    print("\n🧪 Testing History Integration...")
    
    # Use test databases
    user_manager = UserManager("test_users.db")
    history_manager = HistoryManager("test_history.db")
    
    # Create test users
    user1 = user_manager.register_user("user1", "pass1")
    user2 = user_manager.register_user("user2", "pass2")
    
    if user1["success"] and user2["success"]:
        user1_id = f"user_{user1['user_id']}"
        user2_id = f"user_{user2['user_id']}"
        
        # Add translations for each user
        print("\n1. Adding translations for users...")
        
        # Mock translation result
        mock_result = {
            'translation': 'Hola mundo',
            'source_lang': 'en',
            'method': 'google',
            'confidence': 0.95,
            'time': 0.5,
            'cached': False
        }
        
        # Add entries for user1
        history_manager.add_entry("Hello world", mock_result, "es", user_id=user1_id)
        history_manager.add_entry("Good morning", mock_result, "es", user_id=user1_id)
        
        # Add entries for user2
        history_manager.add_entry("Hello world", mock_result, "fr", user_id=user2_id)
        
        # Test user-specific history retrieval
        print("\n2. Testing user-specific history...")
        user1_history = history_manager.get_all(user_id=user1_id)
        user2_history = history_manager.get_all(user_id=user2_id)
        
        print(f"User1 has {len(user1_history)} translations")
        print(f"User2 has {len(user2_history)} translations")
        
        # Test user-specific stats
        print("\n3. Testing user-specific stats...")
        user1_stats = history_manager.get_stats(user_id=user1_id)
        user2_stats = history_manager.get_stats(user_id=user2_id)
        
        print(f"User1 stats: {user1_stats}")
        print(f"User2 stats: {user2_stats}")
        
        print("\n✅ History integration tests completed!")
    else:
        print("❌ Failed to create test users")

def cleanup_test_files():
    """Clean up test database files"""
    test_files = ["test_users.db", "test_history.db"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ Cleaned up {file}")

if __name__ == "__main__":
    print("🚀 Starting User Authentication Tests")
    print("=" * 50)
    
    try:
        test_user_manager()
        test_history_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Cleaning up test files...")
        cleanup_test_files()
        print("✅ Cleanup completed!")