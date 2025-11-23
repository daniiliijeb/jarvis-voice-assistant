@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   JARVIS - STARTING
echo ========================================
echo.

if not exist .venv\Scripts\python.exe (
  echo ERROR: Virtual environment not found!
  echo Run: INSTALLER.bat
  echo.
  pause
  exit /b 1
)

set "VENV_PATH=%CD%\.venv\Scripts"
set "FFMPEG_PATH=%CD%\tools\ffmpeg\bin"

if exist "%FFMPEG_PATH%" (
  set "PATH=%FFMPEG_PATH%;%PATH%"
)
set "PATH=%VENV_PATH%;%PATH%"

echo Starting Jarvis...
echo.

python -m jarvis.app.main
set EXIT_CODE=!ERRORLEVEL!

echo.
echo ========================================
if !EXIT_CODE! EQU 0 (
  echo   JARVIS FINISHED SUCCESSFULLY
) else (
  echo   JARVIS FINISHED WITH ERROR
)
echo ========================================
echo.
echo Exit code: !EXIT_CODE!
echo.
pause
exit /b !EXIT_CODE!
