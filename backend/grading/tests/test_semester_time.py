"""
SemesterTimeCalculator 单元测试
"""

import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from grading.services.semester_time import SemesterTimeCalculator


class TestSemesterTimeCalculator(unittest.TestCase):
    """SemesterTimeCalculator测试类"""

    def setUp(self):
        """测试前准备"""
        self.calculator = SemesterTimeCalculator()

    def test_calculate_dates_from_template_season_spring(self):
        """测试春季学期日期计算"""
        start_date, end_date = self.calculator.calculate_dates_from_template_season(2026, "spring")

        self.assertEqual(start_date, date(2026, 3, 1))
        self.assertEqual(end_date, date(2026, 7, 31))

    def test_calculate_dates_from_template_season_autumn(self):
        """测试秋季学期日期计算"""
        start_date, end_date = self.calculator.calculate_dates_from_template_season(2026, "autumn")

        self.assertEqual(start_date, date(2026, 9, 1))
        self.assertEqual(end_date, date(2027, 2, 28))  # 跨年到2月底

    def test_calculate_dates_from_template_season_invalid_season(self):
        """测试无效季节"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_dates_from_template_season(2026, "invalid")

    def test_calculate_dates_from_template(self):
        """测试基于模板计算日期"""
        # 测试春季日期
        spring_date = date(2026, 4, 15)
        start_date, end_date = self.calculator.calculate_dates_from_template(spring_date)

        self.assertEqual(start_date.year, 2026)
        self.assertEqual(start_date.month, 3)  # 春季从3月开始

        # 测试秋季日期
        autumn_date = date(2026, 10, 15)
        start_date, end_date = self.calculator.calculate_dates_from_template(autumn_date)

        self.assertEqual(start_date.year, 2026)
        self.assertEqual(start_date.month, 9)  # 秋季从9月开始

    def test_calculate_semester_duration(self):
        """测试学期持续时间计算"""
        start_date = date(2026, 3, 1)
        end_date = date(2026, 7, 31)

        duration = self.calculator.calculate_semester_duration(start_date, end_date)

        # 3月1日到7月31日大约是22周
        expected_weeks = ((end_date - start_date).days // 7) + 1
        self.assertEqual(duration, expected_weeks)

    def test_calculate_semester_duration_invalid_dates(self):
        """测试无效日期范围"""
        start_date = date(2026, 7, 31)
        end_date = date(2026, 3, 1)  # 结束日期早于开始日期

        with self.assertRaises(ValueError):
            self.calculator.calculate_semester_duration(start_date, end_date)

    def test_adjust_dates_by_duration(self):
        """测试根据持续周数调整日期"""
        start_date = date(2026, 3, 1)
        duration_weeks = 16

        end_date = self.calculator.adjust_dates_by_duration(start_date, duration_weeks)

        # 16周后的日期
        expected_end = start_date + timedelta(weeks=15, days=6)  # 15周+6天=16周
        self.assertEqual(end_date, expected_end)

    def test_adjust_dates_by_duration_invalid_duration(self):
        """测试无效持续周数"""
        start_date = date(2026, 3, 1)

        with self.assertRaises(ValueError):
            self.calculator.adjust_dates_by_duration(start_date, 0)

        with self.assertRaises(ValueError):
            self.calculator.adjust_dates_by_duration(start_date, -5)

    def test_dates_overlap(self):
        """测试日期重叠检测"""
        # 测试重叠情况
        start1, end1 = date(2026, 3, 1), date(2026, 7, 31)
        start2, end2 = date(2026, 6, 1), date(2026, 10, 31)

        self.assertTrue(self.calculator._dates_overlap(start1, end1, start2, end2))

        # 测试不重叠情况
        start1, end1 = date(2026, 3, 1), date(2026, 7, 31)
        start2, end2 = date(2026, 9, 1), date(2027, 1, 31)

        self.assertFalse(self.calculator._dates_overlap(start1, end1, start2, end2))

        # 测试边界情况
        start1, end1 = date(2026, 3, 1), date(2026, 7, 31)
        start2, end2 = date(2026, 8, 1), date(2026, 12, 31)

        self.assertFalse(self.calculator._dates_overlap(start1, end1, start2, end2))

    def test_detect_season_from_date(self):
        """测试从日期检测季节"""
        # 测试春季日期
        spring_dates = [
            date(2026, 2, 15),
            date(2026, 3, 1),
            date(2026, 5, 15),
            date(2026, 7, 31),
        ]

        for test_date in spring_dates:
            season = self.calculator._detect_season_from_date(test_date)
            self.assertEqual(season, "spring", f"日期 {test_date} 应该是春季")

        # 测试秋季日期
        autumn_dates = [
            date(2026, 1, 15),
            date(2026, 8, 1),
            date(2026, 9, 15),
            date(2026, 12, 31),
        ]

        for test_date in autumn_dates:
            season = self.calculator._detect_season_from_date(test_date)
            self.assertEqual(season, "autumn", f"日期 {test_date} 应该是秋季")

    def test_adjust_date_to_year(self):
        """测试日期年份调整"""
        original_date = date(2025, 3, 15)
        adjusted_date = self.calculator._adjust_date_to_year(original_date, 2026)

        self.assertEqual(adjusted_date, date(2026, 3, 15))

    def test_adjust_date_to_year_leap_year(self):
        """测试闰年日期调整"""
        # 2月29日调整到非闰年
        leap_date = date(2024, 2, 29)  # 2024是闰年
        adjusted_date = self.calculator._adjust_date_to_year(leap_date, 2025)  # 2025不是闰年

        self.assertEqual(adjusted_date, date(2025, 2, 28))

    def test_handle_invalid_date_spring(self):
        """测试春季无效日期处理"""
        template_config = {
            "start_month": 2,
            "start_day": 30,  # 2月没有30日
            "end_month": 2,
            "end_day": 30,
        }

        start_date, end_date = self.calculator._handle_invalid_date(
            2025, "spring", template_config, ValueError("Invalid date")
        )

        # 应该回退到安全的日期
        self.assertEqual(start_date.month, 2)
        self.assertEqual(end_date.month, 2)
        self.assertTrue(start_date <= end_date)

    def test_handle_invalid_date_autumn(self):
        """测试秋季无效日期处理"""
        template_config = {
            "start_month": 9,
            "start_day": 31,  # 9月没有31日
            "end_month": 2,
            "end_day": 30,
        }

        start_date, end_date = self.calculator._handle_invalid_date(
            2025, "autumn", template_config, ValueError("Invalid date")
        )

        # 应该回退到安全的日期
        self.assertEqual(start_date.month, 9)
        self.assertTrue(start_date <= end_date)

    def test_get_semester_templates_default(self):
        """测试获取默认模板"""
        templates = self.calculator.get_semester_templates()

        # 应该包含春季和秋季模板
        self.assertIn("spring", templates)
        self.assertIn("autumn", templates)

        # 检查春季模板
        spring_template = templates["spring"]
        self.assertEqual(spring_template["start_month"], 3)
        self.assertEqual(spring_template["end_month"], 7)

        # 检查秋季模板
        autumn_template = templates["autumn"]
        self.assertEqual(autumn_template["start_month"], 9)
        self.assertEqual(autumn_template["end_month"], 1)

    @patch("grading.services.semester_time.SemesterTemplate")
    def test_get_semester_templates_from_database(self, mock_template):
        """测试从数据库获取模板"""
        # 模拟数据库模板
        mock_db_template = Mock()
        mock_db_template.season = "spring"
        mock_db_template.start_month = 2
        mock_db_template.start_day = 15
        mock_db_template.end_month = 6
        mock_db_template.end_day = 15
        mock_db_template.duration_weeks = 20
        mock_db_template.name_pattern = "{year}年{season}学期"

        mock_template.objects.filter.return_value = [mock_db_template]

        templates = self.calculator.get_semester_templates()

        # 应该使用数据库中的模板
        spring_template = templates["spring"]
        self.assertEqual(spring_template["start_month"], 2)
        self.assertEqual(spring_template["start_day"], 15)
        self.assertEqual(spring_template["source"], "database")

    def test_suggest_alternative_dates(self):
        """测试建议替代日期"""
        preferred_start = date(2026, 3, 1)
        suggestions = self.calculator.suggest_alternative_dates(preferred_start, "spring")

        # 应该返回建议列表
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

        # 每个建议应该包含必要的字段
        for suggestion in suggestions:
            self.assertIn("start_date", suggestion)
            self.assertIn("end_date", suggestion)
            self.assertIn("conflicts", suggestion)
            self.assertIn("conflict_semesters", suggestion)

            # 日期应该是有效的
            self.assertIsInstance(suggestion["start_date"], date)
            self.assertIsInstance(suggestion["end_date"], date)
            self.assertTrue(suggestion["start_date"] <= suggestion["end_date"])


if __name__ == "__main__":
    unittest.main()
