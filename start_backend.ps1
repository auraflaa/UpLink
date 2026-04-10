<#
.SYNOPSIS
Bootstraps and starts the entire UpLink Backend Services cluster.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "Backend"

if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] Could not find the Backend directory at $BackendDir" -ForegroundColor Red
    Exit 1
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Bootstrapping UpLink Backend Cluster..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Push-Location $BackendDir

# 1. Automated Python Environment Bootstrapping
$VenvDir = Join-Path $BackendDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "[*] Virtual environment not found. Creating one now..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[*] Verifying dependencies from requirements.txt..." -ForegroundColor Yellow
$ActivateScript = Join-Path $VenvDir "Scripts\activate.ps1"
if (Test-Path $ActivateScript) {
    # Run pip install in the current shell before spinning up the background tasks
    & powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '$ActivateScript'; pip install -r requirements.txt; exit `$LASTEXITCODE }"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Warning: Dependency installation may have failed." -ForegroundColor Red
    } else {
        Write-Host "[OK] Dependencies are fully synced." -ForegroundColor Green
    }
} else {
    Write-Host "[!] Warning: Could not find venv activate script at $ActivateScript" -ForegroundColor Red
}

# 2. Start Vector Database (Qdrant)
$QdrantDir = Join-Path $BackendDir "Qdrant DB"
if (Test-Path $QdrantDir) {
    Write-Host "[*] Spinning up Qdrant Vector DB (Docker)..." -ForegroundColor Yellow
    Push-Location $QdrantDir
    docker-compose up -d
    Pop-Location
} else {
    Write-Host "[!] Skipping Qdrant DB: Directory not found." -ForegroundColor DarkGray
}

Write-Host "[*] Giving Qdrant a moment to boot..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 3. Helper function to launch Python services in new windows
function Start-Microservice {
    param(
        [string]$ServiceName,
        [string]$ScriptPath,
        [string]$Color = "Cyan"
    )

    $FullPath = Join-Path $BackendDir $ScriptPath
    
    if (-not (Test-Path $FullPath)) {
        Write-Host "[!] Skipping $ServiceName - Script not found at $FullPath" -ForegroundColor DarkGray
        return
    }

    Write-Host "[*] Starting $ServiceName..." -ForegroundColor $Color
    
    $Args = @(
        "-NoExit",
        "-Command",
        "& {",
        "  $host.UI.RawUI.WindowTitle = '$ServiceName'; ",
        "  Set-Location -Path '$BackendDir'; ",
        "  if (Test-Path 'venv\Scripts\activate.ps1') { . .\venv\Scripts\activate.ps1 } else { Write-Host 'WARNING: VENV NOT FOUND' -ForegroundColor Red }; ",
        "  Write-Host '--- $ServiceName ---' -ForegroundColor $Color; ",
        "  python '$ScriptPath'",
        "}"
    )

    Start-Process powershell -ArgumentList $Args
}

# 4. Launch Services
Start-Microservice -ServiceName "Embedding Service [Port 6377]" -ScriptPath "Embedding Service\server.py" -Color Magenta
Start-Microservice -ServiceName "Document Parser [Port 8004]" -ScriptPath "Document Parser\server.py" -Color Green
Start-Microservice -ServiceName "Event Handler [Port 8003]" -ScriptPath "Event Handler\event.py" -Color Yellow
Start-Microservice -ServiceName "RAG Pipeline (Brain) [Port 6399]" -ScriptPath "RAG Pipeline\server.py" -Color Cyan

Pop-Location

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " All services disparched successfully." -ForegroundColor Cyan
Write-Host " Keep the terminal windows open to monitor their logs." -ForegroundColor Green
Write-Host " To shut everything down, just close all the Python windows." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
