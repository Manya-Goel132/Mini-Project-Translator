# Cleanup Guide

This document lists legacy files that can be safely removed after verifying the new implementations work correctly.

## Legacy Files (Safe to Remove)

### Application Files
These have been replaced by enhanced versions:

| Legacy File | Replaced By | Notes |
|-------------|-------------|-------|
| `app_streamlit.py` | `app_streamlit_enhanced.py` | Basic UI → Enhanced UI with voice input |
| `app_api.py` | `api_server_fastapi.py` | Flask → FastAPI (async) |
| `api_server.py` | `api_server_fastapi.py` | Flask with Celery → FastAPI with Celery |
| `batch_translator.py` | `app_batch_celery.py` | Basic batch → Celery-powered batch |
| `ai_translator.py` | `core/translator.py` | Monolithic → Modular core library |

### Documentation Files (Consider Consolidating)
Many of these contain overlapping information:

| File | Content | Recommendation |
|------|---------|----------------|
| `ABSTRACT.md` | Project overview | Keep or merge into README |
| `ASYNC_IMPLEMENTATION_SUMMARY.md` | Async details | Merge into ARCHITECTURE.md |
| `BEFORE_AFTER.md` | Performance comparison | Keep in README |
| `CACHE_COMPARISON.md` | Cache benchmarks | Merge into ARCHITECTURE.md |
| `CHECKLIST.md` | Implementation checklist | Remove (completed) |
| `COMPLETE_SOLUTION_SUMMARY.md` | Summary | Remove (redundant) |
| `DATABASE_COMPARISON.md` | DB benchmarks | Merge into ARCHITECTURE.md |
| `ENHANCED_UI_GUIDE.md` | UI guide | Keep |
| `FASTAPI_MIGRATION.md` | Migration guide | Archive or remove |
| `FINAL_IMPLEMENTATION_SUMMARY.md` | Summary | Remove (redundant) |
| `IMPLEMENTATION_COMPLETE.md` | Status | Remove (redundant) |
| `MIGRATION_GUIDE.md` | Migration steps | Archive |
| `PROJECT_STRUCTURE.txt` | File structure | Remove (outdated) |
| `QUICK_REFERENCE.md` | Quick ref | Keep |
| `README_REDIS_SECTION.md` | Redis docs | Merge into README |
| `REDIS_CELERY_IMPLEMENTATION.md` | Implementation | Merge into ARCHITECTURE.md |
| `REDIS_CELERY_QUICKSTART.md` | Quick start | Keep |
| `REDIS_CELERY_SETUP.md` | Setup guide | Keep |
| `REFACTORING_COMPLETE.md` | Status | Remove (redundant) |
| `REFACTORING_SUMMARY.md` | Summary | Remove (redundant) |
| `SOLUTION_SUMMARY.md` | Summary | Remove (redundant) |
| `SPEECH_RECOGNITION_GUIDE.md` | STT guide | Keep |
| `SPEECH_RECOGNITION_SUMMARY.md` | STT summary | Merge into guide |
| `SQLITE_IMPLEMENTATION_SUMMARY.md` | SQLite details | Merge into ARCHITECTURE.md |
| `SQLITE_MIGRATION.md` | Migration | Archive |

### Test Files (Review)
| File | Notes |
|------|-------|
| `test_refactoring.py` | May be obsolete |
| `test_sqlite_history.py` | Covered by tests/test_history.py |
| `test_sqlite_simple.py` | Covered by tests/test_history.py |

## Cleanup Commands

```bash
# Remove legacy application files
rm app_streamlit.py app_api.py api_server.py batch_translator.py ai_translator.py

# Remove redundant documentation (after review)
rm CHECKLIST.md COMPLETE_SOLUTION_SUMMARY.md FINAL_IMPLEMENTATION_SUMMARY.md
rm IMPLEMENTATION_COMPLETE.md REFACTORING_COMPLETE.md REFACTORING_SUMMARY.md
rm SOLUTION_SUMMARY.md PROJECT_STRUCTURE.txt

# Remove old test files (after verifying new tests pass)
rm test_refactoring.py test_sqlite_history.py test_sqlite_simple.py
```

## Before Cleanup

1. Run all tests: `pytest tests/ -v`
2. Verify services work: `./start_services.sh`
3. Test the Streamlit app manually
4. Test the API endpoints
5. Backup if needed: `git stash` or commit current state
