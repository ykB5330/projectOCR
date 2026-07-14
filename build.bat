@echo off
setlocal enabledelayedexpansion
title OCR Tool - Build

echo.
echo  ============================================
echo    OCR Text Recognition Tool - Build Script
echo  ============================================
echo.

echo  [1/3] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo         Done.

echo  [2/3] Installing PyInstaller...
pip install pyinstaller -q
if errorlevel 1 (
    echo  [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)
echo         Done.

echo  [3/3] Building (this may take 5-15 minutes)...
pyinstaller app.spec --noconfirm
if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed, see above for details
    pause
    exit /b 1
)

echo.
echo  ============================================
echo    Build Complete!
echo.
echo    Output: dist\OCR_text_recognition\
echo    Launch: OCR_text_recognition.exe
echo  ============================================
echo.
echo  Copy the entire "dist\OCR_text_recognition" folder
echo  to any Windows PC. No Python required.
echo.

start "" "dist\OCR_text_recognition"
pause
