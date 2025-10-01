#!/usr/bin/env python3
"""
环境包装器 - 确保命令在py313环境中执行
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_conda():
    """查找conda可执行文件"""
    # 常见的conda路径
    conda_paths = [
        "~/anaconda3/bin/conda",
        "~/miniconda3/bin/conda",
        "/opt/anaconda3/bin/conda",
        "/opt/miniconda3/bin/conda",
        "/usr/local/anaconda3/bin/conda",
        "/usr/local/miniconda3/bin/conda",
    ]

    # 首先尝试从PATH中找到conda
    conda_cmd = shutil.which("conda")
    if conda_cmd:
        return conda_cmd

    # 尝试常见路径
    for path in conda_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            return expanded_path

    return None


def check_py313_env():
    """检查py313环境是否存在"""
    conda_cmd = find_conda()
    if not conda_cmd:
        return False

    try:
        result = subprocess.run(
            [conda_cmd, "env", "list"], capture_output=True, text=True, check=True
        )
        return "py313" in result.stdout
    except subprocess.CalledProcessError:
        return False


def create_py313_env():
    """创建py313环境"""
    conda_cmd = find_conda()
    if not conda_cmd:
        print("❌ 错误: 未找到conda命令")
        return False

    env_file = Path("environment.yml")
    if not env_file.exists():
        print("❌ 错误: 未找到environment.yml文件")
        return False

    print("🔧 正在创建py313环境...")
    try:
        subprocess.run([conda_cmd, "env", "create", "-f", "environment.yml"], check=True)
        print("✅ py313环境创建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建环境失败: {e}")
        return False


def run_in_py313(command_args):
    """在py313环境中运行命令"""
    conda_cmd = find_conda()
    if not conda_cmd:
        print("❌ 错误: 未找到conda命令")
        print("请确保已安装Anaconda或Miniconda")
        return 1

    # 检查py313环境是否存在
    if not check_py313_env():
        print("⚠️  py313环境不存在")
        if not create_py313_env():
            return 1

    # 构建conda run命令
    conda_run_cmd = [conda_cmd, "run", "-n", "py313"] + command_args

    print(f"🚀 在py313环境中执行: {' '.join(command_args)}")

    try:
        # 设置环境变量
        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "hualiEdu.settings"
        env["PYTHONPATH"] = os.getcwd()

        # 执行命令
        result = subprocess.run(conda_run_cmd, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  命令被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        return 1


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python run_in_env.py <command> [args...]")
        print("示例:")
        print("  python run_in_env.py python manage.py runserver")
        print("  python run_in_env.py python manage.py test")
        print("  python run_in_env.py python test_semester_manager_simple.py")
        return 1

    command_args = sys.argv[1:]
    return run_in_py313(command_args)


if __name__ == "__main__":
    sys.exit(main())
