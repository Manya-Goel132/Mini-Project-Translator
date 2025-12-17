#!/bin/bash

# Start all services for the AI Translator application
# This script starts Redis, Celery workers, Flask API, and Streamlit

set -e

echo "🚀 Starting AI Translator Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
echo -e "${YELLOW}Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Starting Redis..."
    
    # Try to start Redis based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start redis || redis-server --daemonize yes
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo systemctl start redis || redis-server --daemonize yes
    else
        echo "Please start Redis manually: redis-server"
        exit 1
    fi
    
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
fi

echo ""

# Create log directory
mkdir -p logs

# Start Celery worker
echo -e "${YELLOW}Starting Celery worker...${NC}"
celery -A tasks worker --loglevel=info --logfile=logs/celery.log --detach
sleep 2
echo -e "${GREEN}✅ Celery worker started${NC}"

echo ""

# Start FastAPI
echo -e "${YELLOW}Starting FastAPI server...${NC}"
nohup uvicorn api_server_fastapi:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > logs/api.pid
sleep 2
echo -e "${GREEN}✅ FastAPI server started (PID: $API_PID)${NC}"

echo ""

# Start Streamlit
echo -e "${YELLOW}Starting Streamlit app...${NC}"
nohup streamlit run app_streamlit_enhanced.py --server.port 8501 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > logs/streamlit.pid
sleep 3
echo -e "${GREEN}✅ Streamlit app started (PID: $STREAMLIT_PID)${NC}"

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo "📊 Service URLs:"
echo "  - Streamlit App: http://localhost:8501"
echo "  - FastAPI Server: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "  - Celery: logs/celery.log"
echo "  - API: logs/api.log"
echo "  - Streamlit: logs/streamlit.log"
echo ""
echo "🛑 To stop all services, run: ./stop_services.sh"
echo ""
