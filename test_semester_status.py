#!/usr/bin/env python
"""
学期状态功能测试脚本
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
from grading.services.semester_status import semester_status_service


def test_semester_status():
    """测试学期状态功能"""
    print("=== 学期状态功能测试 ===")

    # 清理现有数据
    print("清理现有学期数据...")
    Semester.objects.all().delete()

    # 创建测试数据
    today = date.today()
    print(f"当前日期: {today}")

    # 创建过去的学期（上学期）
    past_semester = Semester.objects.create(
        name="2023年秋季学期",
        start_date=date(2023, 9, 1),
        end_date=date(2024, 1, 15),
        is_active=False,
        season="autumn",
    )
    print(f"创建过去学期: {past_semester.name}")

    # 创建当前学期
    current_semester = Semester.objects.create(
        name="2024年春季学期",
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=60),
        is_active=True,
        season="spring",
    )
    print(f"创建当前学期: {current_semester.name}")

    # 创建未来的学期
    future_semester = Semester.objects.create(
        name="2024年秋季学期",
        start_date=today + timedelta(days=90),
        end_date=today + timedelta(days=210),
        is_active=False,
        season="autumn",
    )
    print(f"创建未来学期: {future_semester.name}")

    # 测试综合状态
    print("\n--- 测试综合学期状态 ---")
    comprehensive_status = semester_status_service.get_comprehensive_status(today)

    print(f"状态摘要: {comprehensive_status['summary']['text']}")
    print(f"状态类型: {comprehensive_status['summary']['type']}")

    if comprehensive_status["current_semester"]:
        current = comprehensive_status["current_semester"]
        print(f"当前学期: {current['name']}")
        print(f"学期季节: {current['season_text']}")
        print(f"学期进度: {comprehensive_status['status'].get('progress_percentage', 0):.1f}%")
        print(f"剩余天数: {comprehensive_status['status'].get('days_to_end', 0)}天")

    # 测试假期状态
    print(f"\n--- 假期状态 ---")
    vacation = comprehensive_status["vacation"]
    print(f"是否假期: {vacation['is_vacation']}")
    if vacation["is_vacation"]:
        print(f"假期类型: {vacation['text']}")
        print(f"假期描述: {vacation['description']}")

    # 测试下一学期信息
    if comprehensive_status["next_semester"]:
        next_sem = comprehensive_status["next_semester"]
        print(f"\n--- 下一学期 ---")
        print(f"下一学期: {next_sem['semester']['name']}")
        print(f"开始日期: {next_sem['start_date']}")
        print(f"倒计时: {next_sem['countdown_text']}")

    # 测试上一学期信息
    if comprehensive_status["previous_semester"]:
        prev_sem = comprehensive_status["previous_semester"]
        print(f"\n--- 上一学期 ---")
        print(f"上一学期: {prev_sem['semester']['name']}")
        print(f"结束日期: {prev_sem['end_date']}")
        print(f"已结束: {prev_sem['elapsed_text']}")

    # 测试时间线
    print(f"\n--- 学期时间线 ---")
    timeline = comprehensive_status["timeline"]
    for item in timeline:
        semester = item["semester"]
        relation = item["relation"]
        status_icon = "📍" if item["is_current"] else "📅"
        print(
            f"{status_icon} {semester['name']} ({relation}) - {semester['start_date']} 到 {semester['end_date']}"
        )

    # 测试仪表板信息
    print(f"\n--- 仪表板信息 ---")
    dashboard = semester_status_service.get_dashboard_info(today)
    print(f"当前状态: {dashboard['current_status']}")
    print(f"当前学期: {dashboard['current_semester']}")
    print(f"是否假期: {dashboard['is_vacation']}")
    print(f"假期类型: {dashboard['vacation_type']}")
    print(f"下一学期: {dashboard['next_semester']}")
    print(f"距离下学期: {dashboard['days_to_next']}天")

    # 测试不同日期场景
    print(f"\n--- 测试不同日期场景 ---")

    # 测试假期日期
    vacation_date = current_semester.end_date + timedelta(days=10)
    print(f"\n假期日期测试 ({vacation_date}):")
    vacation_status = semester_status_service.get_comprehensive_status(vacation_date)
    print(f"状态: {vacation_status['summary']['text']}")
    print(f"假期类型: {vacation_status['vacation']['text']}")

    # 测试学期开始日期
    semester_start = current_semester.start_date
    print(f"\n学期开始日期测试 ({semester_start}):")
    start_status = semester_status_service.get_comprehensive_status(semester_start)
    print(f"状态: {start_status['summary']['text']}")

    # 测试学期结束日期
    semester_end = current_semester.end_date
    print(f"\n学期结束日期测试 ({semester_end}):")
    end_status = semester_status_service.get_comprehensive_status(semester_end)
    print(f"状态: {end_status['summary']['text']}")

    print("\n=== 测试完成 ===")


def test_edge_cases():
    """测试边界情况"""
    print("\n=== 边界情况测试 ===")

    # 测试没有学期的情况
    Semester.objects.all().delete()

    no_semester_status = semester_status_service.get_comprehensive_status()
    print(f"无学期状态: {no_semester_status['summary']['text']}")

    # 测试只有未来学期的情况
    future_only = Semester.objects.create(
        name="未来学期",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=150),
        is_active=False,
    )

    future_only_status = semester_status_service.get_comprehensive_status()
    print(f"只有未来学期: {future_only_status['summary']['text']}")

    print("=== 边界情况测试完成 ===")


if __name__ == "__main__":
    test_semester_status()
    test_edge_cases()
