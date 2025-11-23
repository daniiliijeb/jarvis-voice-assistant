@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Jarvis Voice Assistant - Installer

color 0A
cls

echo.
echo ================================================================
echo   JARVIS VOICE ASSISTANT - INSTALLER
echo ================================================================
echo.
echo   Automatic installation and setup
echo.
echo   This installer will:
echo   [OK] Check and install Python 3.11
echo   [OK] Create virtual environment
echo   [OK] Install all dependencies
echo   [OK] Configure Jarvis
echo.
echo ================================================================
echo.
pause

set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

REM ========================================
REM STEP 1: Check Python
REM ========================================
echo.
echo ================================================================
echo   [STEP 1/6] Checking Python 3.11
echo ================================================================
echo.

py -3.11 -V >nul 2>&1
if errorlevel 1 (
    echo   [X] Python 3.11 not found
    echo.
    echo   Downloading Python 3.11.9 installer...
    echo   [                    ] 0%%
    
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP%\python-3.11.9-installer.exe"
    
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing } catch { Write-Host 'Error'; exit 1 }"
    
    if not exist "%PYTHON_INSTALLER%" (
        color 0C
        echo   [X] ERROR: Failed to download Python
        echo.
        echo   Please install Python 3.11 manually:
        echo   https://www.python.org/downloads/
        echo.
        echo   IMPORTANT: Select "Add Python to PATH" during installation
        echo.
        pause
        exit /b 1
    )
    
    echo   [====================] 100%%
    echo   [OK] Installer downloaded
    echo.
    echo   Starting Python installer...
    echo   IMPORTANT: Select "Add Python to PATH" during installation!
    echo.
    pause
    
    start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1
    
    timeout /t 5 /nobreak >nul
    
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
    set "PATH=%PATH%;%ProgramFiles%\Python311;%ProgramFiles%\Python311\Scripts"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311-32;%LOCALAPPDATA%\Programs\Python\Python311-32\Scripts"
    
    py -3.11 -V >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo   [X] Python not found after installation
        echo.
        echo   Please restart this script after installing Python
        echo   or add Python to PATH manually
        echo.
        pause
        exit /b 1
    )
    
    color 0A
    echo   [OK] Python 3.11 installed successfully!
) else (
    echo   [OK] Python 3.11 found
    py -3.11 -V
)

REM ========================================
REM STEP 2: Create virtual environment
REM ========================================
echo.
echo ================================================================
echo   [STEP 2/6] Creating virtual environment
echo ================================================================
echo.

if exist .venv (
    echo   [~] Virtual environment already exists
    if not exist .venv\Scripts\python.exe (
        echo   [~] Environment is corrupted, recreating...
        rmdir /s /q .venv
        py -3.11 -m venv .venv
    ) else (
        echo   [OK] Virtual environment is OK
    )
) else (
    echo   [~] Creating virtual environment...
    echo   [                    ] 0%%
    py -3.11 -m venv .venv
    if errorlevel 1 (
        color 0C
        echo   [X] ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    echo   [====================] 100%%
    echo   [OK] Virtual environment created
)

if not exist .venv\Scripts\python.exe (
    color 0C
    echo   [X] ERROR: Virtual environment not created
    pause
    exit /b 1
)

set "PATH=%CD%\.venv\Scripts;%PATH%"

REM ========================================
REM STEP 3: Install dependencies
REM ========================================
echo.
echo ================================================================
echo   [STEP 3/6] Installing dependencies
echo ================================================================
echo.

echo   [~] Updating pip...
python -m pip install --upgrade pip --quiet >nul 2>&1
if errorlevel 1 (
    echo   [X] Error updating pip
) else (
    echo   [OK] pip updated
)

echo.
echo   [~] Installing core dependencies...
echo   [                    ] 0%%
python -m pip install -r requirements-core.txt
if errorlevel 1 (
    color 0C
    echo   [X] ERROR: Failed to install dependencies
    echo   Check your internet connection
    pause
    exit /b 1
)
echo   [====================] 100%%
echo   [OK] Core dependencies installed

echo.
echo   [~] Checking PyAudio...
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo   [~] Installing PyAudio via pipwin...
    python -m pip install pipwin >nul 2>&1
    pipwin install pyaudio >nul 2>&1
    if errorlevel 1 (
        echo   [WARNING] PyAudio not installed
    ) else (
        echo   [OK] PyAudio installed
    )
) else (
    echo   [OK] PyAudio already installed
)

echo.
echo   [~] Installing additional packages...

python -c "import faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo   [~] faster-whisper...
    python -m pip install faster-whisper >nul 2>&1
    if errorlevel 1 (
        echo   [WARNING] faster-whisper not installed (Whisper STT unavailable)
    ) else (
        echo   [OK] faster-whisper installed
    )
) else (
    echo   [OK] faster-whisper already installed
)

python -c "import sentence_transformers" >nul 2>&1
if errorlevel 1 (
    echo   [~] sentence-transformers...
    python -m pip install sentence-transformers >nul 2>&1
    if errorlevel 1 (
        echo   [WARNING] sentence-transformers not installed (Semantic Router unavailable)
    ) else (
        echo   [OK] sentence-transformers installed
    )
) else (
    echo   [OK] sentence-transformers already installed
)

python -c "import pygetwindow; import pyautogui" >nul 2>&1
if errorlevel 1 (
    echo   [~] pygetwindow and pyautogui...
    python -m pip install pygetwindow pyautogui >nul 2>&1
    if errorlevel 1 (
        echo   [WARNING] pygetwindow/pyautogui not installed (Context-Aware unavailable)
    ) else (
        echo   [OK] pygetwindow and pyautogui installed
    )
) else (
    echo   [OK] pygetwindow and pyautogui already installed
)

REM ========================================
REM STEP 4: Setup folders
REM ========================================
echo.
echo ================================================================
echo   [STEP 4/6] Setting up folders and files
echo ================================================================
echo.

if not exist jarvis\logs (
    mkdir jarvis\logs
    echo   [OK] Created jarvis\logs folder
) else (
    echo   [OK] jarvis\logs folder exists
)

if not exist jarvis\data (
    mkdir jarvis\data
    echo   [OK] Created jarvis\data folder
) else (
    echo   [OK] jarvis\data folder exists
)

if not exist jarvis\data\version.txt (
    echo 0.1.0 > jarvis\data\version.txt
    echo   [OK] Created version file
) else (
    echo   [OK] Version file exists
)

REM ========================================
REM STEP 5: Setup updates
REM ========================================
echo.
echo ================================================================
echo   [STEP 5/6] Setting up updates
echo ================================================================
echo.
echo   For automatic update checks, enter GitHub repository
echo   Example: daniiliijeb/jarvis-voice-assistant
echo   Or press Enter to skip
echo.
set /p GITHUB_REPO="GitHub repository: "

if not "!GITHUB_REPO!"=="" (
    (
        echo GITHUB_REPO=!GITHUB_REPO!
    ) > .env
    echo   [OK] Update settings saved
) else (
    echo   [~] Updates disabled (can be configured later)
)

REM ========================================
REM STEP 6: Setup ElevenLabs (optional)
REM ========================================
echo.
echo ================================================================
echo   [STEP 6/6] Setting up ElevenLabs (optional)
echo ================================================================
echo.
echo   For realistic Jarvis voice, you need ElevenLabs API key
echo   Get key: https://elevenlabs.io/app/settings/api-keys
echo   Or press Enter to skip
echo.
set /p ELEVENLABS_KEY="ElevenLabs API key: "

if not "!ELEVENLABS_KEY!"=="" (
    echo !ELEVENLABS_KEY! > jarvis\data\elevenlabs_api_key.txt
    echo   [OK] API key saved
    echo.
    echo   Popular voices:
    echo   - Adam (pNInz6obpgDQGcFmaJgB) - default
    echo   - Antoni (ErXwobaYiN019PkySvjV)
    echo   - Josh (TxGEqnHWrfWFTfGW9XjX)
    echo.
    set /p VOICE_ID="Voice ID (or Enter for Adam): "
    if not "!VOICE_ID!"=="" (
        echo !VOICE_ID! > jarvis\data\elevenlabs_voice_id.txt
        echo   [OK] Voice ID saved
    )
) else (
    echo   [~] API key not entered (will use standard voice)
)

REM ========================================
REM Final check
REM ========================================
echo.
echo ================================================================
echo   [CHECK] Final installation check
echo ================================================================
echo.

python -c "import speech_recognition; import pyttsx3" >nul 2>&1
if errorlevel 1 (
    color 0C
    echo   [X] ERROR: Check failed
    pause
    exit /b 1
)

echo   [OK] All checks passed successfully!

echo.
echo   [~] Creating run file...
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%%~dp0"
    echo if not exist .venv\Scripts\python.exe ^(
    echo   echo ERROR: Virtual environment not found!
    echo   echo Run: INSTALLER.bat
    echo   pause
    echo   exit /b 1
    echo ^)
    echo set "PATH=%%CD%%\.venv\Scripts;%%PATH%%"
    echo python -m jarvis.app.main
    echo pause
) > RUN_JARVIS.bat

echo   [OK] RUN_JARVIS.bat file created

REM ========================================
REM Completion
REM ========================================
color 0A
echo.
echo ================================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo   Jarvis installed in: %INSTALL_DIR%
echo.
echo   To run:
echo   - Double-click: RUN_JARVIS.bat
echo   - Or run: python -m jarvis.app.main
echo.
echo   To check system:
echo   python -m jarvis.app.main --health
echo.
pause
exit /b 0

