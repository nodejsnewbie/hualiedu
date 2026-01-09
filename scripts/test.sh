#!/bin/bash
# 在 conda py313 环境下运行测试的辅助脚本

set -e

echo "在 conda py313 环境下运行测试..."

# 如果没有参数，运行所有测试
if [ $# -eq 0 ]; then
    echo "运行所有测试..."
    conda run -n py313 python manage.py test --verbosity=2
else
    # 运行指定的测试
    echo "运行测试: $@"
    conda run -n py313 python manage.py test "$@" --verbosity=2
fi
