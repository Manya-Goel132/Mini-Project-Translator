# 🔐 User Authentication & Personalized History Guide

## Overview

The AI Language Translator now supports user authentication with personalized translation history. Users can choose between registered accounts or guest sessions, with all translation history being user-specific and secure.

## Features

### 🎯 Authentication Methods

1. **Registered Accounts**
   - Username/email and password authentication
   - Persistent history across devices and sessions
   - 30-day session duration
   - Account recovery support (email-based)

2. **Guest Sessions**
   - Device-based identification
   - Local history storage tied to device
   - No registration required
   - Friendly device naming

### 🔒 Security Features

- Password hashing with salt
- Session token management
- SQL injection protection
- User data isolation
- Secure session expiration

### 📊 Personalized Features

- User-specific translation history
- Individual statistics and analytics
- Personal export/import capabilities
- Isolated cache and preferences

## Getting Started

### For New Users

1. **Open the Application**
   - Navigate to the AI Language Translator
   - You'll see the authentication screen

2. **Choose Authentication Method**
   - **Guest Mode**: Click "Start as Guest" for immediate access
   - **Create Account**: Fill out registration form
   - **Login**: Use existing credentials

3. **Start Translating**
   - All translations are automatically saved to your personal history
   - Access your statistics and history in the sidebar

### For Existing Users

1. **Login with Credentials**
   - Enter username/email and password
   - Sessions last 30 days for convenience

2. **Access Your History**
   - View personalized statistics
   - Export your translation history
   - Search through your translations

## User Interface

### Authentication Screen

```
🔐 User Authentication
Choose authentication method:
○ Guest (Device Only)  ○ Register Account  ○ Login to Account

[Authentication form based on selection]
```

### Sidebar User Info

**Registered Users:**
```
👤 username
📧 email@example.com
[🚪 Logout]
```

**Guest Users:**
```
👤 Device Name
Guest Mode
[🚪 Logout]
```

### Personalized Statistics

- **Your Translations**: Count of personal translations
- **Personal Analytics**: Confidence, speed, language preferences
- **Usage Patterns**: Most used language pairs, methods

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    device_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active INTEGER DEFAULT 1,
    user_type TEXT DEFAULT 'registered'
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_token TEXT UNIQUE NOT NULL,
    device_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Guest Sessions Table
```sql
CREATE TABLE guest_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    session_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);
```

### Enhanced Translations Table
```sql
CREATE TABLE translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,  -- New field for user identification
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
);
```

## API Reference

### UserManager Class

#### Registration
```python
result = user_manager.register_user(
    username="myuser",
    password="securepass",
    email="user@example.com"  # optional
)
```

#### Login
```python
result = user_manager.login_user(
    username="myuser",
    password="securepass"
)
```

#### Guest Session
```python
result = user_manager.create_guest_session(
    session_name="My Laptop"  # optional
)
```

#### Session Verification
```python
# For registered users
result = user_manager.verify_session(session_token="token")

# For guest users
result = user_manager.verify_session(device_id="device_id")
```

### HistoryManager Integration

#### Add Entry with User ID
```python
history_manager.add_entry(
    original_text="Hello world",
    translation_result=result,
    target_lang="es",
    user_id="user_123"  # New parameter
)
```

#### Get User-Specific History
```python
# Get recent translations for user
recent = history_manager.get_recent(count=10, user_id="user_123")

# Get user statistics
stats = history_manager.get_stats(user_id="user_123")

# Search user's history
results = history_manager.search(
    query="hello",
    user_id="user_123"
)
```

### StreamlitAuth Class

#### Initialize Authentication
```python
auth = StreamlitAuth()

# Check if authenticated
if not auth.is_authenticated():
    if auth.show_auth_ui():
        st.rerun()
    return

# Get current user ID
user_id = auth.get_user_id()
```

## Migration from Previous Version

### Automatic Migration

The system automatically handles migration:

1. **Existing History**: Preserved in database without user_id (accessible to all)
2. **New Translations**: Require authentication and are user-specific
3. **Database Schema**: Automatically updated with new columns

### Manual Migration (if needed)

```python
# Assign existing translations to a specific user
with history_manager._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE translations SET user_id = ? WHERE user_id IS NULL",
        ("legacy_user",)
    )
    conn.commit()
```

## Security Considerations

### Password Security
- Passwords are hashed using SHA-256 with salt
- Salt: "ai_translator_salt_2024"
- Minimum password length: 6 characters

### Session Security
- Session tokens are UUIDs (cryptographically secure)
- 30-day expiration for convenience
- Automatic cleanup of expired sessions

### Data Isolation
- User data is strictly isolated by user_id
- SQL injection protection through parameterized queries
- No cross-user data access

### Privacy
- Guest sessions use device-based identification
- No personal data required for guest mode
- Email is optional for registered users

## Troubleshooting

### Common Issues

1. **Authentication Module Not Available**
   ```
   ⚠️ Authentication module issue: No module named 'core.user_auth'
   ```
   - Ensure `core/user_auth.py` exists
   - Check Python path and imports

2. **Database Errors**
   ```
   Error adding history entry: database is locked
   ```
   - Check file permissions
   - Ensure no other processes are using the database

3. **Session Expired**
   ```
   Session expired
   ```
   - Login again to create a new session
   - Sessions last 30 days by default

### Reset Authentication

```python
# Clear all authentication data (development only)
import os
os.remove("users.db")  # Remove user database
os.remove("translator.db")  # Remove history database
```

## Configuration

### Environment Variables

```bash
# Optional: Custom database paths
export USER_DB_PATH="custom_users.db"
export HISTORY_DB_PATH="custom_history.db"

# Optional: Session duration (days)
export SESSION_DURATION_DAYS="30"
```

### Streamlit Configuration

```toml
# .streamlit/config.toml
[server]
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

## Best Practices

### For Users
1. Use strong passwords for registered accounts
2. Choose descriptive names for guest sessions
3. Regularly export your translation history
4. Logout when using shared devices

### For Developers
1. Always pass user_id to history operations
2. Handle authentication state changes gracefully
3. Implement proper error handling for auth failures
4. Test both registered and guest user flows

### For Deployment
1. Secure database files with proper permissions
2. Use HTTPS in production
3. Implement rate limiting for authentication
4. Monitor for suspicious login attempts

## Future Enhancements

### Planned Features
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] Social login (Google, GitHub)
- [ ] Team/organization accounts
- [ ] Advanced user roles and permissions
- [ ] Data export in multiple formats
- [ ] Translation sharing between users

### API Improvements
- [ ] RESTful API for external integrations
- [ ] Webhook support for real-time updates
- [ ] Bulk operations for enterprise users
- [ ] Advanced analytics and reporting

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test file: `test_user_auth.py`
3. Examine the implementation in `core/user_auth.py`
4. Test with the provided examples

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Compatibility**: Python 3.8+, Streamlit 1.28+