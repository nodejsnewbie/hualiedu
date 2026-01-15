#!/bin/bash
# Check container service status

ENSURE_RUNNING=false
if [ "$1" = "--ensure" ]; then
    ENSURE_RUNNING=true
fi

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo "Error: Podman not found"
    echo "Please install Podman:"
    echo "  - macOS: brew install podman"
    echo "  - Linux: sudo apt install podman (Ubuntu/Debian) or sudo dnf install podman (Fedora/RHEL)"
    echo "  - Or visit: https://podman.io/getting-started/installation"
    exit 1
fi

# Check MySQL status
MYSQL_RUNNING=$(podman ps --filter name=huali-mysql --filter status=running --format "{{.Names}}" 2>/dev/null)
REDIS_RUNNING=$(podman ps --filter name=huali-redis --filter status=running --format "{{.Names}}" 2>/dev/null)

if [ "$ENSURE_RUNNING" = false ]; then
    # Check status only
    echo "Checking container service status..."
    if [ -n "$MYSQL_RUNNING" ]; then
        echo "[OK] MySQL is running"
    else
        echo "[X] MySQL is not running"
    fi
    if [ -n "$REDIS_RUNNING" ]; then
        echo "[OK] Redis is running"
    else
        echo "[X] Redis is not running"
    fi
else
    # Ensure services are running
    echo "Ensuring container services are running..."
    
    # Start MySQL
    if [ -z "$MYSQL_RUNNING" ]; then
        echo "Starting MySQL container..."
        MYSQL_EXISTS=$(podman ps -a --filter name=huali-mysql --format "{{.Names}}" 2>/dev/null)
        if [ -n "$MYSQL_EXISTS" ]; then
            podman start huali-mysql 2>/dev/null || true
        else
            podman run -d --name huali-mysql \
                -e MYSQL_ROOT_PASSWORD=root_password \
                -e MYSQL_DATABASE=huali_edu \
                -e MYSQL_USER=huali_user \
                -e MYSQL_PASSWORD=HualiUser_2026 \
                -p 3306:3306 \
                docker.io/library/mysql:8.0 \
                --default-authentication-plugin=mysql_native_password \
                --character-set-server=utf8mb4 \
                --collation-server=utf8mb4_unicode_ci 2>/dev/null || true
        fi
        echo "Waiting for MySQL to start..."
        sleep 8
    fi
    
    # Start Redis
    if [ -z "$REDIS_RUNNING" ]; then
        echo "Starting Redis container..."
        REDIS_EXISTS=$(podman ps -a --filter name=huali-redis --format "{{.Names}}" 2>/dev/null)
        if [ -n "$REDIS_EXISTS" ]; then
            podman start huali-redis 2>/dev/null || true
        else
            podman run -d --name huali-redis \
                -p 6379:6379 \
                docker.io/library/redis:7-alpine \
                redis-server --appendonly yes 2>/dev/null || true
        fi
        sleep 2
    fi
    
    echo "[OK] Container services are ready"
fi
