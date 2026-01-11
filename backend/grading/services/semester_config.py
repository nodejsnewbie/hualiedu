"""
学期配置管理模块

提供学期自动创建和管理的配置功能，包括：
- 配置项的读取和验证
- 默认模板的管理
- 功能开关控制
"""

import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from grading.exceptions import SemesterConfigurationError, handle_semester_exceptions
from grading.models import SemesterTemplate

# 配置日志
logger = logging.getLogger(__name__)


# 默认配置
DEFAULT_SEMESTER_CONFIG = {
    "AUTO_CREATION_ENABLED": True,
    "AUTO_DETECTION_ENABLED": True,
    "AUTO_UPDATE_CURRENT_SEMESTER": True,
    "CREATE_MISSING_TEMPLATES": True,
    "DEFAULT_SEMESTER_DURATION_WEEKS": 16,
    "CACHE_TIMEOUT_SECONDS": 300,  # 5分钟
    "MAX_FUTURE_SEMESTERS": 2,
    "MAX_PAST_SEMESTERS_TO_KEEP": 10,
    "NOTIFICATION_ENABLED": True,
    "LOG_LEVEL": "INFO",
    "SPRING_SEMESTER": {
        "start_month": 3,
        "start_day": 1,
        "end_month": 7,
        "end_day": 31,
        "name_pattern": "{year}年春季学期",
    },
    "AUTUMN_SEMESTER": {
        "start_month": 9,
        "start_day": 1,
        "end_month": 2,  # 次年2月
        "end_day": 28,  # 2月底（不考虑闰年的复杂性）
        "name_pattern": "{year}年秋季学期",
    },
}


class SemesterConfigManager:
    """学期配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.cache_prefix = "semester_config:"
        self.config_cache = {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        # 首先尝试从缓存获取
        cache_key = f"{self.cache_prefix}{key}"
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        # 尝试从Django settings获取
        semester_settings = getattr(settings, "SEMESTER_AUTO_CREATION", {})
        if key in semester_settings:
            value = semester_settings[key]
        elif key in DEFAULT_SEMESTER_CONFIG:
            value = DEFAULT_SEMESTER_CONFIG[key]
        else:
            value = default

        # 缓存配置值
        cache_timeout = self.get_config("CACHE_TIMEOUT_SECONDS", 300)
        cache.set(cache_key, value, cache_timeout)

        return value

    def set_config(self, key: str, value: Any, persist: bool = False) -> None:
        """设置配置值

        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化到数据库
        """
        # 验证配置值
        self._validate_config_value(key, value)

        # 更新缓存
        cache_key = f"{self.cache_prefix}{key}"
        cache_timeout = self.get_config("CACHE_TIMEOUT_SECONDS", 300)
        cache.set(cache_key, value, cache_timeout)

        # 如果需要持久化，可以扩展到数据库存储
        if persist:
            logger.info(f"配置 {key} 已更新为: {value}")

    def is_auto_creation_enabled(self) -> bool:
        """检查是否启用自动创建"""
        return self.get_config("AUTO_CREATION_ENABLED", True)

    def is_auto_detection_enabled(self) -> bool:
        """检查是否启用自动检测"""
        return self.get_config("AUTO_DETECTION_ENABLED", True)

    def is_auto_update_enabled(self) -> bool:
        """检查是否启用自动更新当前学期"""
        return self.get_config("AUTO_UPDATE_CURRENT_SEMESTER", True)

    def get_default_duration_weeks(self) -> int:
        """获取默认学期周数"""
        return self.get_config("DEFAULT_SEMESTER_DURATION_WEEKS", 16)

    def get_spring_semester_config(self) -> Dict[str, Any]:
        """获取春季学期配置"""
        return self.get_config("SPRING_SEMESTER", DEFAULT_SEMESTER_CONFIG["SPRING_SEMESTER"])

    def get_autumn_semester_config(self) -> Dict[str, Any]:
        """获取秋季学期配置"""
        return self.get_config("AUTUMN_SEMESTER", DEFAULT_SEMESTER_CONFIG["AUTUMN_SEMESTER"])

    def get_semester_config_by_season(self, season: str) -> Dict[str, Any]:
        """根据季节获取学期配置

        Args:
            season: 季节 ('spring' 或 'autumn')

        Returns:
            学期配置字典
        """
        if season == "spring":
            return self.get_spring_semester_config()
        elif season == "autumn":
            return self.get_autumn_semester_config()
        else:
            raise SemesterConfigurationError(
                f"不支持的季节: {season}", config_key="season", config_value=season
            )

    def clear_cache(self) -> None:
        """清除配置缓存"""
        # 清除所有学期配置相关的缓存
        cache_keys = [f"{self.cache_prefix}{key}" for key in DEFAULT_SEMESTER_CONFIG.keys()]
        cache.delete_many(cache_keys)
        logger.info("学期配置缓存已清除")

    def reload_config(self) -> None:
        """重新加载配置"""
        self.clear_cache()
        logger.info("学期配置已重新加载")

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        for key in DEFAULT_SEMESTER_CONFIG.keys():
            config[key] = self.get_config(key)
        return config

    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性

        Returns:
            验证结果字典
        """
        errors = []
        warnings = []

        try:
            # 检查必要的配置项
            required_configs = ["AUTO_CREATION_ENABLED", "SPRING_SEMESTER", "AUTUMN_SEMESTER"]

            for config_key in required_configs:
                value = self.get_config(config_key)
                if value is None:
                    errors.append(f"缺少必要配置: {config_key}")

            # 验证春季学期配置
            spring_config = self.get_spring_semester_config()
            self._validate_semester_template_config("spring", spring_config, errors, warnings)

            # 验证秋季学期配置
            autumn_config = self.get_autumn_semester_config()
            self._validate_semester_template_config("autumn", autumn_config, errors, warnings)

            # 验证数值配置
            duration_weeks = self.get_default_duration_weeks()
            if not isinstance(duration_weeks, int) or duration_weeks < 1 or duration_weeks > 52:
                errors.append(f"无效的学期周数: {duration_weeks}")

        except Exception as e:
            errors.append(f"配置验证异常: {str(e)}")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_config_value(self, key: str, value: Any) -> None:
        """验证配置值

        Args:
            key: 配置键
            value: 配置值

        Raises:
            SemesterConfigurationError: 配置值无效
        """
        if key == "DEFAULT_SEMESTER_DURATION_WEEKS":
            if not isinstance(value, int) or value < 1 or value > 52:
                raise SemesterConfigurationError(
                    f"学期周数必须是1-52之间的整数，当前值: {value}",
                    config_key=key,
                    config_value=value,
                )
        elif key in [
            "AUTO_CREATION_ENABLED",
            "AUTO_DETECTION_ENABLED",
            "AUTO_UPDATE_CURRENT_SEMESTER",
        ]:
            if not isinstance(value, bool):
                raise SemesterConfigurationError(
                    f"配置 {key} 必须是布尔值，当前值: {value}", config_key=key, config_value=value
                )

    def _validate_semester_template_config(
        self, season: str, config: Dict[str, Any], errors: list, warnings: list
    ) -> None:
        """验证学期模板配置

        Args:
            season: 季节
            config: 配置字典
            errors: 错误列表
            warnings: 警告列表
        """
        required_fields = ["start_month", "start_day", "end_month", "end_day", "name_pattern"]

        for field in required_fields:
            if field not in config:
                errors.append(f"{season}学期配置缺少字段: {field}")
                continue

            value = config[field]

            if field in ["start_month", "end_month"]:
                if not isinstance(value, int) or value < 1 or value > 12:
                    errors.append(f"{season}学期{field}必须是1-12之间的整数: {value}")
            elif field in ["start_day", "end_day"]:
                if not isinstance(value, int) or value < 1 or value > 31:
                    errors.append(f"{season}学期{field}必须是1-31之间的整数: {value}")
            elif field == "name_pattern":
                if not isinstance(value, str) or "{year}" not in value:
                    errors.append(f"{season}学期名称模式必须包含{{year}}占位符: {value}")


class SemesterTemplateManager:
    """学期模板管理器"""

    def __init__(self):
        """初始化模板管理器"""
        self.config_manager = SemesterConfigManager()

    @handle_semester_exceptions()
    def ensure_default_templates(self) -> Dict[str, Any]:
        """确保默认模板存在

        Returns:
            操作结果字典
        """
        if not self.config_manager.get_config("CREATE_MISSING_TEMPLATES", True):
            return {"created": 0, "message": "自动创建模板功能已禁用"}

        created_count = 0

        with transaction.atomic():
            # 创建春季学期模板
            spring_created = self._ensure_season_template("spring")
            if spring_created:
                created_count += 1

            # 创建秋季学期模板
            autumn_created = self._ensure_season_template("autumn")
            if autumn_created:
                created_count += 1

        logger.info(f"默认模板检查完成，创建了 {created_count} 个模板")

        return {"created": created_count, "message": f"成功创建 {created_count} 个默认模板"}

    def _ensure_season_template(self, season: str) -> bool:
        """确保指定季节的模板存在

        Args:
            season: 季节

        Returns:
            是否创建了新模板
        """
        # 检查是否已存在活跃模板
        existing_template = SemesterTemplate.objects.filter(season=season, is_active=True).first()

        if existing_template:
            logger.debug(f"{season}季节模板已存在: {existing_template}")
            return False

        # 获取配置
        config = self.config_manager.get_semester_config_by_season(season)

        # 创建新模板
        template = SemesterTemplate.objects.create(
            season=season,
            start_month=config["start_month"],
            start_day=config["start_day"],
            end_month=config["end_month"],
            end_day=config["end_day"],
            name_pattern=config["name_pattern"],
            duration_weeks=self.config_manager.get_default_duration_weeks(),
            is_active=True,
        )

        logger.info(f"创建了{season}季节模板: {template}")
        return True

    @handle_semester_exceptions()
    def update_template_from_config(self, season: str) -> bool:
        """从配置更新模板

        Args:
            season: 季节

        Returns:
            是否更新成功
        """
        config = self.config_manager.get_semester_config_by_season(season)

        template = SemesterTemplate.objects.filter(season=season, is_active=True).first()

        if not template:
            # 如果模板不存在，创建新的
            return self._ensure_season_template(season)

        # 更新现有模板
        template.start_month = config["start_month"]
        template.start_day = config["start_day"]
        template.end_month = config["end_month"]
        template.end_day = config["end_day"]
        template.name_pattern = config["name_pattern"]
        template.duration_weeks = self.config_manager.get_default_duration_weeks()
        template.save()

        logger.info(f"更新了{season}季节模板: {template}")
        return True

    def get_template_summary(self) -> Dict[str, Any]:
        """获取模板摘要

        Returns:
            模板摘要字典
        """
        templates = SemesterTemplate.objects.filter(is_active=True)

        summary = {"total_count": templates.count(), "seasons": {}, "missing_seasons": []}

        for template in templates:
            summary["seasons"][template.season] = {
                "id": template.id,
                "name_pattern": template.name_pattern,
                "start_date": f"{template.start_month}-{template.start_day}",
                "end_date": f"{template.end_month}-{template.end_day}",
                "duration_weeks": template.duration_weeks,
            }

        # 检查缺失的季节
        expected_seasons = ["spring", "autumn"]
        for season in expected_seasons:
            if season not in summary["seasons"]:
                summary["missing_seasons"].append(season)

        return summary


# 全局配置管理器实例
config_manager = SemesterConfigManager()
template_manager = SemesterTemplateManager()
