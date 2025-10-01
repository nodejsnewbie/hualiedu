#!/usr/bin/env python3
"""
测试命令包装器 - 确保在py313环境中执行
"""

import os
import sys

from run_in_env import run_in_py313


def main():
    """测试命令包装器"""
    if len(sys.argv) < 2:
        print("用法: python test_py313.py <test_file_or_module>")
        print("示例:")
        print("  python test_py313.py test_semester_manager_simple.py")
        print("  python test_py313.py grading.tests.test_semester_manager")
        print("  python test_py313.py manage.py test")
        return 1

    test_target = sys.argv[1]

    # 判断是文件还是Django测试模块
    if test_target.endswith(".py"):
        # Python文件
        test_args = ["python", test_target] + sys.argv[2:]
    elif test_target == "manage.py":
        # Django测试命令
        test_args = ["python", "manage.py"] + sys.argv[2:]
    else:
        # Django测试模块
        test_args = ["python", "manage.py", "test", test_target] + sys.argv[2:]

    # 在py313环境中执行
    return run_in_py313(test_args)


if __name__ == "__main__":
    sys.exit(main())
