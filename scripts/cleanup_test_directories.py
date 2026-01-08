#!/usr/bin/env python3
"""
清理 Hypothesis 测试生成的随机目录

这些目录是由 Hypothesis 属性测试自动生成的，用于测试路径处理功能。
现在已经配置 Hypothesis 使用系统临时目录，这些目录不应该再被创建。

使用方法：
    python scripts/cleanup_test_directories.py
    或
    uv run python scripts/cleanup_test_directories.py
"""

import os
import re
import shutil
import sys
from pathlib import Path


# 定义要保留的目录（白名单）
# 只保留真正的项目目录
KEEP_DIRS = {
    ".git",
    ".github",
    ".kiro",
    ".venv",
    ".vscode",
    ".idea",
    ".pytest_cache",
    "__pycache__",
    "docs",
    "grading",
    "hualiEdu",
    "toolbox",
    "templates",
    "static",
    "staticfiles",
    "media",
    "logs",
    "scripts",
    "tests",
    "htmlcov",
    "node_modules",
}

# 定义要删除的目录模式（正则表达式）
DELETE_PATTERNS = [
    r"^[0-9]$",  # 单个数字
    r"^[A-Za-z]$",  # 单个字母
    r"^[^A-Za-z0-9._-]",  # 以特殊字符开头
    r"^其他课程$",  # 测试课程目录
    r"^数据结构$",
    r"^算法设计$",
    r"^Data Structures$",
]


def has_control_characters(dir_name: str) -> bool:
    """检查目录名是否包含控制字符"""
    # 检查是否包含控制字符 (0x00-0x1F, 0x7F-0x9F)
    return bool(re.search(r'[\x00-\x1F\x7F-\x9F]', dir_name))


def should_delete(dir_name: str) -> bool:
    """检查目录是否应该被删除"""
    # 检查白名单
    if dir_name in KEEP_DIRS:
        return False

    # 检查是否包含控制字符（如 0ñ\x04）
    if has_control_characters(dir_name):
        return True

    # 检查删除模式
    for pattern in DELETE_PATTERNS:
        if re.match(pattern, dir_name):
            return True

    return False


def cleanup_test_directories(project_root: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    清理测试生成的随机目录
    
    Args:
        project_root: 项目根目录
        dry_run: 如果为 True，只显示将要删除的目录，不实际删除
        
    Returns:
        (deleted_count, skipped_count): 删除和跳过的目录数量
    """
    deleted_count = 0
    skipped_count = 0
    
    print(f"\n{'=' * 60}")
    print("清理 Hypothesis 测试生成的随机目录")
    print(f"{'=' * 60}\n")
    print(f"项目根目录: {project_root}")
    print(f"模式: {'预览模式（不实际删除）' if dry_run else '删除模式'}\n")
    
    # 遍历根目录下的所有目录
    for item in project_root.iterdir():
        # 只处理目录
        if not item.is_dir():
            continue
        
        dir_name = item.name
        
        # 跳过隐藏目录（以 . 开头）
        if dir_name.startswith('.'):
            continue
        
        # 检查是否应该删除
        if should_delete(dir_name):
            # 使用 repr() 显示包含控制字符的目录名
            display_name = repr(dir_name) if has_control_characters(dir_name) else dir_name
            print(f"🗑️  删除: {display_name}")
            if not dry_run:
                try:
                    shutil.rmtree(item)
                    deleted_count += 1
                except OSError as e:
                    print(f"   ❌ 删除失败: {e}")
            else:
                deleted_count += 1
        else:
            print(f"✅ 保留: {dir_name}")
            skipped_count += 1
    
    # 清理 .hypothesis 目录（如果存在）
    hypothesis_dir = project_root / ".hypothesis"
    if hypothesis_dir.exists():
        print("\n🗑️  删除 .hypothesis 目录")
        if not dry_run:
            try:
                shutil.rmtree(hypothesis_dir)
                print("   ✅ 已删除")
            except OSError as e:
                print(f"   ❌ 删除失败: {e}")
    
    return deleted_count, skipped_count


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 检查是否为预览模式
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    # 执行清理
    deleted, skipped = cleanup_test_directories(project_root, dry_run)
    
    # 显示统计
    print(f"\n{'=' * 60}")
    print("清理完成")
    print(f"{'=' * 60}")
    print(f"删除目录数: {deleted}")
    print(f"保留目录数: {skipped}")
    
    if dry_run:
        print("\n⚠️  这是预览模式，没有实际删除任何目录")
        print("   要实际删除，请运行: python scripts/cleanup_test_directories.py")
    
    # 显示提示
    print("\n💡 提示:")
    print("1. 这些目录是由 Hypothesis 属性测试生成的")
    print("2. 现在已配置 Hypothesis 使用系统临时目录")
    print("3. 如果这些目录再次出现，请检查测试配置")
    print("4. 参考文档: docs/HYPOTHESIS_TESTING.md")
    print()


if __name__ == "__main__":
    main()
