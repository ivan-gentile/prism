# PRISM Server Auto-Start Script
# Mantiene il server PRISM sempre in esecuzione

param(
    [switch]$AsService,
    [switch]$Background
)

$ProjectPath = "C:\Users\ITBlangeGi\prism"
$PythonExe = "$ProjectPath\venv\Scripts\python.exe"
$AppScript = "$ProjectPath\prism_webapp.py"

Write-Host "🚀 PRISM Auto-Start Script" -ForegroundColor Green
Write-Host "📁 Project Path: $ProjectPath" -ForegroundColor Cyan
Write-Host "🐍 Python: $PythonExe" -ForegroundColor Cyan

function Start-PRISMServer {
    Set-Location $ProjectPath
    
    Write-Host "🔄 Starting PRISM Web Server..." -ForegroundColor Yellow
    
    while ($true) {
        try {
            Write-Host "$(Get-Date): Starting server..." -ForegroundColor Green
            
            # Avvia il server
            & $PythonExe $AppScript
            
            # Se arriviamo qui, il server si è fermato
            Write-Host "$(Get-Date): Server stopped. Restarting in 5 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            
        } catch {
            Write-Host "$(Get-Date): Error occurred: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "$(Get-Date): Restarting in 10 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
}

function Test-ServerHealth {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 10 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if ($Background) {
    Write-Host "🔧 Starting in background mode..." -ForegroundColor Magenta
    Start-Job -ScriptBlock ${function:Start-PRISMServer} -Name "PRISM-Server"
    Write-Host "✅ PRISM Server job started. Check with: Get-Job" -ForegroundColor Green
} else {
    Start-PRISMServer
}
