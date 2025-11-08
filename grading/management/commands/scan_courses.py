"""
管理命令：扫描仓库目录，自动发现和创建课程
使用方法：python manage.py scan_courses <repo_path> [--dry-run]
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from grading.models import Course, Semester


class Command(BaseCommand):
    help = '扫描仓库目录，自动发现和创建课程'

    def add_arguments(self, parser):
        parser.add_argument('repo_path', type=str, help='仓库路径')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示将要创建的课程，不实际创建',
        )
        parser.add_argument(
            '--teacher',
            type=str,
            help='指定教师用户名（默认使用第一个staff用户）',
        )

    def auto_detect_course_type(self, course_name):
        """自动检测课程类型"""
        course_name_lower = course_name.lower()
        
        # 实验课关键词
        lab_keywords = ["实验", "lab", "experiment"]
        # 实训课关键词
        practice_keywords = ["实训", "practice", "实践"]
        # 混合课关键词
        mixed_keywords = ["理论与实验", "理论+实验", "mixed"]
        
        if any(keyword in course_name_lower for keyword in mixed_keywords):
            return "mixed"
        elif any(keyword in course_name_lower for keyword in lab_keywords):
            return "lab"
        elif any(keyword in course_name_lower for keyword in practice_keywords):
            return "practice"
        else:
            return "theory"

    def handle(self, *args, **options):
        repo_path = options['repo_path']
        dry_run = options['dry_run']
        teacher_username = options.get('teacher')
        
        self.stdout.write(f'扫描仓库路径: {repo_path}')
        self.stdout.write('-' * 80)
        
        if not os.path.exists(repo_path):
            self.stdout.write(
                self.style.ERROR(f'路径不存在: {repo_path}')
            )
            return
        
        # 获取当前活跃学期
        current_semester = Semester.objects.filter(is_active=True).first()
        if not current_semester:
            current_semester = Semester.objects.order_by('-start_date').first()
        
        if not current_semester:
            self.stdout.write(
                self.style.ERROR('没有可用的学期，请先创建学期')
            )
            return
        
        self.stdout.write(f'使用学期: {current_semester.name}')
        
        # 获取教师用户
        if teacher_username:
            try:
                teacher = User.objects.get(username=teacher_username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'用户不存在: {teacher_username}')
                )
                return
        else:
            teacher = User.objects.filter(is_staff=True).first()
            if not teacher:
                self.stdout.write(
                    self.style.ERROR('没有可用的教师用户')
                )
                return
        
        self.stdout.write(f'使用教师: {teacher.username}')
        self.stdout.write('-' * 80)
        
        # 扫描目录
        created_count = 0
        skipped_count = 0
        updated_count = 0
        
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            
            # 只处理目录
            if not os.path.isdir(item_path):
                continue
            
            # 跳过隐藏目录
            if item.startswith('.'):
                continue
            
            # 跳过特殊目录
            if item in ['__pycache__', 'node_modules', '.git']:
                continue
            
            course_name = item
            course_type = self.auto_detect_course_type(course_name)
            
            # 检查是否已存在
            existing = Course.objects.filter(name=course_name).first()
            
            if existing:
                # 检查类型是否需要更新
                if existing.course_type != course_type:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'[预览-更新] {course_name}: {existing.course_type} -> {course_type}'
                            )
                        )
                    else:
                        old_type = existing.course_type
                        existing.course_type = course_type
                        existing.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'[已更新] {course_name}: {old_type} -> {course_type}'
                            )
                        )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f'[跳过] {course_name} (已存在，类型: {course_type})'
                    )
                    skipped_count += 1
                continue
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[预览-创建] {course_name} -> {course_type}'
                    )
                )
            else:
                Course.objects.create(
                    name=course_name,
                    course_type=course_type,
                    semester=current_semester,
                    teacher=teacher,
                    location='待设置',
                    description=f'自动扫描创建（从目录: {item_path}）'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[已创建] {course_name} -> {course_type}'
                    )
                )
            
            created_count += 1
        
        self.stdout.write('-' * 80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'预览模式：将创建 {created_count} 个课程，更新 {updated_count} 个，跳过 {skipped_count} 个（未实际操作）'
                )
            )
            self.stdout.write(f'运行 python manage.py scan_courses {repo_path} 以实际创建')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'成功创建了 {created_count} 个课程，更新了 {updated_count} 个，跳过了 {skipped_count} 个'
                )
            )
