"""
Flask REST API Server for AI Language Translator
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from datetime import datetime
from core.translator import AITranslator
import logging
import os

app = Flask(__name__)
CORS(app)

# Initialize translator (shared instance)
translator = AITranslator()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API rate limiting (simple in-memory store)
request_counts = {}
RATE_LIMIT = 100  # requests per hour per IP


def check_rate_limit(ip_address):
    """Simple rate limiting"""
    current_time = time.time()
    hour_ago = current_time - 3600
    
    if ip_address not in request_counts:
        request_counts[ip_address] = []
    
    # Remove old requests
    request_counts[ip_address] = [
        req_time for req_time in request_counts[ip_address] 
        if req_time > hour_ago
    ]
    
    # Check if under limit
    if len(request_counts[ip_address]) >= RATE_LIMIT:
        return False
    
    # Add current request
    request_counts[ip_address].append(current_time)
    return True


@app.route('/')
def home():
    """API documentation page"""
    docs = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Translator API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007bff; font-weight: bold; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🤖 AI Translator API</h1>
        <p>Advanced translation API with multiple AI backends</p>
        
        <h2>Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/translate</h3>
            <p>Translate text using AI models</p>
            <h4>Request Body:</h4>
            <pre><code>{
    "text": "Hello world",
    "source_lang": "en",
    "target_lang": "es"
}</code></pre>
            <h4>Response:</h4>
            <pre><code>{
    "success": true,
    "translation": "Hola mundo",
    "source_lang": "en",
    "target_lang": "es",
    "method": "AI Model",
    "confidence": 0.95,
    "time_taken": 0.23
}</code></pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/detect</h3>
            <p>Detect language of text</p>
            <h4>Request Body:</h4>
            <pre><code>{
    "text": "Bonjour le monde"
}</code></pre>
            <h4>Response:</h4>
            <pre><code>{
    "success": true,
    "detected_language": "fr",
    "confidence": 0.98
}</code></pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/languages</h3>
            <p>Get supported languages</p>
            <h4>Response:</h4>
            <pre><code>{
    "success": true,
    "languages": {
        "en": "English",
        "es": "Spanish",
        ...
    }
}</code></pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/batch</h3>
            <p>Batch translate multiple texts</p>
            <h4>Request Body:</h4>
            <pre><code>{
    "texts": ["Hello", "World"],
    "source_lang": "en",
    "target_lang": "es"
}</code></pre>
        </div>
        
        <h2>Rate Limiting</h2>
        <p>API is limited to <strong>100 requests per hour per IP address</strong></p>
        
        <h2>Error Codes</h2>
        <ul>
            <li><code>400</code> - Bad Request (missing parameters)</li>
            <li><code>429</code> - Too Many Requests (rate limit exceeded)</li>
            <li><code>500</code> - Internal Server Error</li>
        </ul>
    </body>
    </html>
    """
    return docs


@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text endpoint"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Maximum 100 requests per hour.'
            }), 429
        
        # Get request data
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: text'
            }), 400
        
        text = data['text']
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'en')
        
        if not text.strip():
            return jsonify({
                'success': False,
                'error': 'Text cannot be empty'
            }), 400
        
        # Perform translation
        result = translator.smart_translate(text, source_lang, target_lang)
        
        if result:
            response = {
                'success': True,
                'translation': result['translation'],
                'source_lang': result['source_lang'],
                'target_lang': target_lang,
                'method': result['method'],
                'confidence': result['confidence'],
                'time_taken': result['time']
            }
            
            logger.info(f"Translation successful: {source_lang}->{target_lang} via {result['method']}")
            return jsonify(response)
        else:
            return jsonify({
                'success': False,
                'error': 'Translation failed'
            }), 500
    
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/detect', methods=['POST'])
def detect_language():
    """Language detection endpoint"""
    try:
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded'
            }), 429
        
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: text'
            }), 400
        
        text = data['text']
        
        if not text.strip():
            return jsonify({
                'success': False,
                'error': 'Text cannot be empty'
            }), 400
        
        detected_lang, confidence = translator.detect_language(text)
        
        return jsonify({
            'success': True,
            'detected_language': detected_lang,
            'language_name': translator.supported_languages.get(detected_lang, 'Unknown'),
            'confidence': confidence
        })
    
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    return jsonify({
        'success': True,
        'languages': translator.supported_languages
    })


@app.route('/api/batch', methods=['POST'])
def batch_translate():
    """Batch translation endpoint"""
    try:
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded'
            }), 429
        
        data = request.get_json()
        
        if not data or 'texts' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: texts'
            }), 400
        
        texts = data['texts']
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'en')
        
        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({
                'success': False,
                'error': 'texts must be a non-empty list'
            }), 400
        
        if len(texts) > 50:
            return jsonify({
                'success': False,
                'error': 'Maximum 50 texts per batch request'
            }), 400
        
        results = []
        
        for text in texts:
            if not text or not text.strip():
                results.append({
                    'success': False,
                    'error': 'Empty text'
                })
                continue
            
            result = translator.smart_translate(text.strip(), source_lang, target_lang)
            
            if result:
                results.append({
                    'success': True,
                    'original': text,
                    'translation': result['translation'],
                    'method': result['method'],
                    'confidence': result['confidence']
                })
            else:
                results.append({
                    'success': False,
                    'original': text,
                    'error': 'Translation failed'
                })
            
            time.sleep(0.1)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })
    
    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting AI Translator API on port {port}")
    print(f"📖 API documentation available at http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
