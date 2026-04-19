@echo off
chcp 65001 >nul

echo ============================================
echo Clean Tool - Close port 8080 and disable proxy
echo ============================================
echo.

echo [1/2] Check port 8080...
netstat -ano | findstr ":8080" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found process on port 8080, killing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
        echo   Killing PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":8080" | findstr "LISTENING" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Warning: Port 8080 still in use, please close manually
    ) else (
        echo Port 8080 released
    )
) else (
    echo Port 8080 is free
)

echo.
echo [2/2] Disable system proxy...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f >nul 2>&1
echo Proxy disabled

echo.
echo ============================================
echo Cleanup complete!
echo ============================================
