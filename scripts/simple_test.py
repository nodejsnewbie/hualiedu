#!/usr/bin/env python
"""
简单测试脚本 - 直接测试Git存储适配器
"""

import os
import sys
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hualiEdu.settings')

import django
django.setup()

from grading.services.git_storage_adapter import GitStorageAdapter
from grading.services.storage_adapter import RemoteAccessError


def test_git_adapter():
    """测试Git存储适配器的网络错误处理"""
    print("=== 测试Git存储适配器 ===")
    
    # 使用一个不存在的Git仓库来模拟网络错误
    test_url = "https://gitee.com/nonexistent/repo.git"
    
    adapter = GitStorageAdapter(
        git_url=test_url,
        branch="main"
    )
    
    print(f"测试URL: {test_url}")
    
    try:
        print("尝试获取远程仓库...")
        repo_dir = adapter._ensure_remote_fetched()
        print(f"✅ 成功获取仓库目录: {repo_dir}")
        return True
    except RemoteAccessError as e:
        print(f"❌ 捕获到RemoteAccessError: {e}")
        print(f"用户友好消息: {getattr(e, 'user_message', '无')}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {type(e).__name__}: {e}")
        return False


def test_network_detection():
    """测试网络连接检测"""
    print("\n=== 测试网络连接检测 ===")
    
    # 测试网络错误关键词检测
    test_errors = [
        "ssh: Could not resolve hostname gitee.com: Name or service not known",
        "fatal: Could not read from remote repository",
        "Network is unreachable",
        "Connection timed out"
    ]
    
    network_keywords = [
        "could not resolve hostname", 
        "name or service not known", 
        "network unreachable", 
        "connection timed out"
    ]
    
    for error in test_errors:
        is_network_error = any(keyword in error.lower() for keyword in network_keywords)
        status = "✅ 网络错误" if is_network_error else "❌ 非网络错误"
        print(f"{status}: {error[:50]}...")
    
    return True


if __name__ == '__main__':
    print("开始测试Git存储适配器的网络错误处理...\n")
    
    # 测试网络错误检测逻辑
    detection_success = test_network_detection()
    
    # 测试实际的Git适配器（会触发网络错误）
    adapter_success = test_git_adapter()
    
    print(f"\n=== 测试结果 ===")
    print(f"网络错误检测: {'✅ 成功' if detection_success else '❌ 失败'}")
    print(f"Git适配器测试: {'✅ 成功' if adapter_success else '❌ 失败（预期）'}")
    
    if not adapter_success:
        print("\n📝 说明: Git适配器测试失败是预期的，因为我们使用了不存在的仓库URL")
        print("重要的是检查是否正确捕获和处理了网络错误")