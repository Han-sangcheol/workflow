@echo off
chcp 65001 > nul 2>&1
cls

echo ========================================
echo Work Log AI Analysis System
echo ========================================
echo.

REM Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check Ollama (프로그램이 자동으로 시작합니다)
echo Checking Ollama...
curl -s http://localhost:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo Ollama server not running. The application will start it automatically.
    echo.
)

REM Run program
echo.
echo Starting application...
echo.
python main.py

REM Deactivate virtual environment
deactivate
