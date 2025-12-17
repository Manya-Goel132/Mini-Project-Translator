## 🆕 Advanced Features: Redis & Celery

### Centralized Caching & Task Queues

The application now supports **production-grade distributed processing** with Redis and Celery:

**Benefits:**
- ✅ **Shared Cache**: All apps (Streamlit, API, Batch) share the same Redis cache
- ✅ **50-67% Memory Reduction**: Models loaded once, shared across workers
- ✅ **8-10x Faster**: Batch processing with parallel workers
- ✅ **Scalable**: Add more workers for higher throughput
- ✅ **Resilient**: Auto-retry on failure, survive crashes
- ✅ **Non-blocking**: Queue tasks and check status later

### Quick Start with Redis & Celery

```bash
# 1. Install Redis
brew install redis  # macOS
# or
sudo apt install redis-server  # Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start all services
./start_services.sh

# 4. Run batch jobs with Celery
python app_batch_celery.py input.csv output.csv --text-column text
```

### Architecture with Redis

```
┌─────────────────────────────────┐
│         Redis Server            │
│  ┌──────────┐  ┌──────────┐    │
│  │  Cache   │  │  Queue   │    │
│  └──────────┘  └──────────┘    │
└─────────────────────────────────┘
          ▲
          │ Shared State
    ┌─────┴─────┬─────────┐
    │           │         │
┌───▼────┐  ┌──▼────┐  ┌─▼──────┐
│Streamlit│  │Flask  │  │Celery  │
│   App   │  │  API  │  │Workers │
└─────────┘  └───────┘  └────────┘
```

📚 **See [REDIS_CELERY_SETUP.md](REDIS_CELERY_SETUP.md) for detailed setup**
📊 **See [CACHE_COMPARISON.md](CACHE_COMPARISON.md) for before/after comparison**

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration from old to new structure
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Summary of refactoring changes
- **[BEFORE_AFTER.md](BEFORE_AFTER.md)** - Visual comparison of old vs new
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card
- **[REDIS_CELERY_SETUP.md](REDIS_CELERY_SETUP.md)** - Redis & Celery setup guide ⭐ NEW
- **[CACHE_COMPARISON.md](CACHE_COMPARISON.md)** - Cache performance comparison ⭐ NEW
