@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Update to GitHub

color 0B
cls

echo.
echo ================================================================
echo   UPDATING PROJECT TO GITHUB
echo ================================================================
echo.

cd /d "%~dp0"

REM Check git
where git >nul 2>&1
if errorlevel 1 (
    color 0C
    echo   [X] Git not installed!
    echo.
    echo   Install Git from https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

REM Check repository
git status >nul 2>&1
if errorlevel 1 (
    color 0C
    echo   [X] This is not a Git repository!
    echo.
    echo   Initialize repository first:
    echo   git init
    echo   git remote add origin https://github.com/daniiliijeb/jarvis-voice-assistant.git
    echo.
    pause
    exit /b 1
)

echo   [~] Checking status...
echo.

git status --short
echo.

echo   ================================================================
echo.
set /p CONFIRM="Add all changes and commit? (y/n): "

if /i not "!CONFIRM!"=="y" (
    echo   Cancelled
    pause
    exit /b 0
)

echo.
echo   [~] Adding all changes...
git add .
if errorlevel 1 (
    color 0C
    echo   [X] ERROR: Failed to add files
    pause
    exit /b 1
)
echo   [OK] Files added

echo.
echo   Enter commit message:
echo   (or press Enter for default message)
set /p COMMIT_MSG="Commit message: "

if "!COMMIT_MSG!"=="" (
    set "COMMIT_MSG=Update: Fixed TTS error and improved voice recognition filtering"
)

echo.
echo   [~] Creating commit...
git commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    color 0C
    echo   [X] ERROR: Failed to create commit
    echo   Maybe nothing to commit?
    pause
    exit /b 1
)
echo   [OK] Commit created

echo.
echo   [~] Pushing to GitHub...
echo   (You may need to enter GitHub credentials)
echo.

git push
if errorlevel 1 (
    color 0C
    echo   [X] ERROR: Failed to push to GitHub
    echo.
    echo   Possible reasons:
    echo   1. Authentication failed (use Personal Access Token)
    echo   2. No internet connection
    echo   3. Repository doesn't exist or no access
    echo.
    echo   Try manually: git push
    pause
    exit /b 1
)

color 0A
echo.
echo   ================================================================
echo   SUCCESS! Project updated on GitHub
echo   ================================================================
echo.
echo   View at: https://github.com/daniiliijeb/jarvis-voice-assistant
echo.
pause
exit /b 0

