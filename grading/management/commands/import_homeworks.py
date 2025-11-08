"""
管理命令：从文件系统导入作业信息
使用方法：python manage.py import_homeworks <repo_path> <course_name> [--dry-run]
"""

import os
from django.core.management.base import BaseCommand
from grading.models import Course, Homework


class Command(BaseCommand):
    help = '从文件系统导入作业信息'

    def add_arguments(self, parser):
        parser.add_argument('repo_path', type=str, help='仓库路径')
        parser.add_argument('course_name', type=str, help='课程名称')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要导入的作业，不实际导入',
        )
        parser.add_argument(
            '--default-type',
            type=str,
            default='normal',
            choices=['normal', 'lab_report'],
            help='默认作业类型（如果无法自动判断）',
        )

    def handle(self, *args, **options):
        repo_path = options['repo_path']
        course_name = options['course_name']
        dry_run = options['dry_run']
        default_type = options['default_type']
        
        # 查找课程
        try:
            course = Course.objects.get(name=course_name)
        except Course.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'课程不存在: {course_name}')
            )
            return
        
        self.stdout.write(f'课程: {course.name} (类型: {course.get_course_type_display()})')
        self.stdout.write(f'仓库路径: {repo_path}')
        self.stdout.write('-' * 80)
        
        if not os.path.exists(repo_path):
            self.stdout.write(
                self.style.ERROR(f'路径不存在: {repo_path}')
            )
            return
        
        # 扫描目录
        imported_count = 0
        skipped_count = 0
        
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            
            # 跳过文件，只处理目录
            if not os.path.isdir(item_path):
                continue
            
            # 跳过隐藏目录
            if item.startswith('.'):
                continue
            
            # 跳过班级目录（包含"班"字）
            if '班' in item or 'class' in item.lower():
                continue
            
            # 判断作业类型
            homework_type = default_type
            if course.course_type in ['lab', 'practice', 'mixed']:
                homework_type = 'lab_report'
            elif '实验' in item or 'lab' in item.lower():
                homework_type = 'lab_report'
            
            # 检查是否已存在
            existing = Homework.objects.filter(
                course=course,
                folder_name=item
            ).first()
            
            if existing:
                self.stdout.write(
                    f'[跳过] {item} (已存在)'
                )
                skipped_count += 1
                continue
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[预览] {item} -> {homework_type}'
                    )
                )
            else:
                Homework.objects.create(
                    course=course,
                    title=item,
                    homework_type=homework_type,
                    folder_name=item,
                    description=f'从文件系统导入: {item_path}'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[已导入] {item} -> {homework_type}'
                    )
                )
            
            imported_count += 1
        
        self.stdout.write('-' * 80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'预览模式：将导入 {imported_count} 个作业，跳过 {skipped_count} 个（未实际导入）'
                )
            )
            self.stdout.write(f'运行 python manage.py import_homeworks {repo_path} {course_name} 以实际导入')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'成功导入了 {imported_count} 个作业，跳过 {skipped_count} 个'
                )
            )
