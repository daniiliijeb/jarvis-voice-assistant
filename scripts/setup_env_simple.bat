@echo off
setlocal enabledelayedexpansion

REM Change to project root directory (one level up from scripts/)
cd /d "%~dp0.."
if not exist requirements-core.txt (
  echo ERROR: requirements-core.txt not found
  echo Make sure you run this script from the project root
  echo Current directory: %CD%
  echo.
  pause
  exit /b 1
)

echo Installing Jarvis...
echo Current directory: %CD%
echo.

echo [1/5] Checking Python 3.11...
py -3.11 -V >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.11 not found
  echo Install Python 3.11 from python.org
  set EXIT_CODE=1
  goto :error
)

echo [2/5] Creating virtual environment...
if exist .venv (
  echo .venv already exists, checking if it's valid...
  if not exist .venv\Scripts\activate.bat (
    echo Old .venv is corrupted, removing it...
    rmdir /s /q .venv
  )
)
if not exist .venv (
  echo Creating new virtual environment...
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create .venv
    set EXIT_CODE=1
    goto :error
  )
  echo Waiting for venv to be ready...
  timeout /t 2 /nobreak >nul
)

echo [3/5] Activating environment...
if not exist .venv\Scripts\python.exe (
  echo ERROR: .venv\Scripts\python.exe not found
  echo Virtual environment is corrupted
  echo Try deleting .venv folder and running again
  set EXIT_CODE=1
  goto :error
)

REM Use direct path to python instead of activate.bat
set PATH=%CD%\.venv\Scripts;%PATH%
if not exist .venv\Scripts\activate.bat (
  echo WARNING: activate.bat not found, using direct python path
) else (
  call .venv\Scripts\activate.bat
)

echo [4/5] Installing dependencies...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
  set EXIT_CODE=1
  goto :error
)

python -m pip install -r requirements-core.txt
if errorlevel 1 (
  set EXIT_CODE=1
  goto :error
)

python -m pip install -r requirements-dev.txt >nul 2>&1

echo Checking PyAudio...
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
  echo Installing PyAudio via pipwin...
  python -m pip install pipwin >nul 2>&1
  pipwin install pyaudio
)

echo Проверка ffmpeg (нужен для ElevenLabs)...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
  echo ffmpeg не найден. Устанавливаю...
  echo.
  echo Попытка установки через chocolatey...
  choco install ffmpeg -y >nul 2>&1
  if errorlevel 1 (
    echo Chocolatey недоступен, скачиваю portable версию ffmpeg...
    if not exist tools mkdir tools
    if not exist tools\ffmpeg (
      echo Скачивание ffmpeg...
      powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'tools\ffmpeg.zip'"
      if exist tools\ffmpeg.zip (
        echo Распаковка ffmpeg...
        powershell -Command "Expand-Archive -Path 'tools\ffmpeg.zip' -DestinationPath 'tools' -Force"
        for /d %%i in (tools\ffmpeg-*) do (
          move "%%i" "tools\ffmpeg" >nul 2>&1
        )
        del tools\ffmpeg.zip >nul 2>&1
        echo Добавление ffmpeg в PATH для этой сессии...
        set PATH=%CD%\tools\ffmpeg\bin;%PATH%
        echo ffmpeg установлен в tools\ffmpeg\bin
        echo ПРИМЕЧАНИЕ: ffmpeg будет автоматически доступен при запуске через run.bat
      ) else (
        echo ПРЕДУПРЕЖДЕНИЕ: Не удалось скачать ffmpeg автоматически
        echo Установите ffmpeg вручную с https://ffmpeg.org/download.html
        echo Или установите chocolatey и выполните: choco install ffmpeg
      )
    ) else (
      echo ffmpeg уже существует в папке tools
      set PATH=%CD%\tools\ffmpeg\bin;%PATH%
    )
  ) else (
    echo ffmpeg установлен через chocolatey
  )
) else (
  echo ffmpeg уже установлен
)

echo [5/5] Verifying installation...
python -c "import speech_recognition; import pyttsx3" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Verification failed
  set EXIT_CODE=1
  goto :error
)

echo Checking faster-whisper (для Whisper STT)...
python -c "import faster_whisper" >nul 2>&1
if errorlevel 1 (
  echo WARNING: faster-whisper не найден. Whisper STT будет недоступен.
  echo Установите вручную: pip install faster-whisper
) else (
  echo faster-whisper установлен. Whisper STT доступен.
)

if not exist jarvis\logs mkdir jarvis\logs
if not exist jarvis\data mkdir jarvis\data

echo.
echo ========================================
echo   ELEVENLABS API KEY (Optional)
echo ========================================
echo.
echo Для реалистичного голоса Jarvis нужен API ключ ElevenLabs.
echo Получить ключ: https://elevenlabs.io/app/settings/api-keys
echo.
echo Введите API ключ ElevenLabs (или нажмите Enter чтобы пропустить):
set /p ELEVENLABS_KEY="API Key: "
if not "%ELEVENLABS_KEY%"=="" (
  echo Сохранение API ключа...
  echo %ELEVENLABS_KEY% > jarvis\data\elevenlabs_api_key.txt
  echo API ключ сохранен!
  echo.
  echo Популярные голоса для Jarvis:
  echo   Adam (pNInz6obpgDQGcFmaJgB) - глубокий, уверенный [по умолчанию]
  echo   Antoni (ErXwobaYiN019PkySvjV) - четкий, быстрый
  echo   Josh (TxGEqnHWrfWFTfGW9XjX) - молодой, энергичный
  echo   Arnold (VR6AewLTigWG4xSOukaG) - мощный, авторитетный
  echo   Daniel (ThT5KcBeYPX3keUQqHPh) - британский, элегантный
  echo.
  echo Введите voice_id (или нажмите Enter для Adam по умолчанию):
  set /p VOICE_ID="Voice ID: "
  if not "%VOICE_ID%"=="" (
    echo %VOICE_ID% > jarvis\data\elevenlabs_voice_id.txt
    echo Voice ID сохранен!
  )
) else (
  echo API ключ не введен. Jarvis будет использовать стандартный голос.
  echo Вы можете добавить ключ позже в файл: jarvis\data\elevenlabs_api_key.txt
)

echo.
echo ========================================
echo   INSTALLATION COMPLETE
echo ========================================
echo.
echo Run: run.bat
echo Build: scripts\build_exe.bat
echo.
goto :end

:error
echo.
echo ========================================
echo   INSTALLATION FAILED
echo ========================================
echo.
goto :end

:end
pause
exit /b 0

