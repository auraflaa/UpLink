<#
.SYNOPSIS
Stops all running UpLink backend services.
#>

$Ports = @(8000, 8002, 8003, 8004, 6399, 6377)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Stopping UpLink Backend Cluster..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

foreach ($Port in $Ports) {
    $connections = netstat -ano | Select-String ":$Port\s" | Where-Object { $_ -match "LISTENING" }
    foreach ($conn in $connections) {
        $parts = $conn -split '\s+' | Where-Object { $_ -ne '' }
        $pid = $parts[-1]
        if ($pid -match '^\d+$') {
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "[OK] Killed process $pid on port $Port" -ForegroundColor Green
            } catch {
                Write-Host "[!] Could not kill PID $pid on port $Port`: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    if (-not $connections) {
        Write-Host "[--] Nothing listening on port $Port" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "[OK] All UpLink backend services stopped." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
