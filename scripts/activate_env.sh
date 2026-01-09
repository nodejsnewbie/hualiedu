#!/bin/bash
# 激活 conda py313 环境的辅助脚本

echo "激活 conda py313 环境..."
eval "$(conda shell.bash hook)"
conda activate py313

if [ $? -eq 0 ]; then
    echo "✓ 环境激活成功"
    echo "当前 Python 版本: $(python --version)"
    echo "当前环境: $CONDA_DEFAULT_ENV"
else
    echo "✗ 环境激活失败"
    exit 1
fi
