"""
学期命名引擎
负责处理学期命名规则和模式识别
"""

import re
from datetime import date
from typing import Optional


class SemesterNamingEngine:
    """学期命名规则引擎"""

    def __init__(self):
        # 常见的年份模式
        self.year_patterns = [
            r"(\d{4})年",  # 2025年
            r"(\d{4})",  # 2025
        ]

        # 季节映射
        self.season_map = {
            "spring": "春季",
            "autumn": "秋季",
            "春": "春季",
            "秋": "秋季",
            "春季": "春季",
            "秋季": "秋季",
        }

        # 反向季节映射
        self.reverse_season_map = {v: k for k, v in self.season_map.items()}
        self.reverse_season_map.update(
            {
                "春": "spring",
                "秋": "autumn",
            }
        )

    def generate_name_from_reference(self, reference_name: str, target_year: int) -> str:
        """
        基于参考学期名称生成新名称

        Args:
            reference_name: 参考学期名称，如"2025年秋季"
            target_year: 目标年份，如2026

        Returns:
            新的学期名称，如"2026年秋季"
        """
        if not reference_name or not target_year:
            return self.generate_default_name(date(target_year, 9, 1))

        # 尝试替换年份
        new_name = reference_name

        # 查找并替换年份
        for pattern in self.year_patterns:
            match = re.search(pattern, reference_name)
            if match:
                old_year = match.group(1)
                new_name = reference_name.replace(old_year, str(target_year))
                break

        # 如果没有找到年份模式，尝试智能生成
        if new_name == reference_name:
            detected_season = self._detect_season_from_name(reference_name)
            if detected_season:
                season_chinese = self.season_map.get(detected_season, detected_season)
                new_name = f"{target_year}年{season_chinese}"
            else:
                # 如果无法检测季节，使用默认模式
                new_name = f"{target_year}年学期"

        return new_name

    def generate_default_name(self, target_date: date) -> str:
        """
        生成默认学期名称

        Args:
            target_date: 目标日期

        Returns:
            默认学期名称
        """
        season = self.detect_semester_season(target_date)
        season_chinese = self.season_map.get(season, season)
        return f"{target_date.year}年{season_chinese}"

    def detect_semester_season(self, start_date: date) -> str:
        """
        检测学期季节（春季/秋季）

        Args:
            start_date: 学期开始日期

        Returns:
            季节标识：'spring' 或 'autumn'
        """
        month = start_date.month

        # 根据开始月份判断季节
        # 春季学期：3月-7月开始
        # 秋季学期：8月-2月开始（跨年）
        if 3 <= month <= 7:
            return "spring"
        else:
            return "autumn"

    def _detect_season_from_name(self, name: str) -> Optional[str]:
        """
        从学期名称中检测季节

        Args:
            name: 学期名称

        Returns:
            季节标识或None
        """
        name_lower = name.lower()

        # 检查各种季节表示
        for season_key, season_value in self.season_map.items():
            if season_key in name or season_value in name:
                # 返回标准的英文季节标识
                if season_value == "春季":
                    return "spring"
                elif season_value == "秋季":
                    return "autumn"

        # 检查英文季节
        if "spring" in name_lower:
            return "spring"
        elif "autumn" in name_lower or "fall" in name_lower:
            return "autumn"

        return None

    def extract_year_from_name(self, name: str) -> Optional[int]:
        """
        从学期名称中提取年份

        Args:
            name: 学期名称

        Returns:
            年份或None
        """
        for pattern in self.year_patterns:
            match = re.search(pattern, name)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def normalize_season_name(self, season: str) -> str:
        """
        标准化季节名称

        Args:
            season: 季节名称

        Returns:
            标准化的季节名称
        """
        return self.season_map.get(season, season)

    def validate_name_pattern(self, pattern: str) -> bool:
        """
        验证命名模式是否有效

        Args:
            pattern: 命名模式，如"{year}年{season}"

        Returns:
            是否有效
        """
        if not pattern:
            return False

        try:
            # 尝试格式化模式
            test_name = pattern.format(year=2025, season="春季")
            return len(test_name) > 0
        except (KeyError, ValueError, AttributeError):
            return False

    def apply_name_pattern(self, pattern: str, year: int, season: str) -> str:
        """
        应用命名模式生成名称

        Args:
            pattern: 命名模式
            year: 年份
            season: 季节

        Returns:
            生成的名称
        """
        season_chinese = self.normalize_season_name(season)

        try:
            return pattern.format(year=year, season=season_chinese)
        except (KeyError, ValueError):
            # 如果模式无效，使用默认格式
            return f"{year}年{season_chinese}"
