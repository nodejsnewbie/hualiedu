"""
管理命令：根据课程名称自动更新课程类型
使用方法：python manage.py update_course_types [--dry-run]
"""

from django.core.management.base import BaseCommand
from grading.models import Course


class Command(BaseCommand):
    help = '根据课程名称自动更新课程类型'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要更新的课程，不实际更新',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 定义关键词映射
        lab_keywords = ['实验', 'lab', 'experiment', '实训', 'practice']
        
        courses = Course.objects.all()
        total_count = courses.count()
        updated_count = 0
        
        self.stdout.write(f'共找到 {total_count} 个课程')
        self.stdout.write('-' * 80)
        
        for course in courses:
            course_name_lower = course.name.lower()
            old_type = course.course_type
            
            # 检查是否包含实验相关关键词
            is_lab = any(keyword in course_name_lower for keyword in lab_keywords)
            
            if is_lab and course.course_type == 'theory':
                new_type = 'lab'
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[预览] 课程: {course.name} ({old_type} -> {new_type})'
                        )
                    )
                else:
                    course.course_type = new_type
                    course.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[已更新] 课程: {course.name} ({old_type} -> {new_type})'
                        )
                    )
                
                updated_count += 1
            else:
                self.stdout.write(
                    f'[跳过] 课程: {course.name} (类型: {course.course_type})'
                )
        
        self.stdout.write('-' * 80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'预览模式：将更新 {updated_count} 个课程（未实际更新）'
                )
            )
            self.stdout.write('运行 python manage.py update_course_types 以实际更新')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'成功更新了 {updated_count} 个课程的类型'
                )
            )
