#!/usr/bin/env python
"""
更新教师姓名的脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hualiEdu.settings')

import django
django.setup()

from django.contrib.auth.models import User


def update_teacher_name():
    """更新用户linyuan的教师姓名"""
    try:
        # 查找用户linyuan
        user = User.objects.get(username='linyuan')
        print(f"找到用户: {user.username}")
        print(f"当前信息:")
        print(f"  - first_name: '{user.first_name}'")
        print(f"  - last_name: '{user.last_name}'")
        print(f"  - get_full_name(): '{user.get_full_name()}'")
        print(f"  - email: '{user.email}'")
        
        # 更新姓名信息
        user.first_name = "林"
        user.last_name = "原"
        user.save()
        
        print(f"\n✅ 更新成功!")
        print(f"新的信息:")
        print(f"  - first_name: '{user.first_name}'")
        print(f"  - last_name: '{user.last_name}'")
        print(f"  - get_full_name(): '{user.get_full_name()}'")
        
        # 验证get_teacher_display_name函数
        from grading.views import get_teacher_display_name
        display_name = get_teacher_display_name(user)
        print(f"  - get_teacher_display_name(): '{display_name}'")
        
        return True
        
    except User.DoesNotExist:
        print("❌ 用户 'linyuan' 不存在")
        return False
    except Exception as e:
        print(f"❌ 更新失败: {str(e)}")
        return False


def list_all_users():
    """列出所有用户信息"""
    print("=== 所有用户列表 ===")
    users = User.objects.all()
    for user in users:
        print(f"用户名: {user.username}")
        print(f"  - 姓名: {user.get_full_name()}")
        print(f"  - 邮箱: {user.email}")
        print(f"  - 是否活跃: {user.is_active}")
        print(f"  - 是否管理员: {user.is_staff}")
        print()


if __name__ == '__main__':
    print("开始更新教师姓名...\n")
    
    # 先列出所有用户
    list_all_users()
    
    # 更新linyuan用户的姓名
    success = update_teacher_name()
    
    if success:
        print("\n🎉 教师姓名更新完成！")
        print("现在教师签名将显示为 '林原' 而不是 'linyuan'")
    else:
        print("\n⚠️ 更新失败，请检查错误信息")