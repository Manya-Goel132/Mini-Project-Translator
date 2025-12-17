"""
FastAPI-based async API server
High-performance, non-blocking, production-ready
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import time
from datetime import datetime
import asyncio
import logging
from contextlib import asynccontextmanager

from core.translator import AITranslator
from core.caching import SharedModelCache
from core.audio_async import AsyncAudioManager
from core.speech_recognition_async import AsyncSpeechRecognizer
from tasks import translate_text, translate_batch
from celery.result import AsyncResult
from celery_config import celery_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage = {}
RATE_LIMIT = 100  # requests per hour per IP


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("🚀 Starting FastAPI Translator API")
    yield
    # Shutdown
    logger.info("👋 Shutting down FastAPI Translator API")


# Create FastAPI app
app = FastAPI(
    title="AI Translator API",
    description="Advanced async translation API with multiple AI backends",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
translator = AITranslator()
audio_manager = AsyncAudioManager()
speech_recognizer = AsyncSpeechRecognizer()


# Pydantic models
class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    source_lang: str = Field(default="auto")
    target_lang: str = Field(default="en")


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class BatchTranslateRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=100)
    source_lang: str = Field(default="auto")
    target_lang: str = Field(default="en")
    async_mode: bool = Field(default=True, alias="async")


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en")
    slow: bool = Field(default=False)


class STTRequest(BaseModel):
    language: str = Field(default="en")
    engine: str = Field(default="google")


# Rate limiting middleware
async def check_rate_limit(request: Request) -> bool:
    """Check if request is within rate limit"""
    client_ip = request.client.host
    current_time = time.time()
    hour_ago = current_time - 3600
    
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []
    
    # Remove old requests
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip]
        if req_time > hour_ago
    ]
    
    # Check if under limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True


@app.get("/", response_class=HTMLResponse)
async def home():
    """API documentation page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Translator API (FastAPI)</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { color: #007bff; font-weight: bold; padding: 3px 8px; background: #e7f3ff; border-radius: 3px; }
            code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
            pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; }
            .badge { background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI Translator API <span class="badge">FastAPI v3.0</span></h1>
            <p>High-performance async translation API with multiple AI backends</p>
            
            <h2>✨ New Features</h2>
            <ul>
                <li>⚡ <strong>Async/Await</strong> - Non-blocking I/O for high concurrency</li>
                <li>🎵 <strong>Streaming Audio</strong> - TTS without temp files</li>
                <li>📊 <strong>Auto Documentation</strong> - Visit <a href="/docs">/docs</a> for interactive API</li>
                <li>🔄 <strong>Celery Integration</strong> - Background task processing</li>
            </ul>
            
            <h2>📚 Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/translate</h3>
                <p>Translate text using AI models (async)</p>
                <pre><code>{
  "text": "Hello world",
  "source_lang": "en",
  "target_lang": "es"
}</code></pre>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/detect</h3>
                <p>Detect language of text (async)</p>
                <pre><code>{
  "text": "Bonjour le monde"
}</code></pre>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/languages</h3>
                <p>Get supported languages</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/batch</h3>
                <p>Batch translate with Celery (async)</p>
                <pre><code>{
  "texts": ["Hello", "World"],
  "source_lang": "en",
  "target_lang": "es",
  "async": true
}</code></pre>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/tts</h3>
                <p>🆕 Text-to-Speech (streaming audio)</p>
                <pre><code>{
  "text": "Hello world",
  "language": "en",
  "slow": false
}</code></pre>
                <p>Returns: <code>audio/mpeg</code> stream</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/stt</h3>
                <p>🆕 Speech-to-Text (audio upload)</p>
                <p>Upload audio file (WAV, MP3, etc.)</p>
                <pre><code>Form data:
  - audio: file upload
  - language: "en" (optional)
  - engine: "google" (optional)</code></pre>
                <p>Returns: Recognized text</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/task/{task_id}</h3>
                <p>Check Celery task status</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/cache/stats</h3>
                <p>Get cache statistics</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /health</h3>
                <p>Health check endpoint</p>
            </div>
            
            <h2>📖 Interactive Documentation</h2>
            <p>Visit <a href="/docs"><strong>/docs</strong></a> for Swagger UI</p>
            <p>Visit <a href="/redoc"><strong>/redoc</strong></a> for ReDoc</p>
            
            <h2>⚡ Rate Limiting</h2>
            <p>API is limited to <strong>100 requests per hour per IP address</strong></p>
            
            <h2>🔧 Performance</h2>
            <ul>
                <li>Async I/O for high concurrency</li>
                <li>Non-blocking translation calls</li>
                <li>Streaming audio responses</li>
                <li>Redis caching for speed</li>
            </ul>
        </div>
    </body>
    </html>
    """


@app.post("/api/translate")
async def translate_endpoint(request: Request, data: TranslateRequest):
    """
    Translate text using AI models (async)
    
    - **text**: Text to translate
    - **source_lang**: Source language code (default: auto)
    - **target_lang**: Target language code (default: en)
    """
    # Rate limiting
    if not await check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per hour."
        )
    
    try:
        # Run translation in thread pool (translator is sync)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            translator.smart_translate,
            data.text,
            data.source_lang,
            data.target_lang
        )
        
        if result:
            logger.info(f"Translation: {data.source_lang}->{data.target_lang} via {result['method']}")
            return {
                "success": True,
                "translation": result['translation'],
                "source_lang": result['source_lang'],
                "target_lang": data.target_lang,
                "method": result['method'],
                "confidence": result['confidence'],
                "time_taken": result['time'],
                "cached": result.get('cached', False)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Translation failed"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/api/detect")
async def detect_endpoint(request: Request, data: DetectRequest):
    """
    Detect language of text (async)
    
    - **text**: Text to detect language
    """
    # Rate limiting
    if not await check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        # Run detection in thread pool
        loop = asyncio.get_event_loop()
        detected_lang, confidence = await loop.run_in_executor(
            None,
            translator.detect_language,
            data.text
        )
        
        return {
            "success": True,
            "detected_language": detected_lang,
            "language_name": translator.supported_languages.get(detected_lang, 'Unknown'),
            "confidence": confidence
        }
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/api/languages")
async def languages_endpoint():
    """Get supported languages"""
    return {
        "success": True,
        "languages": translator.supported_languages
    }


@app.post("/api/batch")
async def batch_endpoint(request: Request, data: BatchTranslateRequest):
    """
    Batch translate texts (async with Celery)
    
    - **texts**: List of texts to translate
    - **source_lang**: Source language code (default: auto)
    - **target_lang**: Target language code (default: en)
    - **async**: Use Celery for async processing (default: true)
    """
    # Rate limiting
    if not await check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        # Async mode - queue Celery task
        if data.async_mode:
            task = translate_batch.delay(data.texts, data.source_lang, data.target_lang)
            
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "success": True,
                    "task_id": task.id,
                    "status": "queued",
                    "message": "Batch translation queued. Use /api/task/<task_id> to check status",
                    "total_texts": len(data.texts)
                }
            )
        
        # Sync mode - process immediately
        else:
            results = []
            loop = asyncio.get_event_loop()
            
            for text in data.texts:
                if not text or not text.strip():
                    results.append({
                        "success": False,
                        "error": "Empty text"
                    })
                    continue
                
                result = await loop.run_in_executor(
                    None,
                    translator.smart_translate,
                    text.strip(),
                    data.source_lang,
                    data.target_lang
                )
                
                if result:
                    results.append({
                        "success": True,
                        "original": text,
                        "translation": result['translation'],
                        "method": result['method'],
                        "confidence": result['confidence'],
                        "cached": result.get('cached', False)
                    })
                else:
                    results.append({
                        "success": False,
                        "original": text,
                        "error": "Translation failed"
                    })
            
            return {
                "success": True,
                "results": results,
                "total_processed": len(results)
            }
    
    except Exception as e:
        logger.error(f"Batch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/api/task/{task_id}")
async def task_status_endpoint(task_id: str):
    """
    Get Celery task status
    
    - **task_id**: Task ID from batch endpoint
    """
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": task.info
            }
        elif task.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "completed",
                "result": task.result
            }
        elif task.state == 'FAILURE':
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        else:
            return {
                "task_id": task_id,
                "status": task.state.lower()
            }
    
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )


@app.post("/api/tts")
async def tts_endpoint(request: Request, data: TTSRequest):
    """
    Text-to-Speech endpoint (streaming audio)
    
    - **text**: Text to convert to speech
    - **language**: Language code (default: en)
    - **slow**: Slow speech rate (default: false)
    
    Returns: audio/mpeg stream
    """
    # Rate limiting
    if not await check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        # Generate audio bytes
        audio_bytes, error = await audio_manager.generate_audio_bytes(
            data.text,
            data.language,
            slow=data.slow
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )
        
        # Return streaming response
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=tts_{int(time.time())}.mp3"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TTS generation failed"
        )


@app.post("/api/stt")
async def stt_endpoint(
    request: Request,
    language: str = "en",
    engine: str = "google"
):
    """
    Speech-to-Text endpoint (audio upload)
    
    Send audio data as raw bytes in the request body.
    Supports WAV, WebM, MP3, OGG, FLAC, M4A formats.
    
    - **language**: Language code (default: en)
    - **engine**: Recognition engine: google, google_cloud, sphinx, wit (default: google)
    
    Returns: Recognized text
    """
    # Rate limiting
    if not await check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        # Get audio from request body
        audio = await request.body()
        
        if not audio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audio data provided. Send audio bytes in request body."
            )
        
        if len(audio) < 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio too short. Please provide at least 1 second of audio."
            )
        
        # Recognize speech
        text, error = await speech_recognizer.recognize_from_audio_bytes(
            audio,
            language,
            engine
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )
        
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No speech detected in audio"
            )
        
        return {
            "success": True,
            "text": text.strip(),
            "language": language,
            "engine": engine
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech recognition failed"
        )


@app.get("/api/stt/languages")
async def stt_languages_endpoint():
    """Get supported languages for speech recognition"""
    return {
        "success": True,
        "languages": speech_recognizer.async_recognizer.supported_languages if hasattr(speech_recognizer, 'async_recognizer') else {}
    }


@app.get("/api/stt/engines")
async def stt_engines_endpoint():
    """Get available speech recognition engines"""
    try:
        from core.speech_recognition_async import StreamlitSpeechRecognizer
        sr = StreamlitSpeechRecognizer()
        return {
            "success": True,
            "engines": sr.get_engine_info()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/cache/stats")
async def cache_stats_endpoint():
    """Get cache statistics"""
    try:
        cache = SharedModelCache.get_cache()
        stats = cache.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache stats"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache = SharedModelCache.get_cache()
    cache_stats = cache.get_cache_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "framework": "FastAPI",
        "async": True,
        "cache": {
            "redis_connected": cache_stats.get('redis_connected', False),
            "models_loaded": cache_stats.get('models_cached', 0)
        }
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Starting FastAPI Translator API on port {port}")
    print(f"📖 API documentation: http://localhost:{port}/docs")
    print(f"📖 Alternative docs: http://localhost:{port}/redoc")
    
    uvicorn.run(
        "api_server_fastapi:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
