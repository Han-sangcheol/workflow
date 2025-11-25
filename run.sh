#!/bin/bash
# 업무일지 AI 분석 시스템 실행 스크립트 (Linux/Mac)

echo "========================================"
echo "Work Log AI Analysis System"
echo "========================================"
echo

# Check virtual environment
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check Ollama
echo "Checking Ollama server..."
curl -s http://localhost:11434/api/tags > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo
    echo "WARNING: Cannot connect to Ollama server"
    echo "Please make sure Ollama is running: ollama serve"
    echo
    sleep 3
fi

# Run program
echo
echo "Starting application..."
echo
python main.py

# Deactivate virtual environment
deactivate
