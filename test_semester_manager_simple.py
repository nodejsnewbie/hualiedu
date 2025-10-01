#!/usr/bin/env python
"""
简单的学期管理器测试脚本
"""

import os
import sys
from datetime import date, timedelta

import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")

# 检查Python版本
print(f"Python版本: {sys.version}")
print(f"Django路径: {django.__file__}")

django.setup()

from grading.models import Semester
from grading.services.semester_manager import SemesterManager


def test_semester_manager():
    """测试学期管理器功能"""
    print("=== 学期管理器测试 ===")

    # 清理现有数据
    print("清理现有学期数据...")
    Semester.objects.all().delete()

    # 创建测试数据
    today = date.today()
    print(f"当前日期: {today}")

    # 创建过去的学期
    past_semester = Semester.objects.create(
        name="2023年春季学期",
        start_date=date(2023, 3, 1),
        end_date=date(2023, 7, 15),
        is_active=False,
    )
    print(f"创建过去学期: {past_semester.name}")

    # 创建当前学期（包含今天）
    current_semester = Semester.objects.create(
        name="2024年春季学期",
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=60),
        is_active=False,  # 故意设为False，测试自动更新
    )
    print(f"创建当前学期: {current_semester.name} (故意设为非活跃)")

    # 创建未来的学期
    future_semester = Semester.objects.create(
        name="2024年秋季学期",
        start_date=today + timedelta(days=90),
        end_date=today + timedelta(days=180),
        is_active=False,
    )
    print(f"创建未来学期: {future_semester.name}")

    # 初始化学期管理器
    manager = SemesterManager()

    # 测试自动更新当前学期
    print("\n--- 测试自动更新当前学期 ---")
    result = manager.auto_update_current_semester()
    if result:
        print(f"✓ 自动识别当前学期: {result.name}")
        print(f"✓ 学期状态已更新为活跃: {result.is_active}")
    else:
        print("✗ 未识别到当前学期")

    # 验证其他学期状态
    past_semester.refresh_from_db()
    future_semester.refresh_from_db()
    print(f"过去学期状态: {past_semester.is_active}")
    print(f"未来学期状态: {future_semester.is_active}")

    # 测试获取排序的学期列表
    print("\n--- 测试学期排序 ---")
    sorted_semesters = manager.get_sorted_semesters_for_display()
    print("排序后的学期列表:")
    for i, semester in enumerate(sorted_semesters):
        status = "当前" if semester.is_active else "非活跃"
        print(f"  {i+1}. {semester.name} ({status})")

    # 测试学期状态信息
    print("\n--- 测试学期状态信息 ---")
    for semester in [past_semester, current_semester, future_semester]:
        semester.refresh_from_db()
        status_info = manager.get_semester_status_info(semester)
        print(f"{semester.name}:")
        print(f"  状态: {status_info['status_text']}")
        print(f"  是否当前: {status_info['is_current']}")
        print(f"  需要同步: {status_info['needs_sync']}")

    # 测试同步所有学期状态
    print("\n--- 测试同步所有学期状态 ---")
    # 先故意设置错误状态
    past_semester.is_active = True
    past_semester.save()
    future_semester.is_active = True
    future_semester.save()
    current_semester.is_active = False
    current_semester.save()
    print("设置错误的学期状态...")

    sync_result = manager.sync_all_semester_status()
    print(f"同步结果: {sync_result}")

    # 验证同步后的状态
    print("同步后的学期状态:")
    for semester in Semester.objects.all():
        print(f"  {semester.name}: {'活跃' if semester.is_active else '非活跃'}")

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_semester_manager()
