#!/bin/bash
# 在 conda py313 环境下启动开发服务器的辅助脚本

set -e

echo "在 conda py313 环境下启动开发服务器..."

# 默认端口 8000，可以通过参数指定
PORT=${1:-8000}

echo "服务器将在端口 $PORT 上运行"
conda run -n py313 python manage.py runserver $PORT
