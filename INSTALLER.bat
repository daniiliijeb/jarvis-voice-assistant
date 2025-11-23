@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM   JARVIS VOICE ASSISTANT - INSTALLER
REM   Автоматическая установка и настройка
REM ========================================

echo.
echo ========================================
echo   JARVIS VOICE ASSISTANT - INSTALLER
echo ========================================
echo.
echo Этот установщик автоматически:
echo   - Проверит наличие Python 3.11
echo   - Установит Python если нужно
echo   - Создаст виртуальное окружение
echo   - Установит все зависимости
echo   - Настроит Jarvis для работы
echo.
echo ========================================
echo.

REM Выбор папки для установки
echo [ШАГ 1/6] Выбор папки для установки
echo.
set "INSTALL_DIR=%USERPROFILE%\Jarvis"
echo Текущая папка установки: %INSTALL_DIR%
echo.
echo Нажмите Enter для установки в: %INSTALL_DIR%
echo Или введите другой путь:
set /p CUSTOM_DIR="Путь: "

if not "!CUSTOM_DIR!"=="" (
    set "INSTALL_DIR=!CUSTOM_DIR!"
)

echo.
echo Установка будет выполнена в: %INSTALL_DIR%
echo.
pause

REM Создание папки
if not exist "%INSTALL_DIR%" (
    echo Создание папки установки...
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать папку %INSTALL_DIR%
        pause
        exit /b 1
    )
)

REM Определение папки с установщиком (откуда запускается)
set "SOURCE_DIR=%~dp0"

REM Копирование файлов проекта в папку установки
echo.
echo Копирование файлов проекта...
echo Из: %SOURCE_DIR%
echo В: %INSTALL_DIR%

REM Копируем основные файлы и папки
xcopy "%SOURCE_DIR%jarvis" "%INSTALL_DIR%\jarvis\" /E /I /Y /Q >nul
xcopy "%SOURCE_DIR%requirements-core.txt" "%INSTALL_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%requirements-dev.txt" "%INSTALL_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%scripts" "%INSTALL_DIR%\scripts\" /E /I /Y /Q >nul
if exist "%SOURCE_DIR%README.md" xcopy "%SOURCE_DIR%README.md" "%INSTALL_DIR%\" /Y /Q >nul

cd /d "%INSTALL_DIR%"

REM Проверка Python
echo.
echo [ШАГ 2/6] Проверка Python 3.11
echo.
py -3.11 -V >nul 2>&1
if errorlevel 1 (
    echo Python 3.11 не найден!
    echo.
    echo Установка Python 3.11...
    echo.
    echo Скачивание установщика Python...
    
    REM Скачивание Python 3.11
    echo Определение архитектуры системы...
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP%\python-3.11.9-installer.exe"
    
    echo Скачивание установщика Python 3.11.9...
    powershell -Command "try { Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing } catch { Write-Host 'Ошибка скачивания'; exit 1 }"
    
    if not exist "%PYTHON_INSTALLER%" (
        echo ОШИБКА: Не удалось скачать Python
        echo.
        echo Пожалуйста, установите Python 3.11 вручную:
        echo https://www.python.org/downloads/
        echo.
        echo ВАЖНО: При установке выберите "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    
    if not exist "%PYTHON_INSTALLER%" (
        echo ОШИБКА: Не удалось скачать Python
        echo.
        echo Пожалуйста, установите Python 3.11 вручную:
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    
    echo Запуск установщика Python...
    echo ВАЖНО: Установите Python с опцией "Add Python to PATH"
    echo.
    start /wait "" "%PYTHON_INSTALLER%"
    
    REM Ожидание установки
    timeout /t 3 /nobreak >nul
    
    REM Проверка после установки
    py -3.11 -V >nul 2>&1
    if errorlevel 1 (
        echo ОШИБКА: Python 3.11 не установлен или не добавлен в PATH
        echo.
        echo Пожалуйста, установите Python 3.11 вручную:
        echo https://www.python.org/downloads/
        echo И убедитесь, что выбрали "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    
    echo Python 3.11 успешно установлен!
) else (
    echo Python 3.11 найден!
    py -3.11 -V
)

echo.
echo [ШАГ 3/6] Создание виртуального окружения
echo.

if exist .venv (
    echo Виртуальное окружение уже существует
    if not exist .venv\Scripts\python.exe (
        echo Окружение повреждено, пересоздаю...
        rmdir /s /q .venv
        py -3.11 -m venv .venv
    )
) else (
    echo Создание виртуального окружения...
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
)

if not exist .venv\Scripts\python.exe (
    echo ОШИБКА: Виртуальное окружение не создано
    pause
    exit /b 1
)

echo Виртуальное окружение создано успешно!

REM Активация окружения
set "PATH=%CD%\.venv\Scripts;%PATH%"

echo.
echo [ШАГ 4/6] Установка зависимостей
echo.

echo Обновление pip...
python -m pip install --upgrade pip --quiet

echo Установка основных зависимостей...
python -m pip install -r requirements-core.txt
if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости
    echo.
    echo Проверьте подключение к интернету и попробуйте снова
    pause
    exit /b 1
)

echo Установка PyAudio...
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo PyAudio не найден, устанавливаю через pipwin...
    python -m pip install pipwin >nul 2>&1
    pipwin install pyaudio
)

echo Проверка faster-whisper...
python -c "import faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo faster-whisper не найден, устанавливаю...
    python -m pip install faster-whisper
    if errorlevel 1 (
        echo WARNING: Не удалось установить faster-whisper
        echo Whisper STT будет недоступен
        echo Установите вручную: pip install faster-whisper
    ) else (
        echo faster-whisper установлен успешно!
    )
) else (
    echo faster-whisper уже установлен
)

echo Проверка sentence-transformers...
python -c "import sentence_transformers" >nul 2>&1
if errorlevel 1 (
    echo sentence-transformers не найден, устанавливаю...
    python -m pip install sentence-transformers
    if errorlevel 1 (
        echo WARNING: Не удалось установить sentence-transformers
        echo Semantic Router будет недоступен
        echo Установите вручную: pip install sentence-transformers
    ) else (
        echo sentence-transformers установлен успешно!
    )
) else (
    echo sentence-transformers уже установлен
)

echo Проверка pygetwindow и pyautogui...
python -c "import pygetwindow; import pyautogui" >nul 2>&1
if errorlevel 1 (
    echo pygetwindow/pyautogui не найдены, устанавливаю...
    python -m pip install pygetwindow pyautogui
    if errorlevel 1 (
        echo WARNING: Не удалось установить pygetwindow/pyautogui
        echo Context-Aware команды будут недоступны
    ) else (
        echo pygetwindow и pyautogui установлены успешно!
    )
) else (
    echo pygetwindow и pyautogui уже установлены
)

echo.
echo [ШАГ 5/6] Настройка Jarvis
echo.

REM Создание необходимых папок
if not exist jarvis\logs mkdir jarvis\logs
if not exist jarvis\data mkdir jarvis\data

REM Создание файла версии
if not exist jarvis\data\version.txt (
    echo 0.1.0 > jarvis\data\version.txt
)

REM Настройка GitHub репозитория для обновлений
echo.
echo ========================================
echo   НАСТРОЙКА ОБНОВЛЕНИЙ (ОПЦИОНАЛЬНО)
echo ========================================
echo.
echo Для автоматической проверки обновлений укажите GitHub репозиторий
echo Например: yourusername/jarvis-voice-assistant
echo Если оставите пустым - обновления отключены
echo.
set /p GITHUB_REPO="Введите GitHub репозиторий (username/repo-name или Enter чтобы пропустить): "

if not "!GITHUB_REPO!"=="" (
    echo.
    echo GitHub репозиторий для обновлений: !GITHUB_REPO!
    echo Создание файла с настройками...
    (
        echo # GitHub репозиторий для проверки обновлений
        echo GITHUB_REPO=!GITHUB_REPO!
    ) > .env
    echo.
    echo Для использования обновлений установите переменную окружения:
    echo   set GITHUB_REPO=!GITHUB_REPO!
    echo.
    echo Или создайте файл .env в корне проекта с содержимым:
    echo   GITHUB_REPO=!GITHUB_REPO!
) else (
    echo Автоматическая проверка обновлений отключена
    echo Вы можете включить позже, указав GITHUB_REPO
)

echo.
REM Настройка ElevenLabs (опционально)
echo.
echo ========================================
echo   НАСТРОЙКА ELEVENLABS (ОПЦИОНАЛЬНО)
echo ========================================
echo.
echo Для реалистичного голоса Jarvis нужен API ключ ElevenLabs
echo Получить ключ: https://elevenlabs.io/app/settings/api-keys
echo.
set /p ELEVENLABS_KEY="Введите API ключ ElevenLabs (или нажмите Enter чтобы пропустить): "

if not "!ELEVENLABS_KEY!"=="" (
    echo Сохранение API ключа...
    echo !ELEVENLABS_KEY! > jarvis\data\elevenlabs_api_key.txt
    echo API ключ сохранен!
    echo.
    echo Популярные голоса для Jarvis:
    echo   Adam (pNInz6obpgDQGcFmaJgB) - глубокий, уверенный [по умолчанию]
    echo   Antoni (ErXwobaYiN019PkySvjV) - четкий, быстрый
    echo   Josh (TxGEqnHWrfWFTfGW9XjX) - молодой, энергичный
    echo   Arnold (VR6AewLTigWG4xSOukaG) - мощный, авторитетный
    echo   Daniel (ThT5KcBeYPX3keUQqHPh) - британский, элегантный
    echo.
    set /p VOICE_ID="Введите voice_id (или нажмите Enter для Adam): "
    if not "!VOICE_ID!"=="" (
        echo !VOICE_ID! > jarvis\data\elevenlabs_voice_id.txt
        echo Voice ID сохранен!
    )
) else (
    echo API ключ не введен. Jarvis будет использовать стандартный голос.
    echo Вы можете добавить ключ позже в файл: jarvis\data\elevenlabs_api_key.txt
)

echo.
echo [ШАГ 6/6] Финальная проверка
echo.

python -c "import speech_recognition; import pyttsx3" >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Проверка установки не пройдена
    pause
    exit /b 1
)

echo Все проверки пройдены успешно!

REM Создание ярлыка запуска
echo.
echo Создание ярлыка запуска...
(
    echo @echo off
    echo setlocal enabledelayedexpansion
    echo cd /d "%INSTALL_DIR%"
    echo.
    echo if not exist .venv\Scripts\python.exe ^(
    echo   echo ERROR: Virtual environment not found!
    echo   echo Run: INSTALLER.bat
    echo   pause
    echo   exit /b 1
    echo ^)
    echo.
    echo set "PATH=%INSTALL_DIR%\.venv\Scripts;%PATH%"
    echo if exist "%INSTALL_DIR%\tools\ffmpeg\bin" ^(
    echo   set "PATH=%INSTALL_DIR%\tools\ffmpeg\bin;%PATH%"
    echo ^)
    echo.
    echo echo Запуск Jarvis...
    echo python -m jarvis.app.main
    echo set EXIT_CODE=!ERRORLEVEL!
    echo.
    echo if !EXIT_CODE! EQU 0 ^(
    echo   echo Jarvis завершил работу успешно
    echo ^) else ^(
    echo   echo Jarvis завершился с ошибкой
    echo ^)
    echo pause
) > RUN_JARVIS.bat

echo.
echo ========================================
echo   УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!
echo ========================================
echo.
echo Jarvis установлен в: %INSTALL_DIR%
echo.
echo Для запуска:
echo   1. Двойной клик на RUN_JARVIS.bat
echo   2. Или запустите: python -m jarvis.app.main
echo.
echo Для проверки системы:
echo   python -m jarvis.app.main --health
echo.
pause
exit /b 0

