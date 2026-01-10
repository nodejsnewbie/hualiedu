"""
Django管理命令：更新教师姓名
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from grading.views import get_teacher_display_name


class Command(BaseCommand):
    help = '更新教师的显示姓名'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='用户名')
        parser.add_argument('first_name', type=str, help='名字')
        parser.add_argument('last_name', type=str, help='姓氏')

    def handle(self, *args, **options):
        username = options['username']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            user = User.objects.get(username=username)
            
            self.stdout.write(f"找到用户: {user.username}")
            self.stdout.write(f"当前姓名: '{user.get_full_name()}'")
            
            # 更新姓名
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # 验证更新
            display_name = get_teacher_display_name(user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ 成功更新用户 {username} 的姓名为: {display_name}"
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ 用户 '{username}' 不存在")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 更新失败: {str(e)}")
            )