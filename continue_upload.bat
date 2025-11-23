@echo off
chcp 65001 >nul
echo ========================================
echo Продолжение загрузки в GitHub
echo ========================================
echo.

echo [Шаг 1] Проверка remote origin...
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo Добавление remote origin...
    git remote add origin https://github.com/daniiliijeb/jarvis-voice-assistant.git
    echo Remote origin добавлен
) else (
    echo Remote origin уже настроен
    git remote get-url origin
)

echo.
echo [Шаг 2] Добавление всех файлов...
git add .
echo Файлы добавлены

echo.
echo [Шаг 3] Создание коммита...
git commit -m "Initial commit: Jarvis Voice Assistant"
if %errorlevel% neq 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Возможно, нечего коммитить
)

echo.
echo [Шаг 4] Переименование ветки в main...
git branch -M main 2>nul

echo.
echo ========================================
echo Отправка на GitHub...
echo ========================================
echo.
echo ВНИМАНИЕ: Вам потребуется авторизация!
echo.
echo Если используете Personal Access Token:
echo 1. Username: ваш логин GitHub
echo 2. Password: вставьте Personal Access Token (НЕ пароль!)
echo.
echo Получить токен: GitHub → Settings → Developer settings → Personal access tokens
echo.
pause

git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось отправить на GitHub
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

