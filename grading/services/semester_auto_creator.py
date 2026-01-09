"""
自动学期创建服务模块

提供学期自动创建的核心功能，包括：
- 检查并创建当前学期
- 查找参考学期
- 基于参考学期或模板创建新学期
- 重复创建检测和防护
"""

import logging
from datetime import date
from typing import Optional, Tuple

from django.db import IntegrityError, transaction
from django.utils import timezone

from grading.exceptions import (
    DuplicateSemesterError,
    InvalidDateRangeError,
    SemesterCreationError,
    TemplateNotFoundError,
    handle_semester_exceptions,
)
from grading.models import Semester, SemesterTemplate
from grading.services.semester_detector import CurrentSemesterDetector
from grading.services.semester_naming import SemesterNamingEngine
from grading.services.semester_time import SemesterTimeCalculator

# 配置日志
logger = logging.getLogger(__name__)


class SemesterAutoCreator:
    """自动学期创建服务

    负责协调各个组件，实现学期的自动创建功能。
    包括检测当前学期、查找参考学期、创建新学期等核心逻辑。
    """

    def __init__(self):
        """初始化自动创建服务"""
        self.detector = CurrentSemesterDetector()
        self.naming_engine = SemesterNamingEngine()
        self.time_calculator = SemesterTimeCalculator()

    @handle_semester_exceptions(default_return=None)
    def check_and_create_current_semester(self, current_date: date = None) -> Optional[Semester]:
        """检查并创建当前学期

        这是主要的入口方法，检查当前日期是否需要创建学期，
        如果需要则自动创建并返回新学期。

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            新创建的学期对象，如果不需要创建则返回None

        Raises:
            SemesterCreationError: 创建过程中发生错误
        """
        if current_date is None:
            current_date = date.today()

        logger.info(f"开始检查是否需要为日期 {current_date} 创建学期")

        try:
            # 检查是否已存在当前学期
            existing_semester = self.detector.detect_current_semester(current_date)
            if existing_semester:
                logger.info(f"已存在当前学期: {existing_semester.name}")
                return None

            # 检查是否需要创建学期
            if not self.detector.should_create_semester(current_date):
                logger.info(f"当前日期 {current_date} 不需要创建学期")
                return None

            # 尝试查找参考学期
            reference_semester = self.find_reference_semester(current_date)

            try:
                if reference_semester:
                    logger.info(f"找到参考学期: {reference_semester.name}")
                    new_semester = self.create_semester_from_reference(
                        reference_semester, current_date
                    )
                else:
                    logger.info("未找到参考学期，使用模板创建")
                    new_semester = self.create_semester_from_template(current_date)
            except DuplicateSemesterError:
                # 如果学期已存在，检查是否是我们需要的学期
                expected_start, expected_end = self.detector.get_expected_semester_period(
                    current_date
                )
                existing = Semester.objects.filter(
                    start_date=expected_start, end_date=expected_end
                ).first()
                if existing:
                    logger.info(f"学期已存在: {existing.name}")
                    return None
                else:
                    raise

            logger.info(
                f"成功创建学期: {new_semester.name} ({new_semester.start_date} - {new_semester.end_date})"
            )
            return new_semester

        except Exception as e:
            logger.error(f"创建学期失败: {str(e)}")
            raise SemesterCreationError(f"创建学期失败: {str(e)}") from e

    def find_reference_semester(self, target_date: date) -> Optional[Semester]:
        """查找参考学期（上一年同期）

        根据目标日期查找上一年或前几年的同期学期作为参考。
        优先查找上一年，如果没有则查找前两年。

        Args:
            target_date: 目标日期

        Returns:
            参考学期对象，如果没有找到则返回None
        """
        logger.info(f"查找日期 {target_date} 的参考学期")

        # 确定目标季节
        target_season = self._determine_season(target_date)
        logger.info(f"目标季节: {target_season}")

        # 查找历史学期，优先查找上一年，然后查找前两年
        for year_offset in [1, 2, 3]:
            reference_year = target_date.year - year_offset
            logger.info(f"查找 {reference_year} 年的 {target_season} 学期")

            # 查找该年的学期
            reference_semesters = Semester.objects.filter(
                start_date__year__in=[reference_year, reference_year - 1, reference_year + 1]
            ).order_by("start_date")

            if not reference_semesters.exists():
                logger.info(f"{reference_year} 年没有找到任何学期")
                continue

            # 找到最匹配的学期
            best_match = self._find_best_season_match(
                reference_semesters, target_season, target_date
            )

            if best_match:
                logger.info(f"找到最佳匹配学期: {best_match.name}")
                return best_match

        logger.info("未找到合适的参考学期")
        return None

    @handle_semester_exceptions()
    def create_semester_from_reference(
        self, reference_semester: Semester, target_date: date = None
    ) -> Semester:
        """基于参考学期创建新学期

        使用参考学期的模式创建新学期，包括命名规则和时间计算。

        Args:
            reference_semester: 参考学期
            target_date: 目标日期，用于确定新学期的年份

        Returns:
            新创建的学期对象

        Raises:
            SemesterCreationError: 创建过程中发生错误
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"基于参考学期 {reference_semester.name} 创建新学期")

        try:
            with transaction.atomic():
                # 计算新学期的日期
                start_date, end_date = self.time_calculator.calculate_dates_from_reference(
                    reference_semester, target_date.year
                )

                # 验证日期范围
                self._validate_date_range(start_date, end_date)

                # 检查是否已存在相同时间段的学期
                self._check_duplicate_semester(start_date, end_date)

                # 生成新学期名称
                new_name = self.naming_engine.generate_name_from_reference(
                    reference_semester.name, start_date.year
                )

                # 确定季节
                season = self.naming_engine.detect_semester_season(start_date)

                # 创建新学期
                new_semester = Semester.objects.create(
                    name=new_name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=False,  # 新创建的学期默认为非活跃状态
                    auto_created=True,
                    reference_semester=reference_semester,
                    season=season,
                )

                logger.info(f"成功创建学期: {new_semester.name}")
                return new_semester

        except IntegrityError as e:
            logger.error(f"数据库完整性错误: {str(e)}")
            raise DuplicateSemesterError("学期已存在或违反唯一性约束") from e
        except Exception as e:
            logger.error(f"创建学期失败: {str(e)}")
            raise SemesterCreationError(f"创建学期失败: {str(e)}") from e

    @handle_semester_exceptions()
    def create_semester_from_template(self, target_date: date) -> Semester:
        """基于模板创建新学期

        当没有参考学期时，使用预设的学期模板创建新学期。

        Args:
            target_date: 目标日期

        Returns:
            新创建的学期对象

        Raises:
            SemesterCreationError: 创建过程中发生错误
        """
        logger.info(f"基于模板为日期 {target_date} 创建学期")

        try:
            with transaction.atomic():
                # 计算新学期的日期
                start_date, end_date = self.time_calculator.calculate_dates_from_template(
                    target_date
                )

                # 验证日期范围
                self._validate_date_range(start_date, end_date)

                # 检查是否已存在相同时间段的学期
                self._check_duplicate_semester(start_date, end_date)

                # 生成默认名称
                new_name = self.naming_engine.generate_default_name(start_date)

                # 确定季节
                season = self.naming_engine.detect_semester_season(start_date)

                # 创建新学期
                new_semester = Semester.objects.create(
                    name=new_name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=False,  # 新创建的学期默认为非活跃状态
                    auto_created=True,
                    reference_semester=None,
                    season=season,
                )

                logger.info(f"成功基于模板创建学期: {new_semester.name}")
                return new_semester

        except IntegrityError as e:
            logger.error(f"数据库完整性错误: {str(e)}")
            raise DuplicateSemesterError("学期已存在或违反唯一性约束") from e
        except Exception as e:
            logger.error(f"基于模板创建学期失败: {str(e)}")
            raise SemesterCreationError(f"基于模板创建学期失败: {str(e)}") from e

    def _determine_season(self, target_date: date) -> str:
        """确定目标日期对应的季节

        根据实际学期安排：
        - 春季学期：3月-7月
        - 秋季学期：8/9月-次年2月

        Args:
            target_date: 目标日期

        Returns:
            季节字符串 ('spring' 或 'autumn')
        """
        if 3 <= target_date.month <= 7:
            return "spring"
        else:
            # 8月-12月和1月-2月都属于秋季学期
            return "autumn"

    def _find_best_season_match(
        self, semesters, target_season: str, target_date: date
    ) -> Optional[Semester]:
        """在给定的学期列表中找到最匹配的季节学期

        Args:
            semesters: 学期查询集
            target_season: 目标季节
            target_date: 目标日期

        Returns:
            最匹配的学期，如果没有找到则返回None
        """
        best_match = None
        best_score = -1

        for semester in semesters:
            score = self._calculate_season_match_score(semester, target_season, target_date)
            if score > best_score:
                best_score = score
                best_match = semester

        # 只有当匹配分数大于0时才返回结果
        return best_match if best_score > 0 else None

    def _calculate_season_match_score(
        self, semester: Semester, target_season: str, target_date: date
    ) -> int:
        """计算学期与目标季节的匹配分数

        Args:
            semester: 学期对象
            target_season: 目标季节
            target_date: 目标日期

        Returns:
            匹配分数，分数越高匹配度越好
        """
        score = 0

        # 检查学期的季节属性
        if hasattr(semester, "season") and semester.season:
            if semester.season == target_season:
                score += 10

        # 根据开始月份判断季节匹配度
        semester_season = self.naming_engine.detect_semester_season(semester.start_date)
        if semester_season == target_season:
            score += 8

        # 检查月份范围的重叠
        if target_season == "spring":
            target_months = [3, 4, 5, 6, 7]
        else:
            target_months = [9, 10, 11, 12, 1]

        # 计算学期包含的月份
        semester_months = []
        current_date = semester.start_date
        while current_date <= semester.end_date:
            semester_months.append(current_date.month)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        # 计算重叠月份数量
        overlap_months = len(set(semester_months) & set(target_months))
        score += overlap_months

        return score

    def _validate_date_range(self, start_date: date, end_date: date):
        """验证日期范围的有效性

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Raises:
            InvalidDateRangeError: 日期范围无效
        """
        if start_date >= end_date:
            raise InvalidDateRangeError(f"开始日期 {start_date} 必须早于结束日期 {end_date}")

        # 检查学期长度是否合理（不超过1年，不少于1个月）
        duration = (end_date - start_date).days
        if duration > 365:
            raise InvalidDateRangeError(f"学期长度过长: {duration} 天")
        if duration < 30:
            raise InvalidDateRangeError(f"学期长度过短: {duration} 天")

    def _check_duplicate_semester(self, start_date: date, end_date: date):
        """检查是否存在重复的学期

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Raises:
            DuplicateSemesterError: 存在重复学期
        """
        # 检查是否存在完全相同时间段的学期
        existing_exact = Semester.objects.filter(start_date=start_date, end_date=end_date).exists()

        if existing_exact:
            raise DuplicateSemesterError(f"已存在相同时间段的学期: {start_date} - {end_date}")

        # 检查是否存在重叠的学期
        overlapping = Semester.objects.filter(
            start_date__lt=end_date, end_date__gt=start_date
        ).exists()

        if overlapping:
            logger.warning(f"存在时间重叠的学期: {start_date} - {end_date}")
            # 注意：这里只是警告，不抛出异常，因为可能存在合理的重叠情况

    def get_creation_statistics(self) -> dict:
        """获取自动创建的统计信息

        Returns:
            包含统计信息的字典
        """
        total_auto_created = Semester.objects.filter(auto_created=True).count()
        total_semesters = Semester.objects.count()

        return {
            "total_semesters": total_semesters,
            "auto_created_count": total_auto_created,
            "manual_created_count": total_semesters - total_auto_created,
            "auto_created_percentage": (
                (total_auto_created / total_semesters * 100) if total_semesters > 0 else 0
            ),
        }
