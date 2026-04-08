@echo off
chcp 65001 > nul 2>&1
REM ============================================================================
REM @echo off
REM - Meaning: Turn off command echo
REM - Description: Prevents each command from being displayed on screen
REM - '@' symbol: Also hides this command itself from display
REM ============================================================================
REM chcp 65001
REM - Meaning: CHange Code Page (change code page)
REM - Description: Set console character encoding to UTF-8 (65001)
REM - Purpose: Ensures Korean/Unicode characters display correctly
REM 
REM > nul
REM - Meaning: Redirect stdout to nul (trash)
REM - Description: Suppress command output from being displayed
REM
REM 2>&1
REM - Meaning: Redirect stderr (2) to stdout (1)
REM - Description: Also suppress error messages
REM ============================================================================

cls
REM ============================================================================
REM cls
REM - Meaning: CLear Screen
REM - Description: Clear all contents from console and start fresh
REM ============================================================================

echo ========================================
echo Work Log AI Analysis System
echo ========================================
echo.
REM ============================================================================
REM echo
REM - Meaning: Display text on screen
REM - Description: Print specified string to console
REM
REM echo.
REM - Meaning: Print empty line
REM - Description: Adding a period (.) after echo prints a blank line
REM ============================================================================

REM ============================================================================
REM Virtual Environment Existence Check Section
REM ============================================================================
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)
REM ============================================================================
REM if not exist "path" (command)
REM - Meaning: Execute commands in parentheses if file/folder doesn't exist
REM - Description: Handle error if .venv activation script is missing
REM
REM pause
REM - Meaning: Pause execution
REM - Description: Display "Press any key..." and wait for user input
REM - Purpose: Prevent window from closing immediately so user can read error
REM
REM exit /b 1
REM - Meaning: Exit batch file
REM - /b: Exit only current batch file (keep cmd window open)
REM - 1: Set exit code (errorlevel) to 1 (non-zero means error)
REM ============================================================================

REM ============================================================================
REM Virtual Environment Activation Section
REM ============================================================================
call .venv\Scripts\activate.bat
REM ============================================================================
REM call
REM - Meaning: Call another batch file
REM - Description: Execute specified batch file and return to current script
REM - Note: Without 'call', control transfers to called batch and never returns
REM
REM activate.bat
REM - Meaning: Python virtual environment activation script
REM - Description: Activate .venv to use its Python interpreter and packages
REM ============================================================================

REM ============================================================================
REM Ollama Server Status Check Section
REM ============================================================================
echo Checking Ollama...
curl -s http://localhost:11434/api/tags > nul 2>&1
REM ============================================================================
REM curl
REM - Meaning: Client URL - HTTP request tool
REM - Description: Send HTTP request to specified URL
REM
REM -s
REM - Meaning: Silent mode
REM - Description: Suppress progress meter and error messages
REM
REM http://localhost:11434/api/tags
REM - Meaning: Ollama local server API endpoint
REM - Description: Call tags API to check if Ollama is running
REM - Port 11434: Ollama default port
REM ============================================================================

if errorlevel 1 (
    echo Ollama server not running. The application will start it automatically.
    echo.
)
REM ============================================================================
REM if errorlevel 1
REM - Meaning: Check if previous command's return code (errorlevel) is 1 or more
REM - Description: If curl fails (server unreachable), errorlevel becomes non-zero
REM - 0: Success, 1+: Error occurred
REM
REM Note: In Windows batch, errorlevel comparison means "greater than or equal"
REM       So "errorlevel 1" checks if errorlevel >= 1
REM ============================================================================

REM ============================================================================
REM Main Program Execution Section
REM ============================================================================
echo.
echo Starting application...
echo.
python main.py
REM ============================================================================
REM python main.py
REM - Meaning: Run main.py script with Python interpreter
REM - Description: Execute main application with virtual environment activated
REM - The venv's python.exe is used, allowing proper package imports
REM ============================================================================

REM ============================================================================
REM Virtual Environment Deactivation and Exit Section
REM ============================================================================
deactivate
REM ============================================================================
REM deactivate
REM - Meaning: Deactivate virtual environment
REM - Description: Deactivate the venv that was activated by activate.bat
REM - Purpose: Return to system default Python environment after program exits
REM - Note: This command is defined/created when activate.bat runs
REM ============================================================================
