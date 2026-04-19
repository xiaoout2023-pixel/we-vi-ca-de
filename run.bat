@echo off
chcp 65001 >nul

echo Start WeChat Video Capture Tool...
echo.
cd /d "%~dp0"

echo Check port 8080...
netstat -ano | findstr ":8080" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo WARNING: Port 8080 is in use!
    echo Please run clean.bat first, or close the process manually
    echo.
    choice /C YN /M "Run clean.bat to cleanup?"
    if %errorlevel% equ 1 (
        call clean.bat
        echo.
        echo Cleanup done, starting...
    ) else (
        echo.
        echo Cancelled, please cleanup manually
        pause
        exit /b 1
    )
) else (
    echo Port 8080 is available
)

echo.
python -m src.main

pause
