"""
评分类型管理工具
负责管理班级的评分类型配置和转换
"""

import logging
import os
from typing import Tuple

from .models import GradeTypeConfig

logger = logging.getLogger(__name__)

# 评分类型转换映射
GRADE_CONVERSION_MAPS = {
    "letter_to_text": {"A": "优秀", "B": "良好", "C": "中等", "D": "及格", "E": "不及格"},
    "letter_to_numeric": {"A": "90-100", "B": "80-89", "C": "70-79", "D": "60-69", "E": "0-59"},
    "text_to_letter": {"优秀": "A", "良好": "B", "中等": "C", "及格": "D", "不及格": "E"},
    "text_to_numeric": {
        "优秀": "90-100",
        "良好": "80-89",
        "中等": "70-79",
        "及格": "60-69",
        "不及格": "0-59",
    },
    "numeric_to_letter": {"90-100": "A", "80-89": "B", "70-79": "C", "60-69": "D", "0-59": "E"},
    "numeric_to_text": {
        "90-100": "优秀",
        "80-89": "良好",
        "70-79": "中等",
        "60-69": "及格",
        "0-59": "不及格",
    },
}


def get_class_identifier_from_path(file_path: str, base_dir: str) -> str:
    """从文件路径中提取班级标识"""
    try:
        rel_path = os.path.relpath(file_path, base_dir)
        path_parts = rel_path.split(os.sep)
        return path_parts[0] if len(path_parts) >= 1 else "default"
    except Exception as e:
        logger.error(f"提取班级标识失败: {e}")
        return "default"


def get_or_create_grade_type_config(class_identifier: str, tenant=None) -> GradeTypeConfig:
    """获取或创建班级的评分类型配置"""
    try:
        if tenant is None:
            logger.error("租户不能为空")
            return None

        config, created = GradeTypeConfig.objects.get_or_create(
            tenant=tenant,
            class_identifier=class_identifier,
            defaults={"grade_type": "letter", "is_locked": False},
        )
        if created:
            logger.info(
                f"为租户 {tenant.name} 的班级 {class_identifier} 创建新的评分类型配置: {config.grade_type}"
            )
        return config
    except Exception as e:
        logger.error(f"获取评分类型配置失败: {e}")
        return None


def convert_grade(grade: str, from_type: str, to_type: str) -> str:
    """转换评分类型"""
    if from_type == to_type:
        return grade

    conversion_key = f"{from_type}_to_{to_type}"
    if conversion_key in GRADE_CONVERSION_MAPS:
        conversion_map = GRADE_CONVERSION_MAPS[conversion_key]
        return conversion_map.get(grade, grade)
    else:
        logger.warning(f"不支持的评分类型转换: {from_type} -> {to_type}")
        return grade


def validate_grade_type_consistency(
    class_identifier: str, new_grade_type: str, tenant=None
) -> Tuple[bool, str]:
    """验证评分类型一致性"""
    try:
        config = get_or_create_grade_type_config(class_identifier, tenant)
        if config is None:
            return False, "无法获取评分类型配置"
        if config.is_locked and config.grade_type != new_grade_type:
            return (
                False,
                f"班级 {class_identifier} 的评分类型已锁定为 {config.get_grade_type_display()}，不能更改为 {new_grade_type}",
            )
        return True, ""
    except Exception as e:
        logger.error(f"验证评分类型一致性失败: {e}")
        return False, f"验证失败: {str(e)}"


def lock_grade_type_for_class(class_identifier: str, tenant=None) -> bool:
    """锁定班级的评分类型"""
    try:
        config = get_or_create_grade_type_config(class_identifier, tenant)
        if config is None:
            return False
        config.lock_grade_type()
        logger.info(
            f"已锁定租户 {tenant.name} 的班级 {class_identifier} 的评分类型: {config.grade_type}"
        )
        return True
    except Exception as e:
        logger.error(f"锁定评分类型失败: {e}")
        return False


def change_grade_type_for_class(
    class_identifier: str, new_grade_type: str, base_dir: str, tenant=None
) -> Tuple[bool, str, int]:
    """更改班级的评分类型并转换所有相关评分"""
    try:
        config = get_or_create_grade_type_config(class_identifier, tenant)
        if config is None:
            return False, "无法获取评分类型配置", 0

        if not config.can_change_grade_type():
            return False, f"班级 {class_identifier} 的评分类型已锁定，无法更改", 0

        old_grade_type = config.grade_type
        if old_grade_type == new_grade_type:
            return True, f"评分类型已经是 {new_grade_type}，无需更改", 0

        config.grade_type = new_grade_type
        config.save()

        converted_count = convert_all_grades_in_class(
            class_identifier, old_grade_type, new_grade_type, base_dir
        )
        message = f"成功将租户 {tenant.name} 的班级 {class_identifier} 的评分类型从 {old_grade_type} 更改为 {new_grade_type}，转换了 {converted_count} 个文件"
        logger.info(message)

        return True, message, converted_count

    except Exception as e:
        error_msg = f"更改评分类型失败: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, 0


def convert_all_grades_in_class(
    class_identifier: str, from_type: str, to_type: str, base_dir: str
) -> int:
    """转换班级中所有文件的评分类型"""
    import glob

    from .views import get_file_grade_info, write_grade_and_comment_to_file

    converted_count = 0

    try:
        class_dir = os.path.join(base_dir, class_identifier)
        if not os.path.exists(class_dir):
            logger.warning(f"班级目录不存在: {class_dir}")
            return 0

        pattern = os.path.join(class_dir, "**/*.docx")
        files = glob.glob(pattern, recursive=True)

        for file_path in files:
            try:
                grade_info = get_file_grade_info(file_path)

                if grade_info["has_grade"] and grade_info["grade"]:
                    new_grade = convert_grade(grade_info["grade"], from_type, to_type)
                    comment = grade_info.get("comment")

                    write_grade_and_comment_to_file(
                        file_path, grade=new_grade, comment=comment, base_dir=base_dir
                    )
                    converted_count += 1
                    logger.info(f"转换文件 {file_path}: {grade_info['grade']} -> {new_grade}")

            except Exception as e:
                logger.error(f"转换文件 {file_path} 失败: {e}")
                continue

        return converted_count

    except Exception as e:
        logger.error(f"转换班级评分失败: {e}")
        return converted_count


def get_grade_type_display_name(grade_type: str) -> str:
    """获取评分类型的显示名称"""
    display_names = {
        "letter": "字母等级 (A/B/C/D/E)",
        "text": "文本等级 (优秀/良好/中等/及格/不及格)",
        "numeric": "数字等级 (90-100/80-89/70-79/60-69/0-59)",
    }
    return display_names.get(grade_type, grade_type)
