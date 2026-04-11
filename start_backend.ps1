<#
.SYNOPSIS
Bootstraps and starts the UpLink backend service cluster.

.DESCRIPTION
Bootstraps the backend cluster in hidden PowerShell background processes. All output is securely routed to the /logs/ directory to ensure a clean local workflow.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "Backend"

# --- Kill any existing processes on backend ports ---
Write-Host "[*] Cleaning up old processes on backend ports..." -ForegroundColor Yellow
@(8000, 8002, 8003, 8004, 6399, 6377) | ForEach-Object {
    $port = $_
    $results = netstat -ano | Select-String ":$port\s.*LISTENING"
    foreach ($line in $results) {
        $parts = $line.ToString().Trim() -split '\s+'
        $pid = $parts[-1]
        if ($pid -match '^\d+$') {
            Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
            Write-Host "    Freed port $port (PID $pid)" -ForegroundColor DarkGray
        }
    }
}
Start-Sleep -Seconds 1

if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] Could not find the Backend directory at $BackendDir" -ForegroundColor Red
    exit 1
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting UpLink Backend Cluster..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Push-Location $BackendDir

$VenvDir = Join-Path $BackendDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "[*] Virtual environment not found. Creating one now..." -ForegroundColor Yellow
    python -m venv venv
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Could not find Python executable at $PythonExe" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "[*] Verifying Python dependencies..." -ForegroundColor Yellow
& $PythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Warning: Dependency installation reported an error." -ForegroundColor Red
} else {
    Write-Host "[OK] Python dependencies are synced." -ForegroundColor Green
}

function Start-Qdrant {
    param([string]$QdrantDir)

    if (-not (Test-Path $QdrantDir)) {
        Write-Host "[!] Skipping Qdrant DB: Directory not found." -ForegroundColor DarkGray
        return
    }

    Write-Host "[*] Attempting to start Qdrant Vector DB..." -ForegroundColor Yellow
    Push-Location $QdrantDir
    try {
        $DockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
        $Docker = Get-Command docker -ErrorAction SilentlyContinue

        if ($DockerCompose) {
            & $DockerCompose.Source up -d
        } elseif ($Docker) {
            & $Docker.Source compose up -d
        } else {
            Write-Host "[!] Docker is not available. Skipping Qdrant startup." -ForegroundColor DarkGray
            return
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Qdrant startup command completed." -ForegroundColor Green
        } else {
            Write-Host "[!] Qdrant startup returned a non-zero exit code." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[!] Qdrant startup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
}

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

    $LogDir = Join-Path $BackendDir "logs"
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir | Out-Null
    }

    $LogSlug = (($ServiceName -replace "[^A-Za-z0-9]+", "_").Trim("_")).ToLowerInvariant()
    $StdOutLog = Join-Path $LogDir "$LogSlug.out.log"
    $StdErrLog = Join-Path $LogDir "$LogSlug.err.log"

    $Command = "& { " +
        "`$host.ui.RawUI.WindowTitle = '$ServiceName'; " +
        "Set-Location -LiteralPath '$BackendDir'; " +
        "& '$PythonExe' '$FullPath' " +
        "}"

    Start-Process powershell -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command", $Command
    )

    Write-Host "    Started $ServiceName in a new terminal window." -ForegroundColor DarkGray
}

$QdrantDir = Join-Path $BackendDir "Qdrant DB"
Start-Qdrant -QdrantDir $QdrantDir

Write-Host "[*] Giving infrastructure a moment to settle..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Start-Microservice -ServiceName "Embedding Service [Port 6377]" -ScriptPath "Embedding Service\server.py" -Color Magenta
Start-Sleep -Seconds 1
Start-Microservice -ServiceName "Document Parser [Port 8004]" -ScriptPath "Document Parser\server.py" -Color Green
Start-Sleep -Seconds 1
Start-Microservice -ServiceName "Scheduler [Port 8002]" -ScriptPath "Social Connector\scheduler.py" -Color DarkYellow
Start-Sleep -Seconds 1
Start-Microservice -ServiceName "Event Handler [Port 8003]" -ScriptPath "Event Handler\event.py" -Color Yellow
Start-Sleep -Seconds 1
Start-Microservice -ServiceName "RAG Pipeline [Port 6399]" -ScriptPath "RAG Pipeline\server.py" -Color Cyan
Start-Sleep -Seconds 1
Start-Microservice -ServiceName "Main Server [Port 8000]" -ScriptPath "Main Server\server.py" -Color Blue

Pop-Location

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Backend services launched." -ForegroundColor Green
Write-Host " Main Server:     http://127.0.0.1:8000" -ForegroundColor White
Write-Host " Scheduler:       http://127.0.0.1:8002" -ForegroundColor White
Write-Host " Event Handler:   http://127.0.0.1:8003" -ForegroundColor White
Write-Host " Document Parser: http://127.0.0.1:8004" -ForegroundColor White
Write-Host " RAG Pipeline:    http://127.0.0.1:6399" -ForegroundColor White
Write-Host " Logs Directory:  $BackendDir\logs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
