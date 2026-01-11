#!/usr/bin/env python
"""
测试 save_teacher_comment 功能的脚本

用于验证Git仓库文件路径解析和网络错误处理的修复
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hualiEdu.settings')

import django
django.setup()

import requests
from django.test import Client
from django.contrib.auth.models import User
from grading.models import Repository


def test_save_teacher_comment():
    """测试保存教师评价功能"""
    print("=== 测试 save_teacher_comment 功能 ===")
    
    # 创建测试客户端
    client = Client()
    
    # 获取测试用户（假设存在ID为1的用户）
    try:
        user = User.objects.get(id=1)
        print(f"使用测试用户: {user.username}")
    except User.DoesNotExist:
        print("错误: 未找到测试用户，请先创建用户")
        return False
    
    # 登录用户
    client.force_login(user)
    
    # 获取测试仓库（假设存在ID为11的Git仓库）
    try:
        repo = Repository.objects.get(id=11)
        print(f"使用测试仓库: {repo.name} (类型: {repo.repo_type})")
        print(f"仓库URL: {repo.git_url}")
    except Repository.DoesNotExist:
        print("错误: 未找到ID为11的测试仓库")
        return False
    
    # 准备测试数据
    test_data = {
        'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
        'comment': '测试评价：作业完成质量良好，但需要注意格式规范。',
        'grade': 'B',
        'repo_id': '11',
        'course': 'Web前端开发'
    }
    
    print(f"测试数据: {test_data}")
    
    # 发送POST请求
    print("\n发送保存教师评价请求...")
    response = client.post('/grading/save_teacher_comment/', test_data)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.content.decode('utf-8')}")
    
    # 分析响应
    if response.status_code == 200:
        print("✅ 请求成功处理")
        return True
    elif response.status_code == 400:
        print("⚠️  请求被拒绝（可能是网络问题或其他验证失败）")
        return False
    elif response.status_code == 500:
        print("❌ 服务器内部错误")
        return False
    else:
        print(f"❓ 未知响应状态: {response.status_code}")
        return False


def test_get_teacher_comment():
    """测试获取教师评价功能（对比测试）"""
    print("\n=== 测试 get_teacher_comment 功能（对比） ===")
    
    client = Client()
    user = User.objects.get(id=1)
    client.force_login(user)
    
    # 准备测试数据
    test_params = {
        'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
        'repo_id': '11',
        'course': 'Web前端开发'
    }
    
    print(f"测试参数: {test_params}")
    
    # 发送GET请求
    print("发送获取教师评价请求...")
    response = client.get('/grading/get_teacher_comment/', test_params)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.content.decode('utf-8')}")
    
    if response.status_code == 200:
        print("✅ get_teacher_comment 正常工作")
        return True
    else:
        print("❌ get_teacher_comment 也有问题")
        return False


if __name__ == '__main__':
    print("开始测试Git仓库文件操作功能...\n")
    
    # 先测试get功能（应该能工作）
    get_success = test_get_teacher_comment()
    
    # 再测试save功能（之前有问题）
    save_success = test_save_teacher_comment()
    
    print("\n=== 测试结果总结 ===")
    print(f"get_teacher_comment: {'✅ 成功' if get_success else '❌ 失败'}")
    print(f"save_teacher_comment: {'✅ 成功' if save_success else '❌ 失败'}")
    
    if save_success:
        print("\n🎉 修复成功！save_teacher_comment 功能正常工作")
    else:
        print("\n⚠️  仍有问题，需要进一步调试")