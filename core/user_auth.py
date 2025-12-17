"""
User Authentication and Session Management
Supports multiple authentication methods for personalized history
"""

import streamlit as st
import hashlib
import uuid
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import sqlite3


class UserManager:
    """
    Manages user authentication and sessions
    Supports multiple authentication methods
    """
    
    def __init__(self, db_path="users.db"):
        """Initialize user manager with SQLite database"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize user database schema"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    device_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_active INTEGER DEFAULT 1,
                    user_type TEXT DEFAULT 'registered'
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE NOT NULL,
                    device_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Guest sessions table (for device-only identification)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guest_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    session_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "ai_translator_salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_device_id(self) -> str:
        """Generate unique device ID"""
        # Try to get browser fingerprint or use random UUID
        if 'device_id' not in st.session_state:
            st.session_state.device_id = str(uuid.uuid4())
        return st.session_state.device_id
    
    def register_user(self, username: str, password: str, email: str = None) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            username: Unique username
            password: User password
            email: Optional email address
        
        Returns:
            Registration result
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Check if username exists
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return {"success": False, "error": "Username already exists"}
                
                # Check if email exists (if provided)
                if email:
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                    if cursor.fetchone():
                        return {"success": False, "error": "Email already registered"}
                
                # Create user
                password_hash = self._hash_password(password)
                device_id = self._generate_device_id()
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, device_id)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, device_id))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username,
                    "message": "Registration successful!"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login user with username/password
        
        Args:
            username: Username or email
            password: User password
        
        Returns:
            Login result with session info
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Find user by username or email
                cursor.execute("""
                    SELECT id, username, email, password_hash, device_id 
                    FROM users 
                    WHERE (username = ? OR email = ?) AND is_active = 1
                """, (username, username))
                
                user = cursor.fetchone()
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_id, db_username, email, stored_hash, device_id = user
                
                # Verify password
                if self._hash_password(password) != stored_hash:
                    return {"success": False, "error": "Invalid password"}
                
                # Create session
                session_token = str(uuid.uuid4())
                expires_at = datetime.now() + timedelta(days=30)  # 30-day session
                current_device = self._generate_device_id()
                
                cursor.execute("""
                    INSERT INTO sessions (user_id, session_token, device_id, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_token, current_device, expires_at))
                
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                """, (user_id,))
                
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": db_username,
                    "email": email,
                    "session_token": session_token,
                    "device_id": current_device,
                    "message": f"Welcome back, {db_username}!"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}
    
    def create_guest_session(self, session_name: str = None) -> Dict[str, Any]:
        """
        Create guest session for device-only identification
        
        Args:
            session_name: Optional friendly name for the session
        
        Returns:
            Guest session info
        """
        try:
            device_id = self._generate_device_id()
            
            if not session_name:
                session_name = f"Guest_{device_id[:8]}"
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Check if device already has a session
                cursor.execute("""
                    SELECT id, session_name FROM guest_sessions 
                    WHERE device_id = ? AND is_active = 1
                """, (device_id,))
                
                existing = cursor.fetchone()
                if existing:
                    # Update last used
                    cursor.execute("""
                        UPDATE guest_sessions 
                        SET last_used = CURRENT_TIMESTAMP 
                        WHERE device_id = ?
                    """, (device_id,))
                    conn.commit()
                    
                    return {
                        "success": True,
                        "session_type": "guest",
                        "device_id": device_id,
                        "session_name": existing[1],
                        "message": f"Welcome back, {existing[1]}!"
                    }
                
                # Create new guest session
                cursor.execute("""
                    INSERT INTO guest_sessions (device_id, session_name)
                    VALUES (?, ?)
                """, (device_id, session_name))
                
                conn.commit()
                
                return {
                    "success": True,
                    "session_type": "guest",
                    "device_id": device_id,
                    "session_name": session_name,
                    "message": f"Guest session created: {session_name}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Guest session failed: {str(e)}"}
    
    def verify_session(self, session_token: str = None, device_id: str = None) -> Dict[str, Any]:
        """
        Verify active session
        
        Args:
            session_token: Session token for registered users
            device_id: Device ID for guest sessions
        
        Returns:
            Session verification result
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                if session_token:
                    # Verify registered user session
                    cursor.execute("""
                        SELECT s.user_id, u.username, u.email, s.device_id, s.expires_at
                        FROM sessions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.session_token = ? AND s.is_active = 1 AND u.is_active = 1
                    """, (session_token,))
                    
                    session = cursor.fetchone()
                    if not session:
                        return {"success": False, "error": "Invalid session"}
                    
                    user_id, username, email, dev_id, expires_at = session
                    
                    # Check expiration
                    if datetime.fromisoformat(expires_at) < datetime.now():
                        return {"success": False, "error": "Session expired"}
                    
                    return {
                        "success": True,
                        "session_type": "registered",
                        "user_id": user_id,
                        "username": username,
                        "email": email,
                        "device_id": dev_id
                    }
                
                elif device_id:
                    # Verify guest session
                    cursor.execute("""
                        SELECT id, session_name FROM guest_sessions
                        WHERE device_id = ? AND is_active = 1
                    """, (device_id,))
                    
                    guest = cursor.fetchone()
                    if not guest:
                        return {"success": False, "error": "No guest session found"}
                    
                    return {
                        "success": True,
                        "session_type": "guest",
                        "device_id": device_id,
                        "session_name": guest[1]
                    }
                
                else:
                    return {"success": False, "error": "No session credentials provided"}
                    
        except Exception as e:
            return {"success": False, "error": f"Session verification failed: {str(e)}"}
    
    def logout_user(self, session_token: str = None, device_id: str = None) -> Dict[str, Any]:
        """
        Logout user or end guest session
        
        Args:
            session_token: Session token to invalidate
            device_id: Device ID for guest logout
        
        Returns:
            Logout result
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                if session_token:
                    cursor.execute("""
                        UPDATE sessions SET is_active = 0 WHERE session_token = ?
                    """, (session_token,))
                
                if device_id:
                    cursor.execute("""
                        UPDATE guest_sessions SET is_active = 0 WHERE device_id = ?
                    """, (device_id,))
                
                conn.commit()
                
                return {"success": True, "message": "Logged out successfully"}
                
        except Exception as e:
            return {"success": False, "error": f"Logout failed: {str(e)}"}
    
    def get_user_stats(self, user_id: int = None, device_id: str = None) -> Dict[str, Any]:
        """
        Get user statistics
        
        Args:
            user_id: Registered user ID
            device_id: Guest device ID
        
        Returns:
            User statistics
        """
        try:
            # This would integrate with the history manager
            # For now, return basic info
            return {
                "success": True,
                "total_translations": 0,
                "languages_used": [],
                "favorite_language_pair": None,
                "member_since": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class StreamlitAuth:
    """
    Streamlit-specific authentication UI and session management
    """
    
    def __init__(self):
        self.user_manager = UserManager()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state for auth"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'auth_method' not in st.session_state:
            st.session_state.auth_method = None
    
    def show_auth_ui(self) -> bool:
        """
        Show authentication UI and handle login/registration
        
        Returns:
            True if user is authenticated
        """
        if st.session_state.authenticated:
            return True
        
        st.markdown("### 🔐 User Authentication")
        
        # Authentication method selection
        auth_method = st.radio(
            "Choose authentication method:",
            options=["Guest (Device Only)", "Register Account", "Login to Account"],
            horizontal=True
        )
        
        if auth_method == "Guest (Device Only)":
            return self._handle_guest_auth()
        elif auth_method == "Register Account":
            return self._handle_registration()
        elif auth_method == "Login to Account":
            return self._handle_login()
        
        return False
    
    def _handle_guest_auth(self) -> bool:
        """Handle guest authentication"""
        st.markdown("#### 👤 Guest Mode")
        st.info("Your translation history will be saved to this device only.")
        
        session_name = st.text_input(
            "Session Name (optional):",
            placeholder="e.g., My Laptop, Work Computer",
            help="Give your device a friendly name"
        )
        
        if st.button("🚀 Start as Guest", type="primary"):
            result = self.user_manager.create_guest_session(session_name)
            
            if result["success"]:
                st.session_state.authenticated = True
                st.session_state.auth_method = "guest"
                st.session_state.user_info = result
                st.success(result["message"])
                st.rerun()
                return True
            else:
                st.error(result["error"])
        
        return False
    
    def _handle_registration(self) -> bool:
        """Handle user registration"""
        st.markdown("#### 📝 Create Account")
        
        with st.form("registration_form"):
            username = st.text_input("Username*:", help="Choose a unique username")
            email = st.text_input("Email (optional):", help="For account recovery")
            password = st.text_input("Password*:", type="password")
            confirm_password = st.text_input("Confirm Password*:", type="password")
            
            agree_terms = st.checkbox("I agree to the terms of service")
            
            submitted = st.form_submit_button("🎯 Create Account", type="primary")
            
            if submitted:
                if not username or not password:
                    st.error("Username and password are required")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not agree_terms:
                    st.error("Please agree to the terms of service")
                else:
                    result = self.user_manager.register_user(username, password, email)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.info("You can now login with your credentials")
                    else:
                        st.error(result["error"])
        
        return False
    
    def _handle_login(self) -> bool:
        """Handle user login"""
        st.markdown("#### 🔑 Login to Account")
        
        with st.form("login_form"):
            username = st.text_input("Username or Email:")
            password = st.text_input("Password:", type="password")
            
            submitted = st.form_submit_button("🚀 Login", type="primary")
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = self.user_manager.login_user(username, password)
                    
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.auth_method = "registered"
                        st.session_state.user_info = result
                        st.success(result["message"])
                        st.rerun()
                        return True
                    else:
                        st.error(result["error"])
        
        return False
    
    def show_user_info(self):
        """Show current user information"""
        if not st.session_state.authenticated:
            return
        
        user_info = st.session_state.user_info
        
        if st.session_state.auth_method == "guest":
            st.sidebar.markdown(f"👤 **{user_info['session_name']}**")
            st.sidebar.caption("Guest Mode")
        else:
            st.sidebar.markdown(f"👤 **{user_info['username']}**")
            if user_info.get('email'):
                st.sidebar.caption(f"📧 {user_info['email']}")
        
        if st.sidebar.button("🚪 Logout"):
            self.logout()
    
    def logout(self):
        """Logout current user"""
        user_info = st.session_state.user_info
        
        if st.session_state.auth_method == "registered":
            self.user_manager.logout_user(session_token=user_info.get('session_token'))
        else:
            self.user_manager.logout_user(device_id=user_info.get('device_id'))
        
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.auth_method = None
        
        st.success("Logged out successfully!")
        st.rerun()
    
    def get_user_id(self) -> str:
        """
        Get unique user identifier for history management
        
        Returns:
            User ID string (user_id for registered, device_id for guest)
        """
        if not st.session_state.authenticated:
            return None
        
        user_info = st.session_state.user_info
        
        if st.session_state.auth_method == "registered":
            return f"user_{user_info['user_id']}"
        else:
            return f"device_{user_info['device_id']}"
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.authenticated