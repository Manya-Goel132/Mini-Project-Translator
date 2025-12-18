# 🍎 macOS Setup Guide - AI Language Translator

> **Complete setup guide for first-time users on macOS**

## 📋 Prerequisites Check

Before starting, ensure you have:
- macOS 10.14+ (Mojave or later)
- At least 4GB free disk space
- Internet connection for initial setup

## 🚀 Step-by-Step Setup

### Step 1: Install Homebrew (if not already installed)

```bash
# Check if Homebrew is installed
brew --version

# If not installed, install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (for Apple Silicon Macs)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

### Step 2: Install Python 3.9+

```bash
# Install Python via Homebrew
brew install python@3.11

# Verify Python installation
python3 --version
# Should show: Python 3.11.x

# Install pip if not available
python3 -m ensurepip --upgrade
```

### Step 3: Install Redis Server

```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG

# Optional: Check Redis status
brew services list | grep redis
```

### Step 4: Install System Dependencies

```bash
# Install audio system dependencies
brew install portaudio
brew install ffmpeg

# Install speech recognition dependencies (optional but recommended)
brew install flac
brew install espeak

# For offline TTS support
brew install festival
```

### Step 5: Clone the Repository

```bash
# Navigate to your preferred directory
cd ~/Downloads  # or wherever you want the project

# Clone the repository
git clone https://github.com/Manya-Goel132/Mini-Project-Translator.git

# Navigate to project directory
cd Mini-Project-Translator

# Verify you're in the right directory
ls -la
# Should see files like app_streamlit_enhanced.py, requirements.txt, etc.
```

### Step 6: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv translator_env

# Activate virtual environment
source translator_env/bin/activate

# Verify virtual environment is active (should show (translator_env) in prompt)
which python
# Should show: /path/to/Mini-Project-Translator/translator_env/bin/python
```

### Step 7: Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify key packages are installed
pip list | grep -E "(streamlit|fastapi|redis|celery)"
```

### Step 8: Test the Installation

```bash
# Test Redis connection
python3 -c "import redis; r = redis.Redis(); print('Redis:', r.ping())"

# Test core modules
python3 -c "from core.translator import AITranslator; print('✅ Translator module works')"
python3 -c "from core.history import HistoryManager; print('✅ History module works')"
python3 -c "from core.user_auth import UserManager; print('✅ Authentication module works')"
```

### Step 9: Start the Application

```bash
# Option 1: Start just the Streamlit app (recommended for first-time users)
streamlit run app_streamlit_enhanced.py

# Option 2: Start all services (advanced users)
chmod +x start_services.sh
./start_services.sh
```

### Step 10: Access the Application

1. **Streamlit Web App**: Open http://localhost:8501 in your browser
2. **FastAPI Docs** (if running full services): http://localhost:8000/docs

## 🎯 Quick Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check Redis
redis-cli ping
# Expected: PONG

# 2. Check Python environment
python3 --version
# Expected: Python 3.9+ 

# 3. Check key packages
python3 -c "import streamlit, redis, celery; print('✅ All packages imported successfully')"

# 4. Check project files
ls -la *.py | head -5
# Should show Python files like app_streamlit_enhanced.py

# 5. Test database creation
python3 -c "from core.history import HistoryManager; h = HistoryManager(); print('✅ Database created')"
```

## 🔧 Troubleshooting Common Issues

### Issue 1: Redis Connection Error
```bash
# Error: ConnectionError: Error 61 connecting to localhost:6379
# Solution: Start Redis service
brew services start redis
redis-cli ping
```

### Issue 2: Python Module Not Found
```bash
# Error: ModuleNotFoundError: No module named 'streamlit'
# Solution: Ensure virtual environment is activated and packages installed
source translator_env/bin/activate
pip install -r requirements.txt
```

### Issue 3: Permission Denied on Scripts
```bash
# Error: Permission denied: ./start_services.sh
# Solution: Make script executable
chmod +x start_services.sh
chmod +x stop_services.sh
```

### Issue 4: Port Already in Use
```bash
# Error: Port 8501 is already in use
# Solution: Kill existing processes or use different port
lsof -ti:8501 | xargs kill -9
# Or run on different port:
streamlit run app_streamlit_enhanced.py --server.port 8502
```

### Issue 5: Audio/Speech Issues
```bash
# Error: No module named 'pyaudio'
# Solution: Install audio dependencies
brew install portaudio
pip install pyaudio

# For speech recognition issues:
brew install flac
pip install SpeechRecognition pydub
```

## 🎵 Optional: Enable Voice Features

For full voice input/output functionality:

```bash
# Install additional audio packages
pip install pyaudio speechrecognition pydub

# Install system audio tools
brew install sox
brew install lame

# Test microphone access (will prompt for permission)
python3 -c "
import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print('✅ Microphone access granted')
"
```

## 🌐 Environment Variables (Optional)

Create a `.env` file for custom configuration:

```bash
# Create .env file
cat > .env << EOF
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Paths
HISTORY_DB_PATH=translator.db
USER_DB_PATH=users.db

# API Configuration
API_PORT=8000
STREAMLIT_PORT=8501

# Feature Flags
ENABLE_OFFLINE_MODE=true
ENABLE_VOICE_INPUT=true
ENABLE_TTS=true
EOF
```

## 🚀 Running Different Components

### Just the Web App (Simplest)
```bash
source translator_env/bin/activate
streamlit run app_streamlit_enhanced.py
```

### Full System with API and Background Tasks
```bash
source translator_env/bin/activate

# Terminal 1: Start Redis (if not running as service)
redis-server

# Terminal 2: Start Celery worker
celery -A tasks worker --loglevel=info

# Terminal 3: Start FastAPI server
uvicorn api_server_fastapi:app --port 8000 --reload

# Terminal 4: Start Streamlit app
streamlit run app_streamlit_enhanced.py
```

### Using the Convenience Script
```bash
source translator_env/bin/activate
./start_services.sh

# To stop all services:
./stop_services.sh
```

## 📱 First-Time Usage

1. **Open the app**: http://localhost:8501
2. **Choose authentication**:
   - **Guest Mode**: Quick start, device-specific history
   - **Create Account**: Persistent history across devices
3. **Test translation**: Try "Hello world" from English to Spanish
4. **Explore features**:
   - Voice input (click microphone icon)
   - File upload (drag & drop text files)
   - Translation history
   - Personal statistics

## 🔄 Daily Usage

After initial setup, you only need:

```bash
# Navigate to project directory
cd ~/Downloads/Mini-Project-Translator

# Activate virtual environment
source translator_env/bin/activate

# Start the app
streamlit run app_streamlit_enhanced.py
```

## 🛑 Stopping the Application

```bash
# If running individual components:
# Press Ctrl+C in each terminal

# If using start_services.sh:
./stop_services.sh

# To stop Redis service:
brew services stop redis
```

## 📦 Updating the Project

```bash
# Pull latest changes
git pull origin main

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt --upgrade

# Restart the application
streamlit run app_streamlit_enhanced.py
```

## 🎉 Success Indicators

You'll know everything is working when:

- ✅ Streamlit app opens at http://localhost:8501
- ✅ Authentication screen appears
- ✅ You can create an account or use guest mode
- ✅ Translation works (try "Hello" → Spanish)
- ✅ History is saved and visible
- ✅ Voice input works (if enabled)
- ✅ No error messages in terminal

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look at terminal output for error messages
2. **Verify prerequisites**: Ensure Python 3.9+, Redis, and dependencies are installed
3. **Test components individually**: Use the verification commands above
4. **Check file permissions**: Ensure scripts are executable
5. **Restart services**: Sometimes a fresh start resolves issues

## 📚 Next Steps

Once everything is running:

- Explore the **User Authentication Guide**: `USER_AUTHENTICATION_GUIDE.md`
- Learn about **Offline Mode**: `OFFLINE_SETUP.md`
- Check out **Advanced Features**: `README.md`
- Review **API Documentation**: http://localhost:8000/docs (if running FastAPI)

---

**Estimated Setup Time**: 15-30 minutes  
**Difficulty**: Beginner-friendly  
**Support**: All commands tested on macOS 12+ (Monterey/Ventura/Sonoma)