"""
当前学期检测器模块

提供学期检测和判断功能，包括：
- 检测当前学期
- 判断是否需要创建新学期
- 计算预期学期时间段
"""

from datetime import date, timedelta
from typing import Optional, Tuple

from django.db.models import Q

from grading.models import Semester


class CurrentSemesterDetector:
    """当前学期检测器

    负责检测当前日期对应的学期，判断是否需要创建新学期，
    以及计算预期的学期时间段。
    """

    def __init__(self):
        """初始化检测器"""
        pass

    def detect_current_semester(self, current_date: date = None) -> Optional[Semester]:
        """检测当前学期

        根据当前日期检测对应的学期。如果当前日期在某个学期的时间范围内，
        返回该学期；如果不在任何学期范围内，返回None。

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            当前学期对象，如果没有找到则返回None
        """
        if current_date is None:
            current_date = date.today()

        # 查找当前日期在范围内的学期
        current_semesters = Semester.objects.filter(
            start_date__lte=current_date, end_date__gte=current_date
        ).order_by("-start_date")

        if current_semesters.exists():
            # 如果存在多个可能的当前学期，选择最近开始的学期
            return current_semesters.first()

        return None

    def should_create_semester(self, current_date: date = None) -> bool:
        """判断是否需要创建学期

        检查当前日期是否需要创建新学期。如果当前日期不在任何现有学期范围内，
        且根据历史模式应该存在学期，则返回True。

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            是否需要创建学期
        """
        if current_date is None:
            current_date = date.today()

        # 如果已经存在当前学期，不需要创建
        if self.detect_current_semester(current_date) is not None:
            return False

        # 检查是否在预期的学期时间段内
        try:
            expected_start, expected_end = self.get_expected_semester_period(current_date)

            # 如果当前日期在预期的学期时间段内，且没有对应学期，则需要创建
            if expected_start <= current_date <= expected_end:
                return True

        except Exception:
            # 如果无法计算预期时间段，使用保守策略
            return True

        # 检查是否在学期间隙中，且即将开始新学期
        return self._is_in_semester_gap_near_start(current_date)

    def get_expected_semester_period(self, current_date: date) -> Tuple[date, date]:
        """获取预期的学期时间段

        根据当前日期和历史学期模式，计算当前日期应该对应的学期时间段。

        Args:
            current_date: 当前日期

        Returns:
            预期的学期开始和结束日期元组

        Raises:
            ValueError: 如果无法计算预期时间段
        """
        # 首先尝试根据历史学期模式计算
        expected_period = self._calculate_from_historical_pattern(current_date)
        if expected_period:
            return expected_period

        # 如果没有历史模式，使用默认的学期模板
        return self._calculate_from_default_template(current_date)

    def _calculate_from_historical_pattern(self, current_date: date) -> Optional[Tuple[date, date]]:
        """根据历史学期模式计算预期时间段

        Args:
            current_date: 当前日期

        Returns:
            预期的学期时间段，如果无法计算则返回None
        """
        # 首先确定当前日期应该属于哪个季节的学期
        if 3 <= current_date.month <= 7:
            # 春季学期，查找去年春季学期作为参考
            season_months = [3, 4, 5, 6, 7]
        else:
            # 秋季学期，查找去年秋季学期作为参考
            season_months = [8, 9, 10, 11, 12, 1, 2]

        # 查找历史学期模式，优先查找去年，然后查找前年
        for year_offset in [1, 2]:
            reference_year = current_date.year - year_offset

            # 查找参考年的学期
            reference_semesters = Semester.objects.filter(
                Q(start_date__year=reference_year) | Q(end_date__year=reference_year)
            ).order_by("start_date")

            if not reference_semesters.exists():
                continue

            # 找到同季节的学期
            best_match = None
            for semester in reference_semesters:
                # 检查学期是否包含目标季节的月份
                semester_months = []
                current_month = semester.start_date.month
                end_month = semester.end_date.month

                if semester.start_date.year == semester.end_date.year:
                    # 同年学期
                    semester_months = list(range(current_month, end_month + 1))
                else:
                    # 跨年学期
                    semester_months = list(range(current_month, 13)) + list(range(1, end_month + 1))

                # 检查是否有重叠的月份
                if any(month in season_months for month in semester_months):
                    best_match = semester
                    break

            if best_match:
                # 将参考学期的日期转换为当前年份
                years_diff = current_date.year - reference_year
                start_date = best_match.start_date.replace(
                    year=best_match.start_date.year + years_diff
                )

                # 处理跨年的情况
                if best_match.end_date.year > best_match.start_date.year:
                    end_date = best_match.end_date.replace(
                        year=best_match.end_date.year + years_diff
                    )
                else:
                    end_date = best_match.end_date.replace(
                        year=best_match.end_date.year + years_diff
                    )

                return (start_date, end_date)

        return None

    def _calculate_from_default_template(self, current_date: date) -> Tuple[date, date]:
        """根据默认模板计算预期时间段

        Args:
            current_date: 当前日期

        Returns:
            预期的学期时间段
        """
        # 根据月份判断是春季还是秋季学期
        if 3 <= current_date.month <= 7:
            # 春季学期：3月-7月
            start_date = date(current_date.year, 3, 1)
            end_date = date(current_date.year, 7, 31)
        else:
            # 秋季学期：9月-次年2月
            if current_date.month >= 9:
                # 9-12月，属于当年秋季学期
                start_date = date(current_date.year, 9, 1)
                end_date = date(current_date.year + 1, 2, 28)  # 2月底
            else:
                # 1-2月，属于上一年的秋季学期
                start_date = date(current_date.year - 1, 9, 1)
                end_date = date(current_date.year, 2, 28)  # 2月底

        return (start_date, end_date)

    def _is_in_semester_gap_near_start(self, current_date: date) -> bool:
        """检查是否在学期间隙中且接近新学期开始

        Args:
            current_date: 当前日期

        Returns:
            是否在学期间隙中且接近新学期开始
        """
        # 查找最近的学期
        recent_semesters = Semester.objects.filter(
            Q(start_date__lte=current_date + timedelta(days=60))
            | Q(end_date__gte=current_date - timedelta(days=60))
        ).order_by("-start_date")

        if not recent_semesters.exists():
            return True  # 如果没有任何学期，应该创建

        # 检查是否在学期间隙中
        in_any_semester = False
        for semester in recent_semesters:
            # 如果当前日期在学期范围内，不在间隙中
            if semester.start_date <= current_date <= semester.end_date:
                in_any_semester = True
                break

        if in_any_semester:
            return False

        # 在学期间隙中，检查是否应该创建新学期
        # 检查是否有即将开始的学期（15天内）
        upcoming_semesters = Semester.objects.filter(
            start_date__gt=current_date, start_date__lte=current_date + timedelta(days=15)
        )

        if upcoming_semesters.exists():
            return False  # 已经有即将开始的学期，不需要创建

        # 检查是否应该有新学期开始
        try:
            expected_start, expected_end = self.get_expected_semester_period(current_date)

            # 如果当前日期在预期学期范围内，或接近预期开始日期
            if expected_start <= current_date <= expected_end:
                return True

            # 如果距离预期开始日期不超过30天
            days_to_expected_start = abs((current_date - expected_start).days)
            if days_to_expected_start <= 30:
                return True

        except Exception:
            # 如果无法计算预期时间段，保守地返回True
            return True

        return False
