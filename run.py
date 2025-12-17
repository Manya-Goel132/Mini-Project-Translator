#!/usr/bin/env python3
"""
AI Language Translator - Main Runner Script
Provides easy access to all translator components
"""

import sys
import argparse
import subprocess
import os
from pathlib import Path

def run_streamlit_app():
    """Run the Streamlit web application"""
    print("🚀 Starting AI Translator Web App...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app_streamlit_enhanced.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit app: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")
        return 0

def run_api_server():
    """Run the FastAPI server"""
    print("🚀 Starting AI Translator API Server...")
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "api_server_fastapi:app", "--host", "0.0.0.0", "--port", "8000"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start API server: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 API server stopped by user")
        return 0

def run_batch_translator(args):
    """Run batch translation"""
    print("🚀 Starting Batch Translation...")
    
    cmd = [sys.executable, "app_batch.py", args.input_file, args.output_file]
    
    if args.source_lang:
        cmd.extend(["--source-lang", args.source_lang])
    if args.target_lang:
        cmd.extend(["--target-lang", args.target_lang])
    if args.file_type:
        cmd.extend(["--file-type", args.file_type])
    if args.text_column:
        cmd.extend(["--text-column", args.text_column])
    if args.text_fields:
        cmd.extend(["--text-fields"] + args.text_fields)
    
    try:
        return subprocess.run(cmd, check=True).returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Batch translation failed: {e}")
        return 1

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running: pip install -r requirements.txt")
        return 1

def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit', 'transformers', 'torch', 'langdetect', 
        'gtts', 'pygame', 'deep_translator', 
        'sentence_transformers', 'fastapi', 'uvicorn', 'redis', 'celery'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: python run.py --install")
        return False
    else:
        print("✅ All dependencies are installed!")
        return True

def show_help():
    """Show detailed help information"""
    help_text = """
🤖 AI Language Translator - Help

USAGE:
    python run.py [COMMAND] [OPTIONS]

COMMANDS:
    web         Start the Streamlit web application (default)
    api         Start the Flask API server
    batch       Run batch translation on files
    install     Install required dependencies
    check       Check if dependencies are installed
    help        Show this help message

WEB APPLICATION:
    python run.py web
    python run.py  # (same as web)
    
    Opens a browser-based interface for interactive translation

API SERVER:
    python run.py api
    
    Starts REST API server on http://localhost:5000
    See API documentation at http://localhost:5000

BATCH TRANSLATION:
    python run.py batch input.csv output.csv --text-column "text" --target-lang "es"
    python run.py batch input.json output.json --text-fields "title" "content"
    python run.py batch input.txt output.txt --source-lang "en" --target-lang "fr"

BATCH OPTIONS:
    --source-lang LANG    Source language code (default: auto)
    --target-lang LANG    Target language code (default: en)
    --file-type TYPE      File type: csv, json, txt (auto-detected)
    --text-column COL     Column name for CSV files
    --text-fields FIELDS  Field names for JSON files (space-separated)

SUPPORTED LANGUAGES:
    en (English), es (Spanish), fr (French), de (German), it (Italian),
    pt (Portuguese), ru (Russian), ja (Japanese), ko (Korean), zh (Chinese),
    ar (Arabic), hi (Hindi), nl (Dutch), sv (Swedish), da (Danish),
    no (Norwegian), fi (Finnish), pl (Polish), tr (Turkish), th (Thai)

EXAMPLES:
    # Start web app
    python run.py
    
    # Start API server
    python run.py api
    
    # Translate CSV file
    python run.py batch data.csv translated_data.csv --text-column "description" --target-lang "es"
    
    # Translate JSON file
    python run.py batch content.json translated_content.json --text-fields "title" "body"
    
    # Install dependencies
    python run.py install

REQUIREMENTS:
    - Python 3.8+
    - Internet connection for translation APIs
    - ~2GB disk space for AI models (downloaded automatically)

For more information, visit: https://github.com/yourusername/ai-language-translator
    """
    print(help_text)

def main():
    parser = argparse.ArgumentParser(
        description="AI Language Translator - Advanced translation with multiple AI backends",
        add_help=False
    )
    
    # Main command
    parser.add_argument(
        'command', 
        nargs='?', 
        default='web',
        choices=['web', 'api', 'batch', 'install', 'check', 'help'],
        help='Command to run'
    )
    
    # Batch translation arguments
    parser.add_argument('input_file', nargs='?', help='Input file for batch translation')
    parser.add_argument('output_file', nargs='?', help='Output file for batch translation')
    parser.add_argument('--source-lang', default='auto', help='Source language code')
    parser.add_argument('--target-lang', default='en', help='Target language code')
    parser.add_argument('--file-type', choices=['csv', 'json', 'txt'], help='File type')
    parser.add_argument('--text-column', help='Column name for CSV files')
    parser.add_argument('--text-fields', nargs='+', help='Field names for JSON files')
    
    # Parse known args to handle help properly
    args, unknown = parser.parse_known_args()
    
    # Handle help
    if args.command == 'help' or '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        return 0
    
    # Handle install
    if args.command == 'install':
        return install_dependencies()
    
    # Handle check
    if args.command == 'check':
        check_dependencies()
        return 0
    
    # Check dependencies for other commands
    if not check_dependencies():
        print("\n💡 Install dependencies first: python run.py install")
        return 1
    
    # Handle commands
    if args.command == 'web':
        return run_streamlit_app()
    
    elif args.command == 'api':
        return run_api_server()
    
    elif args.command == 'batch':
        if not args.input_file or not args.output_file:
            print("❌ Batch translation requires input and output files")
            print("💡 Usage: python run.py batch input.csv output.csv --text-column 'text'")
            return 1
        
        return run_batch_translator(args)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        show_help()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)