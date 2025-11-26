@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   업무일지 AI 분석 시스템 - 빌드 스크립트
echo ============================================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM 가상환경 Python 경로 설정
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

REM 가상환경 확인
if not exist "%VENV_PYTHON%" (
    echo [오류] 가상환경을 찾을 수 없습니다: %VENV_PYTHON%
    echo [!] 먼저 가상환경을 생성하세요.
    pause
    exit /b 1
)

echo [1/4] 가상환경 Python 사용: %VENV_PYTHON%

REM pip 설치 확인 및 설치
echo.
echo [2/4] 빌드 도구 확인 중...
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [!] pip가 가상환경에 없습니다. 설치 중...
    "%VENV_PYTHON%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo [오류] pip 설치에 실패했습니다.
        pause
        exit /b 1
    )
    echo [완료] pip 설치 완료
)

REM PyInstaller 설치 확인
"%VENV_PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller가 가상환경에 설치되어 있지 않습니다.
    echo [!] pip를 사용하여 설치 중...
    "%VENV_PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [오류] PyInstaller 설치에 실패했습니다.
        pause
        exit /b 1
    )
    echo [완료] PyInstaller 설치 완료
)

REM 아이콘 생성 (Pillow 필요)
echo.
echo [2.5/4] 아이콘 생성 중...
if not exist "resources\icon.ico" (
    "%VENV_PYTHON%" -c "import PIL" >nul 2>&1
    if errorlevel 1 (
        echo [!] Pillow 설치 중...
        "%VENV_PYTHON%" -m pip install Pillow
    )
    "%VENV_PYTHON%" build\create_icon.py
)

REM 빌드 실행
echo.
echo [3/4] 빌드 시작...
echo.
"%VENV_PYTHON%" build\build.py --clean %*

if errorlevel 1 (
    echo.
    echo [오류] 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [4/4] 빌드 완료!
echo.
echo ============================================================
echo   결과물 위치:
echo   - 실행 파일: dist\WorkflowAnalyzer\WorkflowAnalyzer.exe
echo   - 설치 프로그램: dist\installer\WorkflowAnalyzer_Setup_*.exe
echo ============================================================
echo.

REM 결과물 폴더 열기 옵션
set /p OPEN_FOLDER="결과물 폴더를 열까요? (Y/N): "
if /i "!OPEN_FOLDER!"=="Y" (
    if exist "dist\installer" (
        explorer "dist\installer"
    ) else if exist "dist" (
        explorer "dist"
    )
)

endlocal

