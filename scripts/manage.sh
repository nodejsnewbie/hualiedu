#!/bin/bash
# 在 conda py313 环境下运行 Django 管理命令的辅助脚本

set -e

if [ $# -eq 0 ]; then
    echo "用法: ./scripts/manage.sh <django命令> [参数...]"
    echo ""
    echo "示例:"
    echo "  ./scripts/manage.sh makemigrations"
    echo "  ./scripts/manage.sh migrate"
    echo "  ./scripts/manage.sh createsuperuser"
    echo "  ./scripts/manage.sh shell"
    exit 1
fi

echo "在 conda py313 环境下运行: python manage.py $@"
conda run -n py313 python manage.py "$@"
