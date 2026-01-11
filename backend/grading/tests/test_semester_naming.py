"""
SemesterNamingEngine 单元测试
"""

import unittest
from datetime import date

from grading.services.semester_naming import SemesterNamingEngine


class TestSemesterNamingEngine(unittest.TestCase):
    """SemesterNamingEngine测试类"""

    def setUp(self):
        """测试前准备"""
        self.engine = SemesterNamingEngine()

    def test_generate_name_from_reference_basic(self):
        """测试基本的参考名称生成"""
        # 测试标准格式
        result = self.engine.generate_name_from_reference("2025年秋季", 2026)
        self.assertEqual(result, "2026年秋季")

        result = self.engine.generate_name_from_reference("2024年春季", 2025)
        self.assertEqual(result, "2025年春季")

    def test_generate_name_from_reference_variations(self):
        """测试各种命名格式的处理"""
        # 测试不同的年份格式
        result = self.engine.generate_name_from_reference("2025秋季", 2026)
        self.assertEqual(result, "2026秋季")

        # 测试带学期的格式
        result = self.engine.generate_name_from_reference("2025年秋季学期", 2026)
        self.assertEqual(result, "2026年秋季学期")

    def test_generate_name_from_reference_edge_cases(self):
        """测试边界情况"""
        # 测试空字符串
        result = self.engine.generate_name_from_reference("", 2026)
        self.assertIn("2026年", result)

        # 测试None
        result = self.engine.generate_name_from_reference(None, 2026)
        self.assertIn("2026年", result)

        # 测试无年份的名称
        result = self.engine.generate_name_from_reference("春季学期", 2026)
        self.assertEqual(result, "2026年春季")

    def test_generate_default_name(self):
        """测试默认名称生成"""
        # 测试春季日期
        spring_date = date(2026, 3, 15)
        result = self.engine.generate_default_name(spring_date)
        self.assertEqual(result, "2026年春季")

        # 测试秋季日期
        autumn_date = date(2026, 9, 15)
        result = self.engine.generate_default_name(autumn_date)
        self.assertEqual(result, "2026年秋季")

    def test_detect_semester_season(self):
        """测试季节检测"""
        # 测试春季月份（3月-7月）
        spring_dates = [
            date(2025, 3, 1),  # 3月开始
            date(2025, 3, 15),
            date(2025, 6, 30),
            date(2025, 7, 15),
        ]
        for test_date in spring_dates:
            result = self.engine.detect_semester_season(test_date)
            self.assertEqual(result, "spring", f"日期 {test_date} 应该是春季")

        # 测试秋季月份（8月-2月，跨年）
        autumn_dates = [
            date(2025, 1, 15),  # 1月属于秋季学期
            date(2025, 2, 15),  # 2月属于秋季学期
            date(2025, 8, 1),  # 8月开始秋季学期
            date(2025, 9, 15),
            date(2025, 12, 31),
        ]
        for test_date in autumn_dates:
            result = self.engine.detect_semester_season(test_date)
            self.assertEqual(result, "autumn", f"日期 {test_date} 应该是秋季")

    def test_detect_season_from_name(self):
        """测试从名称中检测季节"""
        # 测试中文季节
        test_cases = [
            ("2025年春季", "spring"),
            ("2025年秋季", "autumn"),
            ("春季学期", "spring"),
            ("秋季学期", "autumn"),
            ("2025春", "spring"),
            ("2025秋", "autumn"),
        ]

        for name, expected_season in test_cases:
            result = self.engine._detect_season_from_name(name)
            self.assertEqual(result, expected_season, f"名称 '{name}' 应该检测为 {expected_season}")

        # 测试英文季节
        english_cases = [
            ("Spring 2025", "spring"),
            ("Autumn 2025", "autumn"),
            ("Fall 2025", "autumn"),
        ]

        for name, expected_season in english_cases:
            result = self.engine._detect_season_from_name(name)
            self.assertEqual(result, expected_season, f"名称 '{name}' 应该检测为 {expected_season}")

        # 测试无法检测的情况
        result = self.engine._detect_season_from_name("2025年学期")
        self.assertIsNone(result)

    def test_extract_year_from_name(self):
        """测试从名称中提取年份"""
        test_cases = [
            ("2025年春季", 2025),
            ("2024年秋季学期", 2024),
            ("2026春", 2026),
            ("Spring 2027", 2027),
        ]

        for name, expected_year in test_cases:
            result = self.engine.extract_year_from_name(name)
            self.assertEqual(result, expected_year, f"名称 '{name}' 应该提取年份 {expected_year}")

        # 测试无年份的情况
        result = self.engine.extract_year_from_name("春季学期")
        self.assertIsNone(result)

    def test_normalize_season_name(self):
        """测试季节名称标准化"""
        test_cases = [
            ("spring", "春季"),
            ("autumn", "秋季"),
            ("春", "春季"),
            ("秋", "秋季"),
            ("春季", "春季"),
            ("秋季", "秋季"),
        ]

        for input_season, expected_output in test_cases:
            result = self.engine.normalize_season_name(input_season)
            self.assertEqual(
                result, expected_output, f"季节 '{input_season}' 应该标准化为 '{expected_output}'"
            )

    def test_validate_name_pattern(self):
        """测试命名模式验证"""
        # 测试有效模式
        valid_patterns = [
            "{year}年{season}",
            "{year}{season}",
            "{year}年{season}学期",
            "{season}{year}",
        ]

        for pattern in valid_patterns:
            result = self.engine.validate_name_pattern(pattern)
            self.assertTrue(result, f"模式 '{pattern}' 应该是有效的")

        # 测试无效模式
        invalid_patterns = [
            "{invalid}年{season}",
            "{year}年{invalid}",
            "",
            None,
        ]

        for pattern in invalid_patterns:
            result = self.engine.validate_name_pattern(pattern)
            self.assertFalse(result, f"模式 '{pattern}' 应该是无效的")

    def test_apply_name_pattern(self):
        """测试应用命名模式"""
        # 测试标准模式
        result = self.engine.apply_name_pattern("{year}年{season}", 2026, "spring")
        self.assertEqual(result, "2026年春季")

        result = self.engine.apply_name_pattern("{year}{season}学期", 2025, "autumn")
        self.assertEqual(result, "2025秋季学期")

        # 测试无效模式的回退
        result = self.engine.apply_name_pattern("{invalid}模式", 2026, "spring")
        self.assertEqual(result, "2026年春季")

    def test_comprehensive_workflow(self):
        """测试完整的工作流程"""
        # 模拟完整的命名流程
        reference_name = "2025年秋季"
        target_year = 2026

        # 1. 从参考名称生成新名称
        new_name = self.engine.generate_name_from_reference(reference_name, target_year)
        self.assertEqual(new_name, "2026年秋季")

        # 2. 验证生成的名称中的年份
        extracted_year = self.engine.extract_year_from_name(new_name)
        self.assertEqual(extracted_year, target_year)

        # 3. 验证生成的名称中的季节
        detected_season = self.engine._detect_season_from_name(new_name)
        self.assertEqual(detected_season, "autumn")


if __name__ == "__main__":
    unittest.main()
