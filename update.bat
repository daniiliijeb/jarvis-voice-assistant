@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   ОБНОВЛЕНИЕ JARVIS
echo ========================================
echo.

if not exist .venv\Scripts\python.exe (
    echo ERROR: Virtual environment not found!
    echo Run: INSTALLER.bat first
    echo.
    pause
    exit /b 1
)

REM Безопасное добавление в PATH
set "VENV_PATH=%CD%\.venv\Scripts"
set "PATH=%VENV_PATH%;%PATH%"

echo Проверка обновлений...
echo.

python -m jarvis.app.main --check-update
set CHECK_CODE=!ERRORLEVEL!

if !CHECK_CODE! EQU 0 (
    echo.
    echo Найдено обновление! Установить?
    echo.
    set /p INSTALL="Введите 'y' для установки или 'n' для отмены: "
    
    if /i "!INSTALL!"=="y" (
        echo.
        echo Установка обновления...
        echo.
        python -m jarvis.app.main --update
        set UPDATE_CODE=!ERRORLEVEL!
        
        if !UPDATE_CODE! EQU 0 (
            echo.
            echo ========================================
            echo   ОБНОВЛЕНИЕ УСТАНОВЛЕНО УСПЕШНО!
            echo ========================================
            echo.
            echo Перезапустите Jarvis для применения изменений.
        ) else (
            echo.
            echo ========================================
            echo   ОШИБКА ПРИ УСТАНОВКЕ ОБНОВЛЕНИЯ
            echo ========================================
        )
    ) else (
        echo Обновление отменено.
    )
) else (
    echo Обновлений не найдено или произошла ошибка.
)

echo.
pause
exit /b 0


