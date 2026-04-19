# Clean Tool - Close port 8080 and disable proxy
# Run with: .\clean.ps1
# Or: powershell -ExecutionPolicy Bypass -File clean.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Clean Tool - Close port 8080 and disable proxy" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check port 8080
Write-Host "[1/2] Check port 8080..." -ForegroundColor Yellow
$connections = netstat -ano | Select-String ":8080" | Select-String "LISTENING"
if ($connections) {
    Write-Host "Found process on port 8080, killing..." -ForegroundColor Red
    foreach ($line in $connections) {
        $parts = ($line -split "\s+") | Where-Object { $_ -ne "" }
        $pid = $parts[-1]
        if ($pid -match "^\d+$") {
            Write-Host "  Killing PID: $pid" -ForegroundColor Red
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
    $remaining = netstat -ano | Select-String ":8080" | Select-String "LISTENING"
    if ($remaining) {
        Write-Host "Warning: Port 8080 still in use, please close manually" -ForegroundColor Red
    } else {
        Write-Host "Port 8080 released" -ForegroundColor Green
    }
} else {
    Write-Host "Port 8080 is free" -ForegroundColor Green
}

Write-Host ""

# Step 2: Disable proxy
Write-Host "[2/2] Disable system proxy..." -ForegroundColor Yellow
try {
    Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyEnable -Value 0 -ErrorAction Stop
    Write-Host "Proxy disabled" -ForegroundColor Green
} catch {
    Write-Host "Failed to disable proxy, run as Administrator" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Cleanup complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
