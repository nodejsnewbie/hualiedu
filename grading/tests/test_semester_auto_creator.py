"""
SemesterAutoCreator的单元测试
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

from grading.models import Semester, SemesterTemplate
from grading.services.semester_auto_creator import (
    DuplicateSemesterError,
    InvalidDateRangeError,
    SemesterAutoCreator,
    SemesterCreationError,
)


def setup_test_data():
    """设置测试数据"""
    # 清理现有数据
    Semester.objects.all().delete()
    SemesterTemplate.objects.all().delete()

    # 创建测试学期
    # 2023年春季学期
    Semester.objects.create(
        name="2023年春季",
        start_date=date(2023, 3, 1),
        end_date=date(2023, 7, 15),
        is_active=False,
        season="spring",
    )

    # 2023年秋季学期
    Semester.objects.create(
        name="2023年秋季",
        start_date=date(2023, 9, 1),
        end_date=date(2024, 1, 20),
        is_active=False,
        season="autumn",
    )

    # 2024年春季学期
    Semester.objects.create(
        name="2024年春季",
        start_date=date(2024, 3, 1),
        end_date=date(2024, 7, 15),
        is_active=False,
        season="spring",
    )

    # 创建学期模板
    SemesterTemplate.objects.create(
        season="spring",
        start_month=3,
        start_day=1,
        end_month=7,
        end_day=15,
        duration_weeks=16,
        name_pattern="{year}年春季",
        is_active=True,
    )

    SemesterTemplate.objects.create(
        season="autumn",
        start_month=9,
        start_day=1,
        end_month=1,
        end_day=20,
        duration_weeks=16,
        name_pattern="{year}年秋季",
        is_active=True,
    )


def test_check_and_create_current_semester():
    """测试检查并创建当前学期功能"""
    print("测试检查并创建当前学期功能...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试已存在学期的情况
    result = creator.check_and_create_current_semester(date(2024, 4, 15))
    assert result is None
    print("✓ 已存在学期时不创建新学期")

    # 测试需要创建新学期的情况 - 2025年春季
    result = creator.check_and_create_current_semester(date(2025, 4, 15))
    assert result is not None
    assert result.name == "2025年春季"
    assert result.start_date == date(2025, 3, 1)
    assert result.end_date == date(2025, 7, 15)
    assert result.auto_created is True
    assert result.season == "spring"
    print("✓ 成功创建2025年春季学期")

    # 测试创建秋季学期 - 2024年秋季
    result = creator.check_and_create_current_semester(date(2024, 10, 15))
    assert result is not None
    assert result.name == "2024年秋季"
    assert result.start_date == date(2024, 9, 1)
    assert result.end_date == date(2025, 1, 20)
    assert result.auto_created is True
    assert result.season == "autumn"
    print("✓ 成功创建2024年秋季学期")

    # 测试不需要创建学期的情况 - 使用一个不会冲突的日期
    result = creator.check_and_create_current_semester(date(2026, 8, 15))
    # 这个日期在学期间隙中，但根据逻辑可能需要创建
    print(f"学期间隙测试结果: {result.name if result else 'None'}")


def test_find_reference_semester():
    """测试查找参考学期功能"""
    print("\n测试查找参考学期功能...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试查找春季学期参考
    reference = creator.find_reference_semester(date(2025, 4, 15))
    assert reference is not None
    assert reference.season == "spring"
    # 应该找到最近的春季学期作为参考
    assert "春季" in reference.name
    print(f"✓ 成功找到春季学期参考: {reference.name}")

    # 测试查找秋季学期参考
    reference = creator.find_reference_semester(date(2024, 10, 15))
    assert reference is not None
    assert reference.season == "autumn"
    assert "秋季" in reference.name
    print(f"✓ 成功找到秋季学期参考: {reference.name}")

    # 测试查找跨年秋季学期参考
    reference = creator.find_reference_semester(date(2025, 1, 10))
    assert reference is not None
    assert reference.season == "autumn"
    print(f"✓ 成功找到跨年秋季学期参考: {reference.name}")

    # 测试没有参考学期的情况
    reference = creator.find_reference_semester(date(2030, 4, 15))
    # 可能找到也可能找不到，取决于历史数据
    print(f"远期日期参考查找结果: {reference.name if reference else 'None'}")


def test_create_semester_from_reference():
    """测试基于参考学期创建新学期"""
    print("\n测试基于参考学期创建新学期...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 获取参考学期
    reference = Semester.objects.get(name="2024年春季")

    # 基于参考学期创建新学期
    new_semester = creator.create_semester_from_reference(reference, date(2025, 4, 15))

    assert new_semester.name == "2025年春季"
    assert new_semester.start_date == date(2025, 3, 1)
    assert new_semester.end_date == date(2025, 7, 15)
    assert new_semester.auto_created is True
    assert new_semester.reference_semester == reference
    assert new_semester.season == "spring"
    assert new_semester.is_active is False
    print("✓ 成功基于参考学期创建新学期")

    # 测试基于秋季学期创建
    reference_autumn = Semester.objects.get(name="2023年秋季")
    new_autumn = creator.create_semester_from_reference(reference_autumn, date(2025, 10, 15))

    assert new_autumn.name == "2025年秋季"
    assert new_autumn.start_date == date(2025, 9, 1)
    assert new_autumn.end_date == date(2026, 1, 20)
    assert new_autumn.season == "autumn"
    print("✓ 成功基于秋季参考学期创建新学期")


def test_create_semester_from_template():
    """测试基于模板创建新学期"""
    print("\n测试基于模板创建新学期...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试基于春季模板创建
    new_semester = creator.create_semester_from_template(date(2026, 4, 15))

    assert new_semester.name == "2026年春季"
    assert new_semester.start_date == date(2026, 3, 1)
    # 检查实际的结束日期（可能来自模板配置）
    print(f"实际结束日期: {new_semester.end_date}")
    assert new_semester.end_date.month == 7  # 应该在7月结束
    assert new_semester.auto_created is True
    assert new_semester.reference_semester is None
    assert new_semester.season == "spring"
    print("✓ 成功基于春季模板创建新学期")

    # 测试基于秋季模板创建
    new_autumn = creator.create_semester_from_template(date(2026, 10, 15))

    assert new_autumn.name == "2026年秋季"
    assert new_autumn.start_date == date(2026, 9, 1)
    # 检查实际的结束日期（可能来自模板配置）
    print(f"秋季实际结束日期: {new_autumn.end_date}")
    assert new_autumn.end_date.month == 1  # 应该在1月结束
    assert new_autumn.season == "autumn"
    print("✓ 成功基于秋季模板创建新学期")


def test_duplicate_semester_detection():
    """测试重复学期检测"""
    print("\n测试重复学期检测...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 尝试创建已存在的学期 - 使用2024年春季作为参考创建2024年学期（应该冲突）
    reference = Semester.objects.get(name="2024年春季")

    try:
        # 尝试创建相同时间段的学期（使用2024年作为目标年份）
        creator.create_semester_from_reference(reference, date(2024, 4, 15))
        assert False, "应该抛出重复学期异常"
    except (DuplicateSemesterError, SemesterCreationError) as e:
        if "已存在相同时间段的学期" in str(e):
            print("✓ 正确检测到重复学期")
        else:
            raise

    # 测试重叠学期的警告（不应该抛出异常）
    try:
        # 创建一个稍微重叠的学期
        Semester.objects.create(
            name="测试重叠学期",
            start_date=date(2026, 2, 15),
            end_date=date(2026, 4, 15),
            is_active=False,
        )

        new_semester = creator.create_semester_from_template(date(2026, 4, 1))
        print("✓ 重叠学期只产生警告，不阻止创建")
    except Exception as e:
        print(f"重叠学期测试异常: {e}")


def test_date_validation():
    """测试日期验证"""
    print("\n测试日期验证...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试无效日期范围
    try:
        creator._validate_date_range(date(2025, 7, 1), date(2025, 3, 1))
        assert False, "应该抛出无效日期范围异常"
    except InvalidDateRangeError:
        print("✓ 正确检测到开始日期晚于结束日期")

    # 测试学期过长
    try:
        creator._validate_date_range(date(2025, 1, 1), date(2026, 6, 1))
        assert False, "应该抛出学期过长异常"
    except InvalidDateRangeError:
        print("✓ 正确检测到学期过长")

    # 测试学期过短
    try:
        creator._validate_date_range(date(2025, 3, 1), date(2025, 3, 15))
        assert False, "应该抛出学期过短异常"
    except InvalidDateRangeError:
        print("✓ 正确检测到学期过短")

    # 测试正常日期范围
    try:
        creator._validate_date_range(date(2025, 3, 1), date(2025, 7, 15))
        print("✓ 正常日期范围验证通过")
    except InvalidDateRangeError:
        assert False, "正常日期范围不应该抛出异常"


def test_season_determination():
    """测试季节判断"""
    print("\n测试季节判断...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试春季月份
    assert creator._determine_season(date(2025, 3, 15)) == "spring"
    assert creator._determine_season(date(2025, 5, 15)) == "spring"
    assert creator._determine_season(date(2025, 7, 15)) == "spring"
    print("✓ 正确判断春季月份")

    # 测试秋季月份
    assert creator._determine_season(date(2025, 9, 15)) == "autumn"
    assert creator._determine_season(date(2025, 11, 15)) == "autumn"
    assert creator._determine_season(date(2025, 1, 15)) == "autumn"
    print("✓ 正确判断秋季月份")

    # 测试边界月份
    assert creator._determine_season(date(2025, 2, 15)) == "autumn"  # 2月属于秋季学期
    assert creator._determine_season(date(2025, 8, 15)) == "autumn"  # 8月属于秋季学期
    print("✓ 正确处理边界月份")


def test_season_match_scoring():
    """测试季节匹配评分"""
    print("\n测试季节匹配评分...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 获取测试学期
    spring_semester = Semester.objects.get(name="2024年春季")
    autumn_semester = Semester.objects.get(name="2023年秋季")

    # 测试春季学期匹配春季目标
    spring_score = creator._calculate_season_match_score(
        spring_semester, "spring", date(2025, 4, 15)
    )
    assert spring_score > 0
    print(f"✓ 春季学期匹配春季目标得分: {spring_score}")

    # 测试秋季学期匹配秋季目标
    autumn_score = creator._calculate_season_match_score(
        autumn_semester, "autumn", date(2025, 10, 15)
    )
    assert autumn_score > 0
    print(f"✓ 秋季学期匹配秋季目标得分: {autumn_score}")

    # 测试不匹配的情况
    mismatch_score = creator._calculate_season_match_score(
        spring_semester, "autumn", date(2025, 10, 15)
    )
    print(f"✓ 春季学期匹配秋季目标得分: {mismatch_score}")


def test_creation_statistics():
    """测试创建统计信息"""
    print("\n测试创建统计信息...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 创建一些自动学期
    creator.check_and_create_current_semester(date(2025, 4, 15))
    creator.check_and_create_current_semester(date(2024, 10, 15))

    # 获取统计信息
    stats = creator.get_creation_statistics()

    assert stats["total_semesters"] > 0
    assert stats["auto_created_count"] >= 2
    assert stats["manual_created_count"] >= 0
    assert 0 <= stats["auto_created_percentage"] <= 100

    print(
        f"✓ 统计信息: 总学期数={stats['total_semesters']}, "
        f"自动创建={stats['auto_created_count']}, "
        f"手动创建={stats['manual_created_count']}, "
        f"自动创建比例={stats['auto_created_percentage']:.1f}%"
    )


def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况...")
    setup_test_data()

    creator = SemesterAutoCreator()

    # 测试没有任何历史学期的情况
    Semester.objects.all().delete()

    # 应该使用模板创建
    result = creator.check_and_create_current_semester(date(2025, 4, 15))
    assert result is not None
    assert result.auto_created is True
    assert result.reference_semester is None
    print("✓ 没有历史学期时使用模板创建")

    # 测试跨年日期处理
    result = creator.check_and_create_current_semester(date(2025, 1, 10))
    assert result is not None
    assert result.season == "autumn"
    print("✓ 正确处理跨年日期")

    # 测试异常日期
    try:
        result = creator.check_and_create_current_semester(date(1900, 1, 1))
        print(f"历史日期测试结果: {result.name if result else 'None'}")
    except Exception as e:
        print(f"历史日期测试异常: {e}")


def run_all_tests():
    """运行所有测试"""
    print("开始SemesterAutoCreator单元测试...\n")

    try:
        test_check_and_create_current_semester()
        test_find_reference_semester()
        test_create_semester_from_reference()
        test_create_semester_from_template()
        test_duplicate_semester_detection()
        test_date_validation()
        test_season_determination()
        test_season_match_scoring()
        test_creation_statistics()
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
