@echo off
chcp 65001 >nul
setlocal

REM Change to project root directory (one level up from scripts/)
cd /d "%~dp0.."

if not exist .venv\Scripts\python.exe (
  echo Виртуальное окружение не найдено. Сначала запустите scripts\setup_env_simple.bat
  pause
  exit /b 1
)

REM Use direct path to python
set PATH=%CD%\.venv\Scripts;%PATH%
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

where pyinstaller >nul 2>&1
if errorlevel 1 (
  echo PyInstaller не найден. Устанавливаю...
  pip install pyinstaller
  if errorlevel 1 (
    echo Не удалось установить PyInstaller.
    exit /b 1
  )
)

echo Сборка Jarvis.exe...
pyinstaller --clean --noconfirm --onefile --name Jarvis --noconsole --paths . jarvis\app\main.py

if errorlevel 1 (
  echo Сборка не удалась.
  exit /b 1
)

echo.
echo ========================================
echo   СБОРКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Готовый файл: dist\Jarvis.exe
echo Теперь можно запустить его двойным кликом.
echo.
pause
exit /b 0



