@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   Workflow AI Analysis System - Build Script
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Set virtual environment Python path
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

REM Check virtual environment
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found: %VENV_PYTHON%
    echo [!] Please create a virtual environment first.
    pause
    exit /b 1
)

echo [1/4] Using virtual environment Python: %VENV_PYTHON%

REM Check and install pip
echo.
echo [2/4] Checking build tools...
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [!] pip not found in virtual environment. Installing...
    "%VENV_PYTHON%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo [ERROR] Failed to install pip.
        pause
        exit /b 1
    )
    echo [DONE] pip installed successfully
)

REM Check PyInstaller installation
"%VENV_PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller is not installed in virtual environment.
    echo [!] Installing via pip...
    "%VENV_PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
    echo [DONE] PyInstaller installed successfully
)

REM Create icon (requires Pillow)
echo.
echo [2.5/4] Creating icon...
if not exist "resources\icon.ico" (
    "%VENV_PYTHON%" -c "import PIL" >nul 2>&1
    if errorlevel 1 (
        echo [!] Installing Pillow...
        "%VENV_PYTHON%" -m pip install Pillow
    )
    "%VENV_PYTHON%" build\create_icon.py
)

REM Run build
echo.
echo [3/4] Starting build...
echo.
"%VENV_PYTHON%" build\build.py --clean %*

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo ============================================================
echo   Output location:
echo   - Executable: dist\WorkflowAnalyzer\WorkflowAnalyzer.exe
echo   - Installer: dist\installer\WorkflowAnalyzer_Setup_*.exe
echo ============================================================
echo.

REM Option to open output folder
set /p OPEN_FOLDER="Open output folder? (Y/N): "
if /i "!OPEN_FOLDER!"=="Y" (
    if exist "dist\installer" (
        explorer "dist\installer"
    ) else if exist "dist" (
        explorer "dist"
    )
)

endlocal
