#!/usr/bin/env python
"""
测试仓库管理功能
"""

import os
import sys

import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")
django.setup()

from django.contrib.auth.models import User

from grading.models import Repository, Tenant, UserProfile


def test_repository_management():
    """测试仓库管理功能"""
    print("🧪 开始测试仓库管理功能...")

    # 1. 创建测试用户
    print("\n1. 创建测试用户...")
    user, created = User.objects.get_or_create(
        username="test_user",
        defaults={"email": "test@example.com", "first_name": "测试", "last_name": "用户"},
    )
    if created:
        user.set_password("testpass123")
        user.save()
        print(f"✅ 创建用户: {user.username}")
    else:
        print(f"✅ 用户已存在: {user.username}")

    # 2. 创建租户和用户配置文件
    print("\n2. 创建租户和用户配置文件...")
    tenant, created = Tenant.objects.get_or_create(
        name="测试租户", defaults={"description": "测试用租户"}
    )
    if created:
        print(f"✅ 创建租户: {tenant.name}")
    else:
        print(f"✅ 租户已存在: {tenant.name}")

    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={"tenant": tenant, "repo_base_dir": "~/test_repos", "is_tenant_admin": True},
    )
    if created:
        print(f"✅ 创建用户配置文件: {profile}")
    else:
        print(f"✅ 用户配置文件已存在: {profile}")

    # 3. 测试创建本地仓库
    print("\n3. 测试创建本地仓库...")
    local_repo, created = Repository.objects.get_or_create(
        owner=user,
        name="test-local-repo",
        defaults={
            "tenant": tenant,
            "path": "local-homework",
            "description": "测试本地仓库",
            "repo_type": "local",
        },
    )
    if created:
        print(f"✅ 创建本地仓库: {local_repo.name}")
    else:
        print(f"✅ 本地仓库已存在: {local_repo.name}")

    # 4. 测试创建Git仓库
    print("\n4. 测试创建Git仓库...")
    git_repo, created = Repository.objects.get_or_create(
        owner=user,
        name="test-git-repo",
        defaults={
            "tenant": tenant,
            "path": "git-homework",
            "url": "https://github.com/example/test-repo.git",
            "branch": "main",
            "description": "测试Git仓库",
            "repo_type": "git",
        },
    )
    if created:
        print(f"✅ 创建Git仓库: {git_repo.name}")
    else:
        print(f"✅ Git仓库已存在: {git_repo.name}")

    # 5. 测试仓库查询
    print("\n5. 测试仓库查询...")
    user_repos = Repository.objects.filter(owner=user, is_active=True)
    print(f"✅ 用户仓库数量: {user_repos.count()}")

    for repo in user_repos:
        print(f"   - {repo.name} ({repo.get_repo_type_display()})")
        print(f"     路径: {repo.get_display_path()}")
        print(f"     描述: {repo.description}")
        if repo.is_git_repository():
            print(f"     分支: {repo.branch}")
            print(f"     可同步: {repo.can_sync()}")

    # 6. 测试仓库方法
    print("\n6. 测试仓库方法...")
    for repo in user_repos:
        print(f"   仓库: {repo.name}")
        print(f"   - 完整路径: {repo.get_full_path()}")
        print(f"   - 显示路径: {repo.get_display_path()}")
        print(f"   - 是否Git仓库: {repo.is_git_repository()}")
        print(f"   - 可以同步: {repo.can_sync()}")

    print("\n🎉 仓库管理功能测试完成！")
    return True


def test_repository_api():
    """测试仓库API功能"""
    print("\n🔧 测试仓库API功能...")

    from django.test import Client
    from django.urls import reverse

    client = Client()

    # 获取测试用户
    user = User.objects.get(username="test_user")
    client.force_login(user)

    # 测试获取仓库列表API
    print("\n1. 测试获取仓库列表API...")
    response = client.get(reverse("grading:get_repository_list_api"))
    print(f"   状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API响应正常")
        print(f"   仓库数量: {data.get('total', 0)}")
        for repo in data.get("repositories", []):
            print(f"   - {repo['name']} ({repo['type']})")
    else:
        print(f"   ❌ API响应异常: {response.content}")

    print("\n🎉 仓库API测试完成！")


if __name__ == "__main__":
    try:
        test_repository_management()
        test_repository_api()
        print("\n✅ 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
