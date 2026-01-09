#!/usr/bin/env python
"""
批量登分功能诊断脚本

使用方法：
conda run -n py313 python scripts/diagnose_batch_grade.py <课程名称> <作业文件夹名称>

例如：
conda run -n py313 python scripts/diagnose_batch_grade.py Python程序设计 第一次作业
"""

import os
import sys

import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")
django.setup()

from django.contrib.auth.models import User

from grading.models import Course, Homework, Repository


def diagnose(course_name, homework_folder):
    print("=" * 80)
    print("批量登分功能诊断")
    print("=" * 80)
    print()

    # 1. 检查课程是否存在
    print("1. 检查课程...")
    try:
        course = Course.objects.get(name=course_name)
        print(f"   ✓ 课程存在: {course.name}")
        print(f"     - 类型: {course.get_course_type_display()}")
        print(f"     - 班级: {course.class_name or '无'}")
        print(f"     - 教师: {course.teacher.username if course.teacher else '无'}")
    except Course.DoesNotExist:
        print(f"   ✗ 课程不存在: {course_name}")
        print()
        print("解决方案：")
        print("  1. 在Django Admin中创建课程")
        print("  2. 或使用管理命令创建课程")
        return
    print()

    # 2. 检查作业是否存在
    print("2. 检查作业...")
    try:
        homework = Homework.objects.get(course=course, folder_name=homework_folder)
        print(f"   ✓ 作业存在: {homework.title}")
        print(f"     - ID: {homework.id}")
        print(f"     - 类型: {homework.get_homework_type_display()}")
        print(f"     - 文件夹名称: {homework.folder_name}")
    except Homework.DoesNotExist:
        print(f"   ✗ 作业不存在: {homework_folder}")
        print()
        print("解决方案：")
        print(
            f"  1. 使用导入命令: conda run -n py313 python manage.py import_homeworks <仓库路径> {course_name}"
        )
        print("  2. 或在Django Admin中手动创建作业")
        return
    print()

    # 3. 检查仓库
    print("3. 检查仓库...")
    repositories = Repository.objects.filter(is_active=True)
    if not repositories.exists():
        print("   ✗ 没有活跃的仓库")
        print()
        print("解决方案：")
        print("  在Django Admin中创建并激活仓库")
        return

    print(f"   ✓ 找到 {repositories.count()} 个活跃仓库:")
    for repo in repositories:
        print(f"     - {repo.name} ({repo.get_repo_type_display()})")
        print(f"       路径: {repo.get_full_path()}")
    print()

    # 4. 检查作业目录是否存在
    print("4. 检查作业目录...")
    found = False
    for repo in repositories:
        repo_base = repo.get_full_path()

        # 尝试不同的路径组合
        possible_paths = []

        if course.class_name:
            # 路径1: <repo>/<course>/<class>/<homework>
            path1 = os.path.join(repo_base, course.name, course.class_name, homework.folder_name)
            possible_paths.append(path1)

        # 路径2: <repo>/<course>/<homework>
        path2 = os.path.join(repo_base, course.name, homework.folder_name)
        possible_paths.append(path2)

        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                print(f"   ✓ 找到作业目录:")
                print(f"     路径: {path}")
                print(f"     仓库: {repo.name}")

                # 检查目录内容
                files = os.listdir(path)
                word_files = [
                    f for f in files if f.endswith((".docx", ".doc")) and not f.startswith("~$")
                ]
                print(f"     文件数: {len(files)}")
                print(f"     Word文档数: {len(word_files)}")

                found = True
                break

        if found:
            break

    if not found:
        print("   ✗ 未找到作业目录")
        print()
        print("尝试的路径:")
        for repo in repositories:
            repo_base = repo.get_full_path()
            if course.class_name:
                path1 = os.path.join(
                    repo_base, course.name, course.class_name, homework.folder_name
                )
                print(f"  - {path1}")
            path2 = os.path.join(repo_base, course.name, homework.folder_name)
            print(f"  - {path2}")
        print()
        print("解决方案：")
        print("  1. 检查文件夹名称是否与数据库中的 folder_name 一致")
        print("  2. 检查仓库路径是否正确")
        print("  3. 检查课程和班级名称是否正确")
    print()

    # 5. 检查班级成绩登记表
    print("5. 检查班级成绩登记表...")
    if found:
        for repo in repositories:
            repo_base = repo.get_full_path()

            if course.class_name:
                class_dir = os.path.join(repo_base, course.name, course.class_name)
            else:
                class_dir = os.path.join(repo_base, course.name)

            if os.path.exists(class_dir):
                excel_files = [f for f in os.listdir(class_dir) if f.lower().endswith(".xlsx")]
                if excel_files:
                    print(f"   ✓ 找到 {len(excel_files)} 个Excel文件:")
                    for f in excel_files:
                        print(f"     - {f}")
                else:
                    print("   ✗ 未找到Excel文件")
                    print()
                    print("解决方案：")
                    print("  在班级目录中创建成绩登记表Excel文件")
                break
    print()

    print("=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法:")
        print(f"  {sys.argv[0]} <课程名称> <作业文件夹名称>")
        print()
        print("例如:")
        print(f"  {sys.argv[0]} Python程序设计 第一次作业")
        sys.exit(1)

    course_name = sys.argv[1]
    homework_folder = sys.argv[2]

    diagnose(course_name, homework_folder)
