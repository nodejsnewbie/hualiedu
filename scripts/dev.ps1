param(
    [Parameter(Position = 0)]
    [ValidateSet("runserver", "migrate", "services", "down")]
    [string]$Target = "runserver"
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*#") { return }
        if ($_ -match "^\s*$") { return }
        $pair = $_ -split "=", 2
        if ($pair.Length -eq 2) {
            $name = $pair[0].Trim()
            $value = $pair[1].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

function Ensure-Podman {
    $machine = $env:PODMAN_MACHINE
    if (-not $machine) { $machine = "huali-machine" }
    podman machine start $machine | Out-Null

    $network = $env:PODMAN_NETWORK
    if (-not $network) { $network = "huali-net" }
    podman network exists $network
    if ($LASTEXITCODE -ne 0) { podman network create $network | Out-Null }

    $mysqlContainer = $env:MYSQL_CONTAINER
    if (-not $mysqlContainer) { $mysqlContainer = "huali-mysql" }
    $mysqlVolume = $env:MYSQL_VOLUME
    if (-not $mysqlVolume) { $mysqlVolume = "huali-mysql-data" }
    $mysqlImage = $env:MYSQL_IMAGE
    if (-not $mysqlImage) { $mysqlImage = "docker.io/library/mysql:8.0" }
    $mysqlPort = $env:MYSQL_PORT
    if (-not $mysqlPort) { $mysqlPort = "3307" }
    $mysqlDatabase = $env:MYSQL_DATABASE
    if (-not $mysqlDatabase) { $mysqlDatabase = "huali_edu" }
    $mysqlUser = $env:MYSQL_USER
    if (-not $mysqlUser) { $mysqlUser = "huali_user" }
    $mysqlPassword = $env:MYSQL_PASSWORD
    if (-not $mysqlPassword) { $mysqlPassword = "HualiUser_2026" }
    $mysqlRootPassword = $env:MYSQL_ROOT_PASSWORD
    if (-not $mysqlRootPassword) { $mysqlRootPassword = "HualiRoot_2026!" }

    podman volume exists $mysqlVolume
    if ($LASTEXITCODE -ne 0) { podman volume create $mysqlVolume | Out-Null }

    podman container exists $mysqlContainer
    if ($LASTEXITCODE -ne 0) {
        podman run -d --name $mysqlContainer --network $network `
            -p "$mysqlPort:3306" `
            -e "MYSQL_ROOT_PASSWORD=$mysqlRootPassword" `
            -e "MYSQL_DATABASE=$mysqlDatabase" `
            -e "MYSQL_USER=$mysqlUser" `
            -e "MYSQL_PASSWORD=$mysqlPassword" `
            -v "$mysqlVolume:/var/lib/mysql" `
            $mysqlImage | Out-Null
    } else {
        podman start $mysqlContainer | Out-Null
    }

    $redisContainer = $env:REDIS_CONTAINER
    if (-not $redisContainer) { $redisContainer = "huali-redis" }
    $redisImage = $env:REDIS_IMAGE
    if (-not $redisImage) { $redisImage = "docker.io/library/redis:7" }
    $redisPort = $env:REDIS_PORT
    if (-not $redisPort) { $redisPort = "6379" }

    podman container exists $redisContainer
    if ($LASTEXITCODE -ne 0) {
        podman run -d --name $redisContainer --network $network `
            -p "$redisPort:6379" `
            $redisImage | Out-Null
    } else {
        podman start $redisContainer | Out-Null
    }
}

switch ($Target) {
    "services" { Ensure-Podman }
    "migrate" {
        Ensure-Podman
        uv run python manage.py migrate
    }
    "runserver" {
        Ensure-Podman
        uv run python manage.py runserver
    }
    "down" {
        $mysqlContainer = $env:MYSQL_CONTAINER
        if (-not $mysqlContainer) { $mysqlContainer = "huali-mysql" }
        $redisContainer = $env:REDIS_CONTAINER
        if (-not $redisContainer) { $redisContainer = "huali-redis" }
        podman stop $mysqlContainer $redisContainer | Out-Null
    }
}
