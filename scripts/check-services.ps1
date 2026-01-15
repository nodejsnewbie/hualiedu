# Check container service status
param(
    [switch]$EnsureRunning
)

$ErrorActionPreference = "SilentlyContinue"

# Check if podman is available
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Podman not found" -ForegroundColor Red
    Write-Host "Please install Podman Desktop from: https://podman-desktop.io/downloads" -ForegroundColor Yellow
    exit 1
}

# Check if podman machine is running (Windows/macOS only)
if ($IsWindows -or $IsMacOS) {
    $machineStatus = podman machine list --format "{{.Running}}" 2>$null
    if ($machineStatus -notcontains "true") {
        Write-Host "Error: Podman machine is not running" -ForegroundColor Red
        Write-Host "Please start Podman machine with: podman machine start" -ForegroundColor Yellow
        exit 1
    }
}

# Check MySQL status
$mysqlRunning = podman ps --filter name=huali-mysql --filter status=running --format "{{.Names}}" 2>$null
$redisRunning = podman ps --filter name=huali-redis --filter status=running --format "{{.Names}}" 2>$null

if (-not $EnsureRunning) {
    # Check status only
    Write-Host "Checking container service status..." -ForegroundColor Cyan
    if ($mysqlRunning) {
        Write-Host "[OK] MySQL is running" -ForegroundColor Green
    } else {
        Write-Host "[X] MySQL is not running" -ForegroundColor Yellow
    }
    if ($redisRunning) {
        Write-Host "[OK] Redis is running" -ForegroundColor Green
    } else {
        Write-Host "[X] Redis is not running" -ForegroundColor Yellow
    }
} else {
    # Ensure services are running
    Write-Host "Ensuring container services are running..." -ForegroundColor Cyan
    
    # Start MySQL
    if (-not $mysqlRunning) {
        Write-Host "Starting MySQL container..." -ForegroundColor Yellow
        $mysqlExists = podman ps -a --filter name=huali-mysql --format "{{.Names}}" 2>$null
        if ($mysqlExists) {
            podman start huali-mysql 2>$null | Out-Null
        } else {
            podman run -d --name huali-mysql `
                -e MYSQL_ROOT_PASSWORD=root_password `
                -e MYSQL_DATABASE=huali_edu `
                -e MYSQL_USER=huali_user `
                -e MYSQL_PASSWORD=HualiUser_2026 `
                -p 3306:3306 `
                docker.io/library/mysql:8.0 `
                --default-authentication-plugin=mysql_native_password `
                --character-set-server=utf8mb4 `
                --collation-server=utf8mb4_unicode_ci 2>$null | Out-Null
        }
        Write-Host "Waiting for MySQL to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 8
    }
    
    # Start Redis
    if (-not $redisRunning) {
        Write-Host "Starting Redis container..." -ForegroundColor Yellow
        $redisExists = podman ps -a --filter name=huali-redis --format "{{.Names}}" 2>$null
        if ($redisExists) {
            podman start huali-redis 2>$null | Out-Null
        } else {
            podman run -d --name huali-redis `
                -p 6379:6379 `
                docker.io/library/redis:7-alpine `
                redis-server --appendonly yes 2>$null | Out-Null
        }
        Start-Sleep -Seconds 2
    }
    
    Write-Host "[OK] Container services are ready" -ForegroundColor Green
}

