# Script per installare PRISM come servizio Windows
# Richiede NSSM (Non-Sucking Service Manager)

param(
    [switch]$Install,
    [switch]$Remove,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$ServiceName = "PRISM-AD-Server"
$ProjectPath = "C:\Users\ITBlangeGi\prism"
$PythonExe = "$ProjectPath\venv\Scripts\python.exe"
$AppScript = "$ProjectPath\prism_webapp.py"
$NSSMPath = "$ProjectPath\nssm.exe"

Write-Host "🔧 PRISM Service Manager" -ForegroundColor Green

function Download-NSSM {
    if (-not (Test-Path $NSSMPath)) {
        Write-Host "📥 Downloading NSSM..." -ForegroundColor Yellow
        try {
            $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
            $tempZip = "$env:TEMP\nssm.zip"
            
            Invoke-WebRequest -Uri $nssmUrl -OutFile $tempZip
            Expand-Archive -Path $tempZip -DestinationPath $env:TEMP -Force
            
            # Copia nssm.exe appropriato (64-bit)
            $nssmExe = "$env:TEMP\nssm-2.24\win64\nssm.exe"
            Copy-Item $nssmExe $NSSMPath
            
            Remove-Item $tempZip -Force
            Remove-Item "$env:TEMP\nssm-2.24" -Recurse -Force
            
            Write-Host "✅ NSSM downloaded successfully" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to download NSSM: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
}

if ($Install) {
    Download-NSSM
    
    Write-Host "🔧 Installing PRISM as Windows Service..." -ForegroundColor Yellow
    
    # Installa il servizio
    & $NSSMPath install $ServiceName $PythonExe $AppScript
    
    # Configura il servizio
    & $NSSMPath set $ServiceName AppDirectory $ProjectPath
    & $NSSMPath set $ServiceName DisplayName "PRISM-AD Alzheimer Risk Analysis Server"
    & $NSSMPath set $ServiceName Description "Web server per l'analisi del rischio Alzheimer con sistema PRISM-AD"
    & $NSSMPath set $ServiceName Start SERVICE_AUTO_START
    & $NSSMPath set $ServiceName AppRestartDelay 5000
    & $NSSMPath set $ServiceName AppStdout "$ProjectPath\prism_service.log"
    & $NSSMPath set $ServiceName AppStderr "$ProjectPath\prism_service_error.log"
    
    Write-Host "✅ Service installed successfully!" -ForegroundColor Green
    Write-Host "🔄 Starting service..." -ForegroundColor Yellow
    
    Start-Service -Name $ServiceName
    Write-Host "✅ PRISM service is now running!" -ForegroundColor Green
}

if ($Remove) {
    Write-Host "🗑️  Removing PRISM service..." -ForegroundColor Yellow
    
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        & $NSSMPath remove $ServiceName confirm
        Write-Host "✅ Service removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error removing service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Start) {
    Write-Host "▶️  Starting PRISM service..." -ForegroundColor Yellow
    Start-Service -Name $ServiceName
    Write-Host "✅ Service started!" -ForegroundColor Green
}

if ($Stop) {
    Write-Host "⏹️  Stopping PRISM service..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force
    Write-Host "✅ Service stopped!" -ForegroundColor Green
}

if ($Status) {
    Write-Host "📊 PRISM Service Status:" -ForegroundColor Cyan
    Get-Service -Name $ServiceName -ErrorAction SilentlyContinue | Format-Table -AutoSize
    
    Write-Host "🌐 Testing server connection..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Server is responding (Status: $($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "❌ Server is not responding" -ForegroundColor Red
    }
}

# Default: mostra help
if (-not ($Install -or $Remove -or $Start -or $Stop -or $Status)) {
    Write-Host @"
Uso:
  .\install_prism_service.ps1 -Install    # Installa e avvia il servizio
  .\install_prism_service.ps1 -Remove     # Rimuove il servizio
  .\install_prism_service.ps1 -Start      # Avvia il servizio
  .\install_prism_service.ps1 -Stop       # Ferma il servizio
  .\install_prism_service.ps1 -Status     # Mostra stato del servizio

Dopo l'installazione, PRISM sarà sempre in esecuzione come servizio Windows.
"@ -ForegroundColor Cyan
}
