@echo off
chcp 65001 >nul
echo ========================================
echo Загрузка проекта в GitHub
echo ========================================
echo.

REM Проверка наличия git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Git не установлен!
    echo Установите Git с https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/6] Проверка статуса репозитория...
git status >nul 2>&1
set GIT_STATUS=%errorlevel%
if %GIT_STATUS% neq 0 (
    echo [2/6] Инициализация Git репозитория...
    git init
    set GIT_INIT=%errorlevel%
    if %GIT_INIT% neq 0 (
        echo [ОШИБКА] Не удалось инициализировать репозиторий
        pause
        exit /b 1
    )
    echo [OK] Репозиторий успешно инициализирован
) else (
    echo [2/6] Репозиторий уже инициализирован
)

echo [3/6] Проверка remote origin...
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [3/6] Добавление remote origin...
    git remote add origin https://github.com/daniiliijeb/jarvis-voice-assistant.git
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось добавить remote
        pause
        exit /b 1
    )
    echo Remote origin добавлен: https://github.com/daniiliijeb/jarvis-voice-assistant.git
) else (
    echo [3/6] Remote origin уже настроен
    git remote get-url origin
)

echo [4/6] Добавление всех файлов...
git add .
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось добавить файлы
    pause
    exit /b 1
)

echo [5/6] Создание коммита...
git commit -m "Initial commit: Jarvis Voice Assistant"
if %errorlevel% neq 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Возможно, нечего коммитить или коммит уже существует
)

echo [6/6] Переименование ветки в main (если нужно)...
git branch -M main 2>nul

echo.
echo ========================================
echo Отправка на GitHub...
echo ========================================
echo.
echo ВНИМАНИЕ: Вам потребуется авторизация!
echo Если используете Personal Access Token:
echo 1. Получите токен: GitHub → Settings → Developer settings → Personal access tokens
echo 2. При запросе пароля введите токен
echo.
pause

git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось отправить на GitHub
    echo.
    echo Возможные причины:
    echo 1. Неправильная авторизация (используйте Personal Access Token)
    echo 2. Репозиторий не существует или нет доступа
    echo 3. Интернет-соединение
    echo.
    echo Попробуйте выполнить вручную:
    echo   git push -u origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ УСПЕШНО! Проект загружен на GitHub
echo ========================================
echo.
echo Откройте: https://github.com/daniiliijeb/jarvis-voice-assistant
echo.
pause

