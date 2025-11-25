#!/bin/bash
# 업무일지 AI 분석 시스템 설치 스크립트 (Linux/Mac) - uv 사용

echo "========================================"
echo "Work Log AI Analysis System Setup (uv)"
echo "========================================"
echo

# Check Python installation
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python3 first"
    exit 1
fi
python3 --version
echo

# Check and install uv
echo "[2/5] Checking uv installation..."
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install uv"
        echo "Please install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "uv installed successfully!"
else
    uv --version
    echo "uv is already installed!"
fi
echo

# Remove old virtual environment
echo "[3/5] Setting up virtual environment..."
if [ -d ".venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf .venv
fi

# Create virtual environment with uv
echo "Creating virtual environment with uv..."
uv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi
echo "Virtual environment created successfully!"
echo

# Install dependencies with uv
echo "[4/5] Installing dependencies with uv..."
uv pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully!"
echo

# Verify installation
echo "[5/5] Verifying installation..."
source .venv/bin/activate
python -c "import PySide6; print('PySide6:', PySide6.__version__)" 2>/dev/null
deactivate
echo

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo
echo "Virtual environment: .venv (managed by uv)"
echo
echo "To run the program:"
echo "  ./run.sh"
echo
echo "If Ollama is not installed:"
echo "  1. Download from https://ollama.ai"
echo "  2. Run: ollama pull llama3.2"
echo
echo "To update dependencies:"
echo "  uv pip install -r requirements.txt --upgrade"
echo
