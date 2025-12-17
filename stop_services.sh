#!/bin/bash

# Stop all services for the AI Translator application

set -e

echo "🛑 Stopping AI Translator Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Streamlit
if [ -f logs/streamlit.pid ]; then
    STREAMLIT_PID=$(cat logs/streamlit.pid)
    echo -e "${YELLOW}Stopping Streamlit (PID: $STREAMLIT_PID)...${NC}"
    kill $STREAMLIT_PID 2>/dev/null || echo "Streamlit already stopped"
    rm logs/streamlit.pid
    echo -e "${GREEN}✅ Streamlit stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Streamlit PID file not found${NC}"
fi

echo ""

# Stop FastAPI
if [ -f logs/api.pid ]; then
    API_PID=$(cat logs/api.pid)
    echo -e "${YELLOW}Stopping FastAPI server (PID: $API_PID)...${NC}"
    kill $API_PID 2>/dev/null || echo "FastAPI server already stopped"
    rm logs/api.pid
    echo -e "${GREEN}✅ FastAPI server stopped${NC}"
else
    echo -e "${YELLOW}⚠️  FastAPI PID file not found${NC}"
fi

echo ""

# Stop Celery worker
echo -e "${YELLOW}Stopping Celery worker...${NC}"
pkill -f "celery.*worker" || echo "Celery worker already stopped"
echo -e "${GREEN}✅ Celery worker stopped${NC}"

echo ""

# Optionally stop Redis (commented out by default)
# echo -e "${YELLOW}Stopping Redis...${NC}"
# if [[ "$OSTYPE" == "darwin"* ]]; then
#     brew services stop redis
# elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
#     sudo systemctl stop redis
# fi
# echo -e "${GREEN}✅ Redis stopped${NC}"

echo ""
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo ""
echo "Note: Redis is still running. To stop it:"
echo "  macOS: brew services stop redis"
echo "  Linux: sudo systemctl stop redis"
echo ""
