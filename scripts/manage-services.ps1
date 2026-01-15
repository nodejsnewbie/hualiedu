# Manage Podman container services
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("stop", "restart", "logs", "status", "clean")]
    [string]$Action
)

$ErrorActionPreference = "SilentlyContinue"

# Check if podman is available
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Podman not found" -ForegroundColor Red
    Write-Host "Please install Podman Desktop from: https://podman-desktop.io/downloads" -ForegroundColor Yellow
    exit 1
}

switch ($Action) {
    "stop" {
        Write-Host "Stopping container services..." -ForegroundColor Cyan
        podman stop huali-mysql huali-redis 2>$null | Out-Null
        Write-Host "[OK] Container services stopped" -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "Restarting container services..." -ForegroundColor Cyan
        podman restart huali-mysql huali-redis 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Container services restarted" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Failed to restart containers. Please start them first with: make services-up" -ForegroundColor Red
            exit 1
        }
    }
    
    "logs" {
        Write-Host "Viewing container logs (Ctrl+C to exit)..." -ForegroundColor Cyan
        Write-Host "Showing MySQL logs:" -ForegroundColor Yellow
        podman logs -f huali-mysql
    }
    
    "status" {
        Write-Host "Container status:" -ForegroundColor Cyan
        podman ps -a --filter name=huali --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    }
    
    "clean" {
        Write-Host "WARNING: This will delete all containers and data!" -ForegroundColor Red
        $confirmation = Read-Host "Press 'y' to continue or any other key to cancel"
        if ($confirmation -eq 'y') {
            Write-Host "Cleaning containers and data..." -ForegroundColor Yellow
            podman stop huali-mysql huali-redis 2>$null | Out-Null
            podman rm -v huali-mysql huali-redis 2>$null | Out-Null
            Write-Host "[OK] Containers and data cleaned" -ForegroundColor Green
        } else {
            Write-Host "Cancelled" -ForegroundColor Yellow
            exit 0
        }
    }
}
