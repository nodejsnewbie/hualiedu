"""
CurrentSemesterDetector的单元测试
"""

import os
import sys
from datetime import date, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")

import django

django.setup()

from grading.models import Semester
from grading.services.semester_detector import CurrentSemesterDetector


def setup_test_data():
    """设置测试数据"""
    # 清理现有数据
    Semester.objects.all().delete()

    # 创建测试学期
    # 2024年春季学期
    Semester.objects.create(
        name="2024年春季", start_date=date(2024, 3, 1), end_date=date(2024, 7, 15), is_active=False
    )

    # 2024年秋季学期
    Semester.objects.create(
        name="2024年秋季", start_date=date(2024, 9, 1), end_date=date(2025, 1, 20), is_active=True
    )

    # 2025年春季学期
    Semester.objects.create(
        name="2025年春季", start_date=date(2025, 3, 1), end_date=date(2025, 7, 15), is_active=False
    )


def test_detect_current_semester():
    """测试检测当前学期功能"""
    print("测试检测当前学期功能...")
    setup_test_data()

    detector = CurrentSemesterDetector()

    # 测试在学期范围内的日期
    current_semester = detector.detect_current_semester(date(2024, 4, 15))
    assert current_semester is not None
    assert current_semester.name == "2024年春季"
    print("✓ 正确检测到春季学期")

    # 测试在秋季学期范围内的日期
    current_semester = detector.detect_current_semester(date(2024, 10, 15))
    assert current_semester is not None
    assert current_semester.name == "2024年秋季"
    print("✓ 正确检测到秋季学期")

    # 测试跨年学期
    current_semester = detector.detect_current_semester(date(2025, 1, 10))
    assert current_semester is not None
    assert current_semester.name == "2024年秋季"
    print("✓ 正确检测到跨年学期")

    # 测试不在任何学期范围内的日期
    current_semester = detector.detect_current_semester(date(2024, 8, 15))
    assert current_semester is None
    print("✓ 正确识别学期间隙")

    # 测试多个重叠学期时选择最近开始的
    # 创建重叠学期
    Semester.objects.create(
        name="2024年春季延长",
        start_date=date(2024, 3, 15),
        end_date=date(2024, 7, 30),
        is_active=False,
    )

    current_semester = detector.detect_current_semester(date(2024, 4, 1))
    assert current_semester.name == "2024年春季延长"  # 最近开始的学期
    print("✓ 正确选择最近开始的学期")


def test_should_create_semester():
    """测试是否需要创建学期的判断"""
    print("\n测试是否需要创建学期的判断...")
    setup_test_data()

    detector = CurrentSemesterDetector()

    # 测试已存在学期的日期
    should_create = detector.should_create_semester(date(2024, 4, 15))
    assert not should_create
    print("✓ 已存在学期时不需要创建")

    # 测试学期间隙中的日期 - 使用2025年秋季（还不存在）
    test_date = date(2025, 8, 15)
    try:
        expected_start, expected_end = detector.get_expected_semester_period(test_date)
        print(f"预期学期时间段: {expected_start} - {expected_end}")
    except Exception as e:
        print(f"计算预期时间段失败: {e}")

    should_create = detector.should_create_semester(test_date)
    print(f"学期间隙测试 (2025-08-15): should_create = {should_create}")
    assert should_create
    print("✓ 学期间隙中需要创建学期")

    # 测试接近学期开始的日期
    should_create = detector.should_create_semester(date(2025, 8, 20))
    assert should_create
    print("✓ 接近新学期开始时需要创建")

    # 测试远离任何学期的日期
    should_create = detector.should_create_semester(date(2026, 6, 15))
    assert should_create
    print("✓ 预期学期时间段内需要创建")


def test_get_expected_semester_period():
    """测试获取预期学期时间段"""
    print("\n测试获取预期学期时间段...")
    setup_test_data()

    detector = CurrentSemesterDetector()

    # 测试基于历史模式的计算
    start_date, end_date = detector.get_expected_semester_period(date(2025, 4, 15))
    assert start_date == date(2025, 3, 1)
    assert end_date == date(2025, 7, 15)
    print("✓ 正确基于历史模式计算春季学期")

    # 测试秋季学期
    start_date, end_date = detector.get_expected_semester_period(date(2025, 10, 15))
    assert start_date == date(2025, 9, 1)
    assert end_date == date(2026, 1, 20)
    print("✓ 正确基于历史模式计算秋季学期")

    # 测试跨年日期
    start_date, end_date = detector.get_expected_semester_period(date(2026, 1, 10))
    assert start_date == date(2025, 9, 1)
    assert end_date == date(2026, 1, 20)
    print("✓ 正确处理跨年学期")


def test_calculate_from_default_template():
    """测试默认模板计算"""
    print("\n测试默认模板计算...")

    # 清理所有学期数据，测试默认模板
    Semester.objects.all().delete()

    detector = CurrentSemesterDetector()

    # 测试春季学期默认模板
    start_date, end_date = detector.get_expected_semester_period(date(2025, 4, 15))
    assert start_date == date(2025, 3, 1)
    assert end_date == date(2025, 7, 31)
    print("✓ 正确使用春季默认模板")

    # 测试秋季学期默认模板
    start_date, end_date = detector.get_expected_semester_period(date(2025, 10, 15))
    assert start_date == date(2025, 9, 1)
    assert end_date == date(2026, 2, 28)
    print("✓ 正确使用秋季默认模板")

    # 测试1月份（属于上一年秋季）
    start_date, end_date = detector.get_expected_semester_period(date(2025, 1, 15))
    assert start_date == date(2024, 9, 1)
    assert end_date == date(2025, 2, 28)
    print("✓ 正确处理1月份的学期归属")


def test_is_in_semester_gap_near_start():
    """测试学期间隙检测"""
    print("\n测试学期间隙检测...")
    setup_test_data()

    detector = CurrentSemesterDetector()

    # 测试在学期中间（不在间隙）
    is_gap = detector._is_in_semester_gap_near_start(date(2024, 4, 15))
    assert not is_gap
    print("✓ 正确识别非间隙时间")

    # 测试在学期间隙中 - 使用2025年8月（2025秋季学期还不存在）
    is_gap = detector._is_in_semester_gap_near_start(date(2025, 8, 15))
    print(f"学期间隙检测 (2025-08-15): is_gap = {is_gap}")
    assert is_gap
    print("✓ 正确识别学期间隙")

    # 测试接近学期开始
    is_gap = detector._is_in_semester_gap_near_start(date(2025, 2, 20))
    assert not is_gap  # 距离3月1日开始不到15天，但已有学期
    print("✓ 正确处理接近学期开始的情况")


def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况...")
    setup_test_data()

    detector = CurrentSemesterDetector()

    # 测试学期开始日期
    current_semester = detector.detect_current_semester(date(2024, 3, 1))
    assert current_semester is not None
    assert current_semester.name == "2024年春季"
    print("✓ 正确处理学期开始日期")

    # 测试学期结束日期
    current_semester = detector.detect_current_semester(date(2024, 7, 15))
    assert current_semester is not None
    assert current_semester.name == "2024年春季"
    print("✓ 正确处理学期结束日期")

    # 测试学期结束后一天
    current_semester = detector.detect_current_semester(date(2024, 7, 16))
    assert current_semester is None
    print("✓ 正确处理学期结束后的日期")

    # 测试没有任何学期数据的情况
    Semester.objects.all().delete()
    should_create = detector.should_create_semester(date(2025, 4, 15))
    assert should_create
    print("✓ 没有学期数据时正确判断需要创建")


def run_all_tests():
    """运行所有测试"""
    print("开始CurrentSemesterDetector单元测试...\n")

    try:
        test_detect_current_semester()
        test_should_create_semester()
        test_get_expected_semester_period()
        test_calculate_from_default_template()
        test_is_in_semester_gap_near_start()
        test_edge_cases()

        print(f"\n✅ 所有测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
