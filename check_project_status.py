#!/usr/bin/env python3
"""
项目状态检查脚本 - 验证py313环境和项目配置
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_conda():
    """检查conda是否可用"""
    conda_cmd = shutil.which("conda")
    if conda_cmd:
        print(f"✅ Conda已安装: {conda_cmd}")
        return True
    else:
        print("❌ Conda未找到")
        return False


def check_py313_env():
    """检查py313环境"""
    try:
        result = subprocess.run(
            ["conda", "env", "list"], capture_output=True, text=True, check=True
        )
        if "py313" in result.stdout:
            print("✅ py313环境已存在")
            return True
        else:
            print("❌ py313环境不存在")
            return False
    except subprocess.CalledProcessError:
        print("❌ 无法检查conda环境")
        return False


def check_python_version():
    """检查Python版本"""
    try:
        result = subprocess.run(
            ["conda", "run", "-n", "py313", "python", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        if "3.13" in version:
            print(f"✅ Python版本正确: {version}")
            return True
        else:
            print(f"❌ Python版本不正确: {version}")
            return False
    except subprocess.CalledProcessError:
        print("❌ 无法检查Python版本")
        return False


def check_django():
    """检查Django是否可用"""
    try:
        result = subprocess.run(
            [
                "conda",
                "run",
                "-n",
                "py313",
                "python",
                "-c",
                "import django; print(f'Django {django.get_version()}')",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ Django未安装或无法导入")
        return False


def check_project_files():
    """检查项目文件"""
    required_files = [
        "manage.py",
        "environment.yml",
        ".python-version",
        "requirements.txt",
        "run_in_env.py",
        "manage_py313.py",
        "test_py313.py",
    ]

    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 缺失")
            missing_files.append(file)

    return len(missing_files) == 0


def check_vscode_config():
    """检查VS Code配置"""
    vscode_files = [".vscode/settings.json", ".vscode/tasks.json", ".vscode/launch.json"]

    for file in vscode_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"⚠️  {file} 不存在")


def check_environment_tools():
    """检查环境工具"""
    tools = {"direnv": "brew install direnv", "autoenv": "brew install autoenv"}

    for tool, install_cmd in tools.items():
        if shutil.which(tool):
            print(f"✅ {tool}已安装")
        else:
            print(f"⚠️  {tool}未安装 (可选) - 安装命令: {install_cmd}")


def test_semester_manager():
    """测试学期管理器"""
    try:
        print("🧪 测试学期管理器...")
        result = subprocess.run(
            ["python", "test_py313.py", "test_semester_manager_simple.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ 学期管理器测试通过")
            return True
        else:
            print("❌ 学期管理器测试失败")
            print(f"错误输出: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 学期管理器测试超时")
        return False
    except Exception as e:
        print(f"❌ 学期管理器测试异常: {e}")
        return False


def main():
    """主函数"""
    print("🔍 检查项目状态...")
    print("=" * 50)

    checks = [
        ("Conda环境", check_conda),
        ("py313环境", check_py313_env),
        ("Python版本", check_python_version),
        ("Django", check_django),
        ("项目文件", check_project_files),
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n📋 检查{name}:")
        if check_func():
            passed += 1

    print(f"\n📋 检查VS Code配置:")
    check_vscode_config()

    print(f"\n📋 检查环境工具:")
    check_environment_tools()

    print(f"\n📋 功能测试:")
    test_passed = test_semester_manager()

    print("\n" + "=" * 50)
    print(f"📊 检查结果: {passed}/{total} 项基本检查通过")

    if passed == total and test_passed:
        print("🎉 项目配置完美！可以开始开发了")
        print("\n💡 常用命令:")
        print("  make runserver    # 启动开发服务器")
        print("  make test         # 运行测试")
        print("  make help         # 查看所有命令")
        return 0
    else:
        print("⚠️  项目配置需要修复")
        if passed < total:
            print("请修复基本配置问题")
        if not test_passed:
            print("请修复功能测试问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
