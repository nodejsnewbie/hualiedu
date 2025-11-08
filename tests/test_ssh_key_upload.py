#!/usr/bin/env python
"""
测试SSH私钥文件上传功能
"""
import os
import sys
import django
import tempfile

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hualiEdu.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from grading.models import TenantConfig
from django.core.files.uploadedfile import SimpleUploadedFile

def test_ssh_key_upload():
    """测试SSH私钥文件上传功能"""
    print("🔐 测试SSH私钥文件上传功能...")
    
    # 创建测试客户端
    client = Client()
    
    # 登录
    print("\n🔐 登录...")
    login_success = client.login(username='linyuan', password='123')
    if not login_success:
        print("❌ 登录失败")
        return
    print("✅ 登录成功")
    
    # 获取用户和租户
    linyuan_user = User.objects.get(username='linyuan')
    tenant = linyuan_user.profile.tenant
    
    # 清理现有配置
    print("\n🧹 清理现有SSH配置...")
    TenantConfig.objects.filter(tenant=tenant, key='ssh_private_key').delete()
    
    # 创建测试SSH私钥文件
    print("\n📄 创建测试SSH私钥文件...")
    test_ssh_key = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
QRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX
YZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456
7890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcd
efghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijk
lmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqr
stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxy
zABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEF
GHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLM
NOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST
UVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
-----END OPENSSH PRIVATE KEY-----"""
    
    # 创建上传文件对象
    ssh_key_file = SimpleUploadedFile(
        "id_rsa",
        test_ssh_key.encode('utf-8'),
        content_type="text/plain"
    )
    
    # 测试文件上传
    print("\n📤 测试文件上传...")
    auth_config_url = '/admin/grading/tenantconfig/auth-config/'
    
    response = client.post(auth_config_url, {
        'ssh_private_key_file': ssh_key_file,
        'config_https_username': 'testuser',
        'config_https_token': 'test_token_123'
    })
    
    print(f"上传响应状态码: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ 上传成功，页面重定向")
        
        # 检查配置是否保存
        saved_ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
        if saved_ssh_key:
            print("✅ SSH私钥已保存到数据库")
            print(f"   保存的私钥长度: {len(saved_ssh_key)} 字符")
            
            if 'BEGIN OPENSSH PRIVATE KEY' in saved_ssh_key:
                print("✅ SSH私钥格式正确")
            else:
                print("❌ SSH私钥格式不正确")
        else:
            print("❌ SSH私钥未保存")
    else:
        print("❌ 上传失败")
        if response.content:
            content = response.content.decode('utf-8')
            if 'error' in content.lower():
                print("页面包含错误信息")
    
    # 测试无效文件上传
    print("\n🚫 测试无效文件上传...")
    invalid_file = SimpleUploadedFile(
        "invalid.txt",
        b"This is not a valid SSH key",
        content_type="text/plain"
    )
    
    response = client.post(auth_config_url, {
        'ssh_private_key_file': invalid_file
    })
    
    print(f"无效文件上传状态码: {response.status_code}")
    
    # 测试清除SSH私钥
    print("\n🗑️ 测试清除SSH私钥...")
    response = client.post(auth_config_url, {
        'clear_ssh_key': '1'
    })
    
    print(f"清除响应状态码: {response.status_code}")
    
    if response.status_code == 302:
        # 检查是否已清除
        cleared_ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
        if not cleared_ssh_key:
            print("✅ SSH私钥已清除")
        else:
            print("❌ SSH私钥未清除")
    
    print(f"\n🎉 SSH私钥文件上传功能测试完成！")

if __name__ == "__main__":
    test_ssh_key_upload()