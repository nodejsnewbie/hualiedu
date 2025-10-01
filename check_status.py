#!/usr/bin/env python
"""
项目状态检查脚本
检查项目的各个组件是否正常工作
"""

import os
import subprocess
import sys
from pathlib import Path

import django

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")
django.setup()

from django.conf import settings
from django.contrib.auth.models import User

from grading.models import Repository, Tenant, UserProfile


def check_python_environment():
    """检查Python环境"""
    print("🐍 Python环境检查")
    print(f"   Python版本: {sys.version}")
    print(f"   Django版本: {django.get_version()}")
    print(f"   项目路径: {settings.BASE_DIR}")
    print("   ✅ Python环境正常\n")


def check_database():
    """检查数据库连接"""
    print("📊 数据库检查")
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("   ✅ 数据库连接正常")

        # 检查迁移状态
        result = subprocess.run(
            ["python", "manage.py", "showmigrations", "--plan"], capture_output=True, text=True
        )

        if "[ ]" in result.stdout:
            print("   ⚠️  发现未应用的迁移")
        else:
            print("   ✅ 数据库迁移已是最新")

    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
    print()


def check_models():
    """检查模型数据"""
    print("🗃️  模型数据检查")
    try:
        user_count = User.objects.count()
        tenant_count = Tenant.objects.count()
        repo_count = Repository.objects.count()
        profile_count = UserProfile.objects.count()

        print(f"   用户数量: {user_count}")
        print(f"   租户数量: {tenant_count}")
        print(f"   仓库数量: {repo_count}")
        print(f"   用户配置文件数量: {profile_count}")

        if user_count > 0:
            print("   ✅ 模型数据正常")
        else:
            print("   ⚠️  暂无用户数据，建议创建超级用户")

    except Exception as e:
        print(f"   ❌ 模型检查失败: {e}")
    print()


def check_environment_variables():
    """检查环境变量"""
    print("🔧 环境变量检查")

    required_vars = {
        "SECRET_KEY": "必需的Django密钥",
        "DEBUG": "调试模式设置",
    }

    optional_vars = {
        "ARK_API_KEY": "AI评分API密钥",
        "ARK_MODEL": "AI模型名称",
        "LOG_LEVEL": "日志级别",
        "ALLOWED_HOSTS": "允许的主机",
    }

    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: 已设置 ({desc})")
        else:
            print(f"   ❌ {var}: 未设置 ({desc})")

    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: 已设置 ({desc})")
        else:
            print(f"   ⚠️  {var}: 未设置 ({desc})")
    print()


def check_repository_functionality():
    """检查仓库管理功能"""
    print("📁 仓库管理功能检查")
    try:
        # 检查Repository模型字段
        repo_fields = [f.name for f in Repository._meta.fields]
        required_fields = ["owner", "name", "repo_type", "url", "branch"]

        missing_fields = [f for f in required_fields if f not in repo_fields]
        if missing_fields:
            print(f"   ❌ 缺少字段: {missing_fields}")
        else:
            print("   ✅ Repository模型字段完整")

        # 检查仓库数据
        repos = Repository.objects.all()
        print(f"   仓库总数: {repos.count()}")

        for repo in repos[:3]:  # 显示前3个仓库
            print(f"   - {repo.name} ({repo.get_repo_type_display()})")

    except Exception as e:
        print(f"   ❌ 仓库功能检查失败: {e}")
    print()


def check_urls():
    """检查URL配置"""
    print("🌐 URL配置检查")
    try:
        from django.urls import reverse

        test_urls = [
            ("grading:index", "首页"),
            ("grading:repository_management", "仓库管理"),
            ("grading:grading_page", "评分页面"),
            ("admin:index", "管理后台"),
        ]

        for url_name, desc in test_urls:
            try:
                url = reverse(url_name)
                print(f"   ✅ {desc}: {url}")
            except Exception as e:
                print(f"   ❌ {desc}: 配置错误 - {e}")

    except Exception as e:
        print(f"   ❌ URL检查失败: {e}")
    print()


def main():
    """主检查函数"""
    print("🔍 华立教育项目状态检查")
    print("=" * 50)

    check_python_environment()
    check_database()
    check_models()
    check_environment_variables()
    check_repository_functionality()
    check_urls()

    print("🎉 项目状态检查完成！")
    print("\n💡 使用建议:")
    print("   - 运行服务器: ./start_server.sh")
    print("   - 创建超级用户: python manage.py createsuperuser")
    print("   - 收集静态文件: python manage.py collectstatic")
    print("   - 运行测试: python test_repository_management.py")


if __name__ == "__main__":
    main()
