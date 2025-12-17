# 🚀 Redis & Celery Setup Guide

## The Problem We're Solving

Your application has **three separate instances** that don't communicate:
1. **Streamlit App** - Loads models with `@st.cache_resource`
2. **Flask API** - Loads models independently
3. **Batch Script** - Loads models again

This causes:
- ❌ **Wasted Memory**: Same models loaded 3x
- ❌ **Wasted Time**: Models reload on every restart
- ❌ **Data Silos**: History not shared between apps
- ❌ **Brittle Batch**: `time.sleep()` instead of proper queues

## The Solution: Centralized State with Redis + Celery

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Redis Server                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Translation  │  │ Task Queue   │  │ Task Results │  │
│  │    Cache     │  │   (Broker)   │  │   (Backend)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
           ▲                  ▲                  ▲
           │                  │                  │
    ┌──────┴──────┬──────────┴────────┬─────────┴────────┐
    │             │                   │                   │
┌───▼────┐  ┌────▼─────┐  ┌──────────▼──────┐  ┌────────▼────┐
│Streamlit│  │Flask API │  │ Celery Workers  │  │Batch Script │
│   App   │  │  Server  │  │  (1 or more)    │  │   Client    │
└─────────┘  └──────────┘  └─────────────────┘  └─────────────┘
```

### Benefits

✅ **Shared Cache**: All apps use the same Redis cache for translations
✅ **Shared Models**: Models loaded once in memory, shared across workers
✅ **Scalable**: Run multiple Celery workers for parallel processing
✅ **Resilient**: Tasks retry on failure, survive worker crashes
✅ **Non-blocking**: Queue tasks and check status later
✅ **Professional**: Industry-standard architecture

---

## 📦 Installation

### 1. Install Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `redis>=5.0.0` - Redis client
- `celery>=5.3.0` - Task queue
- `diskcache>=5.6.0` - Disk-based cache fallback

---

## 🎯 Usage

### Option 1: Run Everything Locally (Development)

**Terminal 1 - Start Redis:**
```bash
redis-server
```

**Terminal 2 - Start Celery Worker:**
```bash
celery -A tasks worker --loglevel=info
```

**Terminal 3 - Start Flask API:**
```bash
python api_server.py
```

**Terminal 4 - Start Streamlit App:**
```bash
streamlit run app_streamlit.py
```

**Terminal 5 - Run Batch Jobs:**
```bash
# Queue a batch job (returns immediately)
python app_batch_celery.py input.csv output.csv --text-column text --no-wait

# Check task status
python app_batch_celery.py --check-task <task_id>

# Wait for completion
python app_batch_celery.py input.csv output.csv --text-column text
```

### Option 2: Production Setup

**1. Configure Redis URL (optional):**
```bash
export REDIS_URL="redis://localhost:6379/0"
```

**2. Run Celery Workers (multiple for scaling):**
```bash
# Worker 1
celery -A tasks worker --loglevel=info --concurrency=2 -n worker1@%h

# Worker 2 (in another terminal)
celery -A tasks worker --loglevel=info --concurrency=2 -n worker2@%h
```

**3. Monitor Celery:**
```bash
# Flower - Web-based monitoring
pip install flower
celery -A tasks flower
# Open http://localhost:5555
```

---

## 🔧 API Usage

### Synchronous Translation (Small Batches)

```bash
curl -X POST http://localhost:5000/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World"],
    "source_lang": "en",
    "target_lang": "es",
    "async": false
  }'
```

### Asynchronous Translation (Large Batches)

**1. Queue the task:**
```bash
curl -X POST http://localhost:5000/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World", "...100 more texts..."],
    "source_lang": "en",
    "target_lang": "es",
    "async": true
  }'
```

Response:
```json
{
  "success": true,
  "task_id": "abc123-def456-...",
  "status": "queued",
  "message": "Batch translation queued. Use /api/task/<task_id> to check status"
}
```

**2. Check task status:**
```bash
curl http://localhost:5000/api/task/abc123-def456-...
```

Response (in progress):
```json
{
  "task_id": "abc123-def456-...",
  "status": "processing",
  "progress": {
    "current": 50,
    "total": 100
  }
}
```

Response (completed):
```json
{
  "task_id": "abc123-def456-...",
  "status": "completed",
  "result": {
    "success": true,
    "total": 100,
    "results": [...]
  }
}
```

### Cache Statistics

```bash
curl http://localhost:5000/api/cache/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "models_cached": 3,
    "translations_cached_redis": 150,
    "translations_cached_disk": 200,
    "redis_connected": true,
    "redis_memory_used": "2.5M"
  }
}
```

---

## 📊 Batch Processing Examples

### CSV Translation

```bash
# Translate a CSV file
python app_batch_celery.py \
  input.csv \
  output.csv \
  --text-column "description" \
  --source-lang en \
  --target-lang es
```

### JSON Translation

```bash
# Translate JSON fields
python app_batch_celery.py \
  input.json \
  output.json \
  --text-fields "title" "description" \
  --source-lang en \
  --target-lang fr
```

### Async Batch (Queue and Exit)

```bash
# Queue the job and exit
python app_batch_celery.py \
  large_file.csv \
  output.csv \
  --text-column "text" \
  --no-wait

# Returns: Task queued with ID: abc123-def456-...

# Check status later
python app_batch_celery.py --check-task abc123-def456-...
```

---

## 🔍 Monitoring & Debugging

### Check Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

### View Redis Keys

```bash
redis-cli
> KEYS trans:*
> GET trans:en:es:12345
```

### Monitor Celery Workers

```bash
# List active workers
celery -A tasks inspect active

# Check worker stats
celery -A tasks inspect stats

# Purge all tasks
celery -A tasks purge
```

### View Logs

```bash
# Celery worker logs (in terminal)
# Flask API logs (in terminal)
# Batch processing logs
tail -f batch_translation_celery.log
```

---

## 🚀 Scaling

### Run Multiple Workers

```bash
# Start 4 workers with 2 threads each = 8 concurrent tasks
celery -A tasks worker --loglevel=info --concurrency=2 -n worker1@%h &
celery -A tasks worker --loglevel=info --concurrency=2 -n worker2@%h &
celery -A tasks worker --loglevel=info --concurrency=2 -n worker3@%h &
celery -A tasks worker --loglevel=info --concurrency=2 -n worker4@%h &
```

### Dedicated Queues

Edit `celery_config.py` to route tasks to specific queues:

```python
celery_app.conf.task_routes = {
    'tasks.translate_text': {'queue': 'fast'},
    'tasks.translate_batch': {'queue': 'batch'},
}
```

Start workers for specific queues:
```bash
# Fast queue worker (high priority)
celery -A tasks worker -Q fast --loglevel=info

# Batch queue worker (background processing)
celery -A tasks worker -Q batch --loglevel=info
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Redis connection
export REDIS_URL="redis://localhost:6379/0"

# Flask API
export PORT=5000
export DEBUG=False

# Celery
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
```

### Celery Configuration

Edit `celery_config.py` to customize:
- Task time limits
- Worker concurrency
- Result expiration
- Retry policies

---

## 🔒 Production Considerations

### 1. Redis Persistence

Enable Redis persistence in `redis.conf`:
```
save 900 1
save 300 10
save 60 10000
```

### 2. Redis Security

```bash
# Set password
redis-cli CONFIG SET requirepass "your_password"

# Update REDIS_URL
export REDIS_URL="redis://:your_password@localhost:6379/0"
```

### 3. Celery as a Service

Create systemd service file `/etc/systemd/system/celery.service`:
```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=your_user
Group=your_group
WorkingDirectory=/path/to/project
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/path/to/venv/bin/celery -A tasks worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery
sudo systemctl start celery
```

### 4. Monitoring

Use **Flower** for production monitoring:
```bash
pip install flower
celery -A tasks flower --port=5555 --broker=redis://localhost:6379/0
```

---

## 🧪 Testing

### Test Redis Connection

```python
from core.caching import SharedModelCache

cache = SharedModelCache.get_cache()
stats = cache.get_cache_stats()
print(f"Redis connected: {stats['redis_connected']}")
```

### Test Celery Task

```python
from tasks import translate_text

# Queue a task
task = translate_text.delay("Hello world", "en", "es")
print(f"Task ID: {task.id}")

# Wait for result
result = task.get(timeout=30)
print(f"Translation: {result['translation']}")
```

---

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Flower Monitoring](https://flower.readthedocs.io/)

---

## 🆘 Troubleshooting

### Redis not connecting

```bash
# Check if Redis is running
redis-cli ping

# Check Redis logs
tail -f /usr/local/var/log/redis.log  # macOS
tail -f /var/log/redis/redis-server.log  # Linux
```

### Celery worker not starting

```bash
# Check for port conflicts
lsof -i :6379

# Verify Redis URL
echo $REDIS_URL

# Test connection
python -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

### Tasks stuck in PENDING

- Ensure Celery worker is running
- Check worker logs for errors
- Verify Redis connection
- Check task queue: `celery -A tasks inspect active`

### Memory issues

- Limit worker concurrency: `--concurrency=1`
- Enable worker restarts: `--max-tasks-per-child=100`
- Monitor memory: `celery -A tasks inspect stats`

---

## ✅ Summary

You now have:
- ✅ **Centralized caching** with Redis
- ✅ **Distributed task processing** with Celery
- ✅ **Shared state** across all applications
- ✅ **Scalable architecture** for production
- ✅ **Professional batch processing** with queues

All three applications (Streamlit, API, Batch) now share the same cache and can process tasks efficiently!
