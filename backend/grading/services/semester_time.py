"""
学期时间计算引擎
负责计算学期的开始和结束日期
"""

from datetime import date, timedelta
from typing import Dict, Optional, Tuple

from grading.models import Semester, SemesterTemplate


class SemesterTimeCalculator:
    """学期时间计算引擎"""

    def __init__(self):
        # 默认学期模板配置
        self.default_templates = {
            "spring": {
                "start_month": 3,
                "start_day": 1,
                "end_month": 7,
                "end_day": 31,
                "duration_weeks": 18,
            },
            "autumn": {
                "start_month": 9,
                "start_day": 1,
                "end_month": 2,  # 次年2月
                "end_day": 28,  # 2月底
                "duration_weeks": 18,
            },
        }

    def calculate_dates_from_reference(
        self, reference: Semester, target_year: int
    ) -> Tuple[date, date]:
        """
        基于参考学期计算新学期日期

        Args:
            reference: 参考学期对象
            target_year: 目标年份

        Returns:
            (开始日期, 结束日期)
        """
        if not reference:
            raise ValueError("参考学期不能为空")

        try:
            # 使用Semester模型的get_next_year_dates方法
            next_start, next_end = reference.get_next_year_dates()

            # 调整到目标年份
            year_diff = target_year - reference.start_date.year
            if year_diff != 1:
                # 如果不是下一年，需要重新计算
                start_date = self._adjust_date_to_year(reference.start_date, target_year)
                end_date = self._adjust_date_to_year(reference.end_date, target_year)

                # 处理跨年情况
                if reference.end_date.year > reference.start_date.year:
                    end_date = self._adjust_date_to_year(reference.end_date, target_year + 1)

                return start_date, end_date
            else:
                return next_start, next_end

        except Exception as e:
            # 如果计算失败，使用模板方法
            season = reference.get_season()
            return self.calculate_dates_from_template_season(target_year, season)

    def calculate_dates_from_template(self, target_date: date) -> Tuple[date, date]:
        """
        基于模板计算学期日期

        Args:
            target_date: 目标日期

        Returns:
            (开始日期, 结束日期)
        """
        # 根据日期判断季节
        season = self._detect_season_from_date(target_date)

        # 尝试从数据库获取模板
        template = SemesterTemplate.get_template_for_season(season)

        if template:
            try:
                return template.generate_semester_dates(target_date.year)
            except ValueError:
                # 如果模板生成失败，使用默认模板
                pass

        # 使用默认模板
        return self.calculate_dates_from_template_season(target_date.year, season)

    def calculate_dates_from_template_season(self, year: int, season: str) -> Tuple[date, date]:
        """
        基于季节和年份计算学期日期

        Args:
            year: 年份
            season: 季节 ('spring' 或 'autumn')

        Returns:
            (开始日期, 结束日期)
        """
        template_config = self.default_templates.get(season)
        if not template_config:
            raise ValueError(f"不支持的季节: {season}")

        try:
            start_date = date(year, template_config["start_month"], template_config["start_day"])

            # 处理跨年情况
            end_year = year
            if season == "autumn" and template_config["end_month"] <= 7:
                end_year = year + 1

            end_date = date(end_year, template_config["end_month"], template_config["end_day"])

            return start_date, end_date

        except ValueError as e:
            # 处理无效日期（如2月30日）
            return self._handle_invalid_date(year, season, template_config, e)

    def get_semester_templates(self) -> Dict[str, Dict]:
        """
        获取学期模板配置

        Returns:
            模板配置字典
        """
        templates = {}

        # 从数据库获取活跃模板
        db_templates = SemesterTemplate.objects.filter(is_active=True)

        for template in db_templates:
            templates[template.season] = {
                "start_month": template.start_month,
                "start_day": template.start_day,
                "end_month": template.end_month,
                "end_day": template.end_day,
                "duration_weeks": template.duration_weeks,
                "name_pattern": template.name_pattern,
                "source": "database",
            }

        # 补充默认模板（如果数据库中没有）
        for season, config in self.default_templates.items():
            if season not in templates:
                templates[season] = {**config, "source": "default"}

        return templates

    def calculate_semester_duration(self, start_date: date, end_date: date) -> int:
        """
        计算学期持续周数

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            持续周数
        """
        if start_date >= end_date:
            raise ValueError("开始日期必须早于结束日期")

        delta = end_date - start_date
        return (delta.days // 7) + 1

    def adjust_dates_by_duration(self, start_date: date, duration_weeks: int) -> date:
        """
        根据持续周数调整结束日期

        Args:
            start_date: 开始日期
            duration_weeks: 持续周数

        Returns:
            调整后的结束日期
        """
        if duration_weeks <= 0:
            raise ValueError("持续周数必须大于0")

        # 计算结束日期（周数-1是因为第一周也算一周）
        end_date = start_date + timedelta(weeks=duration_weeks - 1, days=6)
        return end_date

    def find_semester_conflicts(
        self, start_date: date, end_date: date, exclude_id: Optional[int] = None
    ) -> list:
        """
        查找与指定日期范围冲突的学期

        Args:
            start_date: 开始日期
            end_date: 结束日期
            exclude_id: 要排除的学期ID

        Returns:
            冲突的学期列表
        """
        conflicts = []

        query = Semester.objects.all()
        if exclude_id:
            query = query.exclude(id=exclude_id)

        for semester in query:
            # 检查日期范围是否重叠
            if self._dates_overlap(start_date, end_date, semester.start_date, semester.end_date):
                conflicts.append(semester)

        return conflicts

    def suggest_alternative_dates(self, preferred_start: date, season: str) -> list:
        """
        建议替代的学期日期

        Args:
            preferred_start: 首选开始日期
            season: 季节

        Returns:
            建议的日期范围列表
        """
        suggestions = []

        # 获取模板配置
        template_config = self.default_templates.get(season, self.default_templates["spring"])

        # 生成几个可能的开始日期
        base_year = preferred_start.year

        for year_offset in [-1, 0, 1]:
            for day_offset in [0, 7, -7, 14, -14]:  # 前后两周的调整
                try:
                    test_year = base_year + year_offset
                    test_start = date(
                        test_year, template_config["start_month"], template_config["start_day"]
                    )
                    test_start += timedelta(days=day_offset)

                    # 计算对应的结束日期
                    end_year = test_year
                    if season == "autumn" and template_config["end_month"] <= 7:
                        end_year = test_year + 1

                    test_end = date(
                        end_year, template_config["end_month"], template_config["end_day"]
                    )

                    # 检查是否有冲突
                    conflicts = self.find_semester_conflicts(test_start, test_end)

                    suggestions.append(
                        {
                            "start_date": test_start,
                            "end_date": test_end,
                            "conflicts": len(conflicts),
                            "conflict_semesters": [s.name for s in conflicts],
                        }
                    )

                except ValueError:
                    # 跳过无效日期
                    continue

        # 按冲突数量排序，无冲突的在前
        suggestions.sort(
            key=lambda x: (x["conflicts"], abs((x["start_date"] - preferred_start).days))
        )

        return suggestions[:5]  # 返回前5个建议

    def _adjust_date_to_year(self, original_date: date, target_year: int) -> date:
        """调整日期到目标年份"""
        try:
            return original_date.replace(year=target_year)
        except ValueError:
            # 处理2月29日的情况
            if original_date.month == 2 and original_date.day == 29:
                return date(target_year, 2, 28)
            raise

    def _detect_season_from_date(self, target_date: date) -> str:
        """根据日期检测季节"""
        month = target_date.month
        if 3 <= month <= 7:
            return "spring"
        else:
            return "autumn"

    def _handle_invalid_date(
        self, year: int, season: str, template_config: dict, error: ValueError
    ) -> Tuple[date, date]:
        """处理无效日期的情况"""
        # 尝试调整到月末
        try:
            if season == "spring":
                start_date = date(year, template_config["start_month"], 1)
                # 找到该月的最后一天
                if template_config["end_month"] == 2:
                    end_date = date(year, 2, 28)
                else:
                    end_date = date(
                        year, template_config["end_month"], min(template_config["end_day"], 30)
                    )
            else:
                start_date = date(year, template_config["start_month"], 1)
                end_year = year + 1 if template_config["end_month"] <= 7 else year
                end_date = date(
                    end_year, template_config["end_month"], min(template_config["end_day"], 30)
                )

            return start_date, end_date

        except ValueError:
            # 如果还是失败，使用最保守的日期
            if season == "spring":
                return date(year, 3, 1), date(year, 7, 30)
            else:
                return date(year, 9, 1), date(year + 1, 1, 30)

    def _dates_overlap(self, start1: date, end1: date, start2: date, end2: date) -> bool:
        """检查两个日期范围是否重叠"""
        return not (end1 < start2 or end2 < start1)
