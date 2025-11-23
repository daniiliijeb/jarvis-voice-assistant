@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   ZAPUSK JARVIS
echo ========================================
echo.

if not exist .venv\Scripts\python.exe (
  echo ERROR: Virtual environment not found!
  echo Run: scripts\setup_env_simple.bat
  echo.
  pause
  exit /b 1
)

REM Безопасное добавление в PATH
set "VENV_PATH=%CD%\.venv\Scripts"
set "FFMPEG_PATH=%CD%\tools\ffmpeg\bin"

if exist "%FFMPEG_PATH%" (
  set "PATH=%FFMPEG_PATH%;%PATH%"
)
set "PATH=%VENV_PATH%;%PATH%"

echo Запуск Jarvis...
echo.

python -m jarvis.app.main
set EXIT_CODE=!ERRORLEVEL!

echo.
echo ========================================
if !EXIT_CODE! EQU 0 (
  echo   JARVIS ZAVERSHIL RABOTU USPESHNO
) else (
  echo   JARVIS ZAVERSHILSYA S OSHIBKOY
)
echo ========================================
echo.
echo Exit code: !EXIT_CODE!
echo.
echo Press any key to exit...
pause >nul
exit /b !EXIT_CODE!
