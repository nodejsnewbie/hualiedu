#!/usr/bin/env python3
"""
项目清理脚本
清理缓存文件、日志文件和临时文件
"""

import glob
import os
import shutil
from pathlib import Path


def cleanup_project():
    """清理项目中的临时文件和缓存"""

    # 项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🧹 开始清理项目文件...")

    # 清理Python缓存
    cache_dirs = ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]

    for cache_dir in cache_dirs:
        for path in glob.glob(f"**/{cache_dir}", recursive=True):
            if os.path.exists(path):
                shutil.rmtree(path)
                print(f"✅ 删除缓存目录: {path}")

    # 清理Python编译文件
    for pyc_file in glob.glob("**/*.pyc", recursive=True):
        os.remove(pyc_file)
        print(f"✅ 删除编译文件: {pyc_file}")

    for pyo_file in glob.glob("**/*.pyo", recursive=True):
        os.remove(pyo_file)
        print(f"✅ 删除编译文件: {pyo_file}")

    # 清理日志文件内容（保留文件结构）
    log_files = glob.glob("logs/*.log")
    for log_file in log_files:
        with open(log_file, "w") as f:
            f.write("")
        print(f"✅ 清空日志文件: {log_file}")

    # 清理临时文件
    temp_patterns = ["**/*~", "**/*.tmp", "**/*.temp", "**/.DS_Store"]

    for pattern in temp_patterns:
        for temp_file in glob.glob(pattern, recursive=True):
            os.remove(temp_file)
            print(f"✅ 删除临时文件: {temp_file}")

    print("🎉 项目清理完成!")


if __name__ == "__main__":
    cleanup_project()
