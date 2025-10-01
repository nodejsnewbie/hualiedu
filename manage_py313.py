#!/usr/bin/env python3
"""
Django管理命令包装器 - 确保在py313环境中执行
"""

import os
import sys

from run_in_env import run_in_py313


def main():
    """Django manage.py命令包装器"""
    # 构建manage.py命令
    manage_args = ["python", "manage.py"] + sys.argv[1:]

    # 在py313环境中执行
    return run_in_py313(manage_args)


if __name__ == "__main__":
    sys.exit(main())
