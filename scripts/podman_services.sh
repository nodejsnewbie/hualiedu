#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
SERVICES=("db" "redis")

compose_cmd=""
if podman compose version >/dev/null 2>&1; then
    compose_cmd="podman compose"
elif command -v podman-compose >/dev/null 2>&1; then
    compose_cmd="podman-compose"
fi

if [ -n "$compose_cmd" ]; then
    echo "启动 Podman 服务: ${SERVICES[*]}"
    $compose_cmd -f "$COMPOSE_FILE" up -d "${SERVICES[@]}"
    exit 0
fi

echo "未找到 podman compose，使用 podman pod 启动服务"

load_env_file() {
    local env_file="$1"
    [ -f "$env_file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [ -z "$line" ] && continue
        case "$line" in
            \#*) continue ;;
        esac
        if [[ "$line" == *"="* ]]; then
            key="${line%%=*}"
            value="${line#*=}"
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            export "$key=$value"
        fi
    done < "$env_file"
}

load_env_file ".env"

MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root}"
MYSQL_DATABASE="${MYSQL_DATABASE:-huali_edu}"
MYSQL_USER="${MYSQL_USER:-huali_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-password}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
REDIS_PORT="${REDIS_PORT:-6379}"

POD_NAME="huali-edu-dev"
MYSQL_VOLUME="huali_edu_mysql_data"
REDIS_VOLUME="huali_edu_redis_data"

port_open() {
    python - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
s = socket.socket()
s.settimeout(0.2)
try:
    s.connect(("127.0.0.1", port))
    print("open")
    sys.exit(0)
except Exception:
    sys.exit(1)
finally:
    s.close()
PY
}

mysql_external=false
redis_external=false
if port_open "$MYSQL_PORT" >/dev/null 2>&1; then
    mysql_external=true
fi
if port_open "$REDIS_PORT" >/dev/null 2>&1; then
    redis_external=true
fi

if $mysql_external && $redis_external; then
    echo "检测到 MySQL/Redis 端口已占用，使用外部服务"
    exit 0
fi

podman volume inspect "$MYSQL_VOLUME" >/dev/null 2>&1 || podman volume create "$MYSQL_VOLUME" >/dev/null
podman volume inspect "$REDIS_VOLUME" >/dev/null 2>&1 || podman volume create "$REDIS_VOLUME" >/dev/null

if ! $mysql_external && ! $redis_external; then
    if ! podman pod exists "$POD_NAME"; then
        podman pod create --name "$POD_NAME" -p "$MYSQL_PORT:3306" -p "$REDIS_PORT:6379" >/dev/null
    fi

    if ! podman container exists "${POD_NAME}-db"; then
        podman run -d --name "${POD_NAME}-db" --pod "$POD_NAME" \
            -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
            -e MYSQL_DATABASE="$MYSQL_DATABASE" \
            -e MYSQL_USER="$MYSQL_USER" \
            -e MYSQL_PASSWORD="$MYSQL_PASSWORD" \
            -v "$MYSQL_VOLUME":/var/lib/mysql \
            mysql:8.0 >/dev/null
    else
        podman start "${POD_NAME}-db" >/dev/null
    fi

    if ! podman container exists "${POD_NAME}-redis"; then
        podman run -d --name "${POD_NAME}-redis" --pod "$POD_NAME" \
            -v "$REDIS_VOLUME":/data \
            redis:7-alpine >/dev/null
    else
        podman start "${POD_NAME}-redis" >/dev/null
    fi
else
    if ! $mysql_external; then
        if ! podman container exists "${POD_NAME}-db"; then
            podman run -d --name "${POD_NAME}-db" -p "$MYSQL_PORT:3306" \
                -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
                -e MYSQL_DATABASE="$MYSQL_DATABASE" \
                -e MYSQL_USER="$MYSQL_USER" \
                -e MYSQL_PASSWORD="$MYSQL_PASSWORD" \
                -v "$MYSQL_VOLUME":/var/lib/mysql \
                mysql:8.0 >/dev/null
        else
            podman start "${POD_NAME}-db" >/dev/null
        fi
    else
        echo "MySQL 端口 $MYSQL_PORT 已占用，跳过启动"
    fi

    if ! $redis_external; then
        if ! podman container exists "${POD_NAME}-redis"; then
            podman run -d --name "${POD_NAME}-redis" -p "$REDIS_PORT:6379" \
                -v "$REDIS_VOLUME":/data \
                redis:7-alpine >/dev/null
        else
            podman start "${POD_NAME}-redis" >/dev/null
        fi
    else
        echo "Redis 端口 $REDIS_PORT 已占用，跳过启动"
    fi
fi

echo "Podman 服务已就绪"
