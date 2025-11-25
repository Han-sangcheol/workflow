@echo off
chcp 65001 > nul 2>&1
cls

echo ========================================
echo Work Log AI Analysis System Setup (uv)
echo ========================================
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Check and install uv
echo [2/5] Checking uv installation...
python -m uv --version > nul 2>&1
if errorlevel 1 (
    echo uv is not installed. Installing uv...
    python -m pip install uv
    if errorlevel 1 (
        echo ERROR: Failed to install uv
        echo Please run: python -m pip install uv
        pause
        exit /b 1
    )
    echo uv installed successfully!
) else (
    python -m uv --version
    echo uv is already installed!
)
echo.

REM Remove old virtual environment
echo [3/5] Setting up virtual environment...
if exist .venv (
    echo Removing old virtual environment...
    rmdir /s /q .venv 2>nul
    timeout /t 1 /nobreak >nul
    if exist .venv (
        echo WARNING: Some files are locked, using --clear flag...
    )
)

REM Create virtual environment with uv (use --clear to overwrite if exists)
echo Creating virtual environment with uv...
python -m uv venv .venv --clear
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo.
    echo Please try manually:
    echo   1. Close any Python/GUI applications
    echo   2. Delete .venv folder manually
    echo   3. Run setup.bat again
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

REM Install dependencies using uv from outside the venv
echo [4/5] Installing dependencies with uv...
echo Installing packages into .venv...
python -m uv pip install --python .venv --link-mode=copy -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: uv pip failed, trying with venv pip...
    call .venv\Scripts\activate.bat
    python -m ensurepip --upgrade 2>nul
    python -m pip install --upgrade pip 2>nul
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        deactivate
        pause
        exit /b 1
    )
    deactivate
)
echo Dependencies installed successfully!
echo.

REM Verify installation
echo [5/5] Verifying installation...
call .venv\Scripts\activate.bat

echo Checking installed packages...
python -c "import PySide6; print('[OK] PySide6:', PySide6.__version__)" 2>nul
if errorlevel 1 (
    echo [FAIL] PySide6 not found
)

python -c "import fitz; print('[OK] PyMuPDF installed')" 2>nul
if errorlevel 1 (
    echo [FAIL] PyMuPDF not found
)

python -c "import docx; print('[OK] python-docx installed')" 2>nul
if errorlevel 1 (
    echo [FAIL] python-docx not found
)

python -c "import requests; print('[OK] requests installed')" 2>nul
if errorlevel 1 (
    echo [FAIL] requests not found
)

python -c "import psutil; print('[OK] psutil installed')" 2>nul
if errorlevel 1 (
    echo [FAIL] psutil not found
)

python -c "import GPUtil; print('[OK] GPUtil installed')" 2>nul
if errorlevel 1 (
    echo [WARNING] GPUtil not found ^(optional for GPU monitoring^)
)

deactivate
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Virtual environment: .venv
echo Package manager: uv
echo.
echo To run the program:
echo   run.bat
echo.
echo If Ollama is not installed:
echo   1. Download from https://ollama.ai
echo   2. Run: ollama pull llama3.2
echo.
echo To add new packages:
echo   python -m uv pip install --python .venv package-name
echo   OR
echo   .venv\Scripts\activate
echo   pip install package-name
echo.
pause
