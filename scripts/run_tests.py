#!/usr/bin/env python3
"""
测试运行脚本
提供不同类型的测试运行选项
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description="", ignore_errors=False):
    """运行命令并显示结果"""
    if description:
        print(f"\n🔄 {description}")

    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print("输出:")
        print(result.stdout)

    if result.stderr and not ignore_errors:
        print("错误:")
        print(result.stderr)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="运行项目测试")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "django", "models", "views", "forms"],
        default="all",
        help="测试类型",
    )
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--failfast", "-f", action="store_true", help="遇到第一个失败就停止")
    parser.add_argument("--parallel", "-p", type=int, help="并行运行测试的进程数")
    parser.add_argument("--pattern", help="测试文件名模式")

    args = parser.parse_args()

    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🧪 开始运行测试...")
    print(f"测试类型: {args.type}")
    print(f"项目目录: {project_root}")

    success = True

    # 设置测试环境变量
    os.environ["DJANGO_SETTINGS_MODULE"] = "hualiEdu.settings"

    if args.type in ["all", "django", "models", "views", "forms"]:
        # 运行Django测试
        cmd = ["python", "manage.py", "test"]

        # 根据测试类型添加特定的测试路径
        if args.type == "models":
            cmd.append("grading.tests.test_models")
        elif args.type == "views":
            cmd.append("grading.tests.test_views")
        elif args.type == "forms":
            cmd.append("grading.tests.test_forms")
        elif args.type == "django":
            cmd.append("grading.tests")

        # 添加选项
        if args.verbose:
            cmd.append("--verbosity=2")

        if args.failfast:
            cmd.append("--failfast")

        if args.parallel:
            cmd.extend(["--parallel", str(args.parallel)])

        if args.pattern:
            cmd.extend(["--pattern", args.pattern])

        if not run_command(cmd, f"运行Django测试 ({args.type})"):
            success = False

    if args.type in ["all", "unit", "integration"]:
        # 运行pytest测试
        cmd = ["python", "-m", "pytest"]

        # 添加测试路径
        if args.type == "unit":
            cmd.extend(["-m", "not integration"])
        elif args.type == "integration":
            cmd.extend(["-m", "integration"])

        # 添加选项
        if args.verbose:
            cmd.append("-v")

        if args.failfast:
            cmd.append("-x")

        if args.coverage:
            cmd.extend(
                [
                    "--cov=grading",
                    "--cov=hualiEdu",
                    "--cov-report=html",
                    "--cov-report=term-missing",
                ]
            )

        # 添加测试路径
        cmd.extend(["tests/", "grading/tests/"])

        if not run_command(cmd, f"运行pytest测试 ({args.type})"):
            success = False

    # 运行代码质量检查
    if args.type == "all":
        print("\n🔍 运行代码质量检查...")

        # 检查Python语法
        print("检查Python语法...")
        result = subprocess.run(
            ["python", "-m", "py_compile"]
            + [
                str(f)
                for f in Path(".").rglob("*.py")
                if "migrations" not in str(f) and "venv" not in str(f)
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            print("⚠️  发现Python语法错误")

        # flake8检查（忽略某些错误）
        run_command(
            ["flake8", "--exclude=migrations,venv,env", "--ignore=E501,W503", "."],
            "运行flake8代码风格检查",
            ignore_errors=True,
        )

        # 检查是否有未提交的迁移文件
        if not run_command(
            ["python", "manage.py", "makemigrations", "--check", "--dry-run"],
            "检查数据库迁移",
            ignore_errors=True,
        ):
            print("⚠️  发现未提交的数据库迁移")

        # 检查模型一致性
        run_command(["python", "manage.py", "check"], "检查Django配置", ignore_errors=True)

    # 生成测试报告
    if success:
        print("\n📊 测试统计:")

        # 统计测试文件数量
        test_files = list(Path(".").rglob("test_*.py"))
        print(f"测试文件数量: {len(test_files)}")

        # 统计测试方法数量
        test_methods = 0
        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    test_methods += content.count("def test_")
            except:
                pass
        print(f"测试方法数量: {test_methods}")

        print("\n✅ 所有测试通过!")

        if args.coverage:
            print("\n📈 覆盖率报告已生成到 htmlcov/ 目录")
    else:
        print("\n❌ 部分测试失败!")
        print("\n💡 调试建议:")
        print("1. 检查测试输出中的错误信息")
        print("2. 使用 --verbose 选项获取更详细的输出")
        print("3. 使用 --failfast 选项在第一个失败时停止")
        print("4. 运行特定类型的测试，如 --type models")
        sys.exit(1)


if __name__ == "__main__":
    main()
