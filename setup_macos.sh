#!/bin/bash

# 🍎 macOS One-Click Setup Script for AI Language Translator
# Run with: curl -sSL https://raw.githubusercontent.com/Manya-Goel132/Mini-Project-Translator/main/setup_macos.sh | bash

set -e  # Exit on any error

echo "🍎 AI Language Translator - macOS Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only."
    exit 1
fi

print_status "Starting macOS setup for AI Language Translator..."

# Step 1: Check/Install Homebrew
print_status "Checking Homebrew installation..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    print_success "Homebrew is already installed"
fi

# Step 2: Install Python
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null || [[ $(python3 -c "import sys; print(sys.version_info >= (3, 9))") != "True" ]]; then
    print_warning "Python 3.9+ not found. Installing Python..."
    brew install python@3.11
else
    print_success "Python 3.9+ is already installed"
fi

# Step 3: Install Redis
print_status "Checking Redis installation..."
if ! command -v redis-server &> /dev/null; then
    print_warning "Redis not found. Installing Redis..."
    brew install redis
fi

print_status "Starting Redis service..."
brew services start redis

# Verify Redis is running
if redis-cli ping &> /dev/null; then
    print_success "Redis is running"
else
    print_error "Failed to start Redis"
    exit 1
fi

# Step 4: Install system dependencies
print_status "Installing system dependencies..."
brew install portaudio ffmpeg flac espeak || print_warning "Some audio dependencies may have failed to install"

# Step 5: Clone repository (if not already in it)
if [[ ! -f "app_streamlit_enhanced.py" ]]; then
    print_status "Cloning repository..."
    git clone https://github.com/Manya-Goel132/Mini-Project-Translator.git
    cd Mini-Project-Translator
else
    print_success "Already in project directory"
fi

# Step 6: Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv translator_env

# Step 7: Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source translator_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 8: Test installation
print_status "Testing installation..."
python3 -c "
try:
    import redis
    r = redis.Redis()
    r.ping()
    print('✅ Redis connection: OK')
except Exception as e:
    print(f'❌ Redis connection: {e}')
    exit(1)

try:
    from core.translator import AITranslator
    from core.history import HistoryManager
    from core.user_auth import UserManager
    print('✅ Core modules: OK')
except Exception as e:
    print(f'❌ Core modules: {e}')
    exit(1)
"

# Step 9: Make scripts executable
chmod +x start_services.sh stop_services.sh setup_git.sh 2>/dev/null || true

print_success "Setup completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   cd $(pwd)"
echo "   source translator_env/bin/activate"
echo "   streamlit run app_streamlit_enhanced.py"
echo ""
echo "📖 For detailed usage instructions, see:"
echo "   - MACOS_SETUP_GUIDE.md (detailed setup)"
echo "   - USER_AUTHENTICATION_GUIDE.md (authentication features)"
echo "   - README.md (full documentation)"
echo ""
echo "🌐 The app will open at: http://localhost:8501"
echo ""

# Optional: Ask if user wants to start the app immediately
read -p "🚀 Would you like to start the application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting AI Language Translator..."
    source translator_env/bin/activate
    streamlit run app_streamlit_enhanced.py
fi