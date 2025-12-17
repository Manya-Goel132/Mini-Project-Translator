# 🚀 Deployment Guide

This guide covers deploying the AI Language Translator to various platforms.

## 📱 Streamlit Cloud Deployment

### Prerequisites
- GitHub repository with the code
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Steps

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Add offline capabilities and voice input"
   git push origin main
   ```

2. **Create Streamlit app**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set main file: `app_streamlit_enhanced.py`
   - Deploy!

3. **Configure for Streamlit Cloud**:
   The app automatically detects Streamlit Cloud and adjusts:
   - Uses disk cache instead of Redis
   - Disables Celery (not supported)
   - Uses online services by default
   - Gracefully handles missing dependencies

### Streamlit Cloud Limitations
- No Redis server (uses disk cache)
- No Celery workers (synchronous processing)
- Limited to online translation services
- Speech recognition may have limitations

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t ai-translator .

# Run with Redis
docker-compose up -d
```

### Docker Compose
```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## ☁️ Cloud Platforms

### Heroku
```bash
# Install Heroku CLI
heroku create your-app-name
heroku addons:create heroku-redis:hobby-dev
git push heroku main
```

### Railway
```bash
# Install Railway CLI
railway login
railway init
railway add redis
railway deploy
```

### Google Cloud Run
```bash
# Build and deploy
gcloud run deploy ai-translator \
  --source . \
  --platform managed \
  --region us-central1
```

## 🔧 Environment Configuration

### Production Environment Variables
```bash
# Core settings
ENVIRONMENT=production
DEBUG=false

# Redis (if available)
REDIS_URL=redis://localhost:6379/0

# API settings
PORT=8501
HOST=0.0.0.0

# Feature flags
OFFLINE_MODE=false
USE_AI_MODELS=true
USE_GOOGLE_TRANSLATE=true
USE_MYMEMORY=true

# Optional: API keys
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
WIT_AI_KEY=your_wit_ai_key
```

### Streamlit Secrets (for Streamlit Cloud)
Create `.streamlit/secrets.toml`:
```toml
[general]
ENVIRONMENT = "production"
OFFLINE_MODE = false

# Add API keys here if needed
# GOOGLE_APPLICATION_CREDENTIALS = "..."
# WIT_AI_KEY = "..."
```

## 📊 Performance Optimization

### For Production
1. **Enable caching**: Use Redis if available
2. **Preload models**: Download common AI models
3. **Use CDN**: For static assets
4. **Monitor resources**: CPU, memory, disk usage
5. **Set up logging**: For debugging and monitoring

### Scaling
- **Horizontal**: Multiple app instances behind load balancer
- **Vertical**: Increase CPU/memory for AI models
- **Caching**: Redis cluster for high availability
- **Background tasks**: Separate Celery workers

## 🔍 Monitoring

### Health Checks
```bash
# API health
curl https://your-app.streamlit.app/health

# Streamlit health
curl https://your-app.streamlit.app/_stcore/health
```

### Metrics to Monitor
- Response time
- Translation accuracy
- Cache hit rate
- Error rate
- Resource usage

## 🛡️ Security

### Production Checklist
- [ ] Enable HTTPS
- [ ] Set up API rate limiting
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable logging and monitoring
- [ ] Regular security updates

### API Security
```python
# Add to FastAPI app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Memory errors**: AI models require 2GB+ RAM
2. **Slow startup**: Models download on first use
3. **Cache issues**: Check Redis connection
4. **Speech recognition**: May not work in all environments

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug
streamlit run app_streamlit_enhanced.py
```

### Correct Repository
Make sure you're using the correct repository:
- **Correct**: https://github.com/Manya-Goel132/Mini-Project-Translator
- **App URL**: https://mini-project-translator.streamlit.app/

## 📈 Deployment Strategies

### Blue-Green Deployment
1. Deploy to staging environment
2. Test thoroughly
3. Switch traffic to new version
4. Keep old version as backup

### Rolling Updates
1. Update one instance at a time
2. Health check each instance
3. Continue if healthy
4. Rollback if issues

### Feature Flags
Use environment variables to enable/disable features:
```python
ENABLE_VOICE_INPUT = os.getenv('ENABLE_VOICE_INPUT', 'true').lower() == 'true'
ENABLE_OFFLINE_MODE = os.getenv('ENABLE_OFFLINE_MODE', 'false').lower() == 'true'
```

## 🎯 Platform-Specific Notes

### Streamlit Cloud
- ✅ Easy deployment
- ✅ Free tier available
- ❌ No Redis/Celery
- ❌ Limited resources

### Heroku
- ✅ Redis add-on available
- ✅ Easy scaling
- ❌ Expensive for AI workloads
- ❌ Ephemeral filesystem

### Google Cloud Run
- ✅ Serverless scaling
- ✅ Good for AI workloads
- ❌ Cold starts
- ❌ More complex setup

### Self-hosted
- ✅ Full control
- ✅ All features available
- ❌ Maintenance overhead
- ❌ Infrastructure costs

Choose the platform that best fits your needs, budget, and technical requirements.