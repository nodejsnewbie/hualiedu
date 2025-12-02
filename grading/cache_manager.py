"""
缓存管理模块

提供统一的缓存管理功能，包括：
- 目录文件数量缓存
- 目录树结构缓存
- 文件内容缓存
- 缓存过期管理
"""

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""

    # 缓存键前缀
    PREFIX_FILE_COUNT = "file_count"
    PREFIX_DIR_TREE = "dir_tree"
    PREFIX_FILE_CONTENT = "file_content"
    PREFIX_FILE_METADATA = "file_metadata"
    PREFIX_COMMENT_TEMPLATE = "comment_template"
    PREFIX_COURSE_LIST = "course_list"
    PREFIX_CLASS_LIST = "class_list"

    # 缓存过期时间（秒）
    TIMEOUT_FILE_COUNT = 300  # 5分钟
    TIMEOUT_DIR_TREE = 600  # 10分钟
    TIMEOUT_FILE_CONTENT = 180  # 3分钟
    TIMEOUT_FILE_METADATA = 300  # 5分钟
    TIMEOUT_COMMENT_TEMPLATE = 600  # 10分钟
    TIMEOUT_COURSE_LIST = 300  # 5分钟
    TIMEOUT_CLASS_LIST = 300  # 5分钟

    # 性能阈值
    MAX_FILES_WARNING = 500  # 文件数量警告阈值
    MAX_FILES_BATCH = 200  # 批量操作建议阈值
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, user_id: Optional[int] = None, tenant_id: Optional[int] = None):
        """
        初始化缓存管理器

        Args:
            user_id: 用户ID（用于生成用户特定的缓存键）
            tenant_id: 租户ID（用于多租户隔离）
        """
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _make_key(self, prefix: str, identifier: str) -> str:
        """
        生成缓存键

        Args:
            prefix: 缓存键前缀
            identifier: 标识符

        Returns:
            完整的缓存键
        """
        parts = [prefix]
        if self.tenant_id:
            parts.append(f"tenant_{self.tenant_id}")
        if self.user_id:
            parts.append(f"user_{self.user_id}")
        parts.append(identifier)
        return ":".join(parts)

    # ==================== 目录文件数量缓存 ====================

    def get_file_count(self, dir_path: str) -> Optional[int]:
        """
        获取缓存的目录文件数量

        Args:
            dir_path: 目录路径

        Returns:
            文件数量，如果缓存不存在则返回None
        """
        key = self._make_key(self.PREFIX_FILE_COUNT, dir_path)
        count = cache.get(key)
        if count is not None:
            self.logger.debug(f"缓存命中 - 目录文件数量: {dir_path} = {count}")
        return count

    def set_file_count(self, dir_path: str, count: int) -> None:
        """
        设置目录文件数量缓存

        Args:
            dir_path: 目录路径
            count: 文件数量
        """
        key = self._make_key(self.PREFIX_FILE_COUNT, dir_path)
        cache.set(key, count, self.TIMEOUT_FILE_COUNT)
        self.logger.debug(f"缓存设置 - 目录文件数量: {dir_path} = {count}")

    def clear_file_count(self, dir_path: Optional[str] = None) -> None:
        """
        清除目录文件数量缓存

        Args:
            dir_path: 目录路径，如果为None则清除所有
        """
        if dir_path:
            key = self._make_key(self.PREFIX_FILE_COUNT, dir_path)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 目录文件数量: {dir_path}")
        else:
            # 清除所有文件数量缓存（通过模式匹配）
            pattern = self._make_key(self.PREFIX_FILE_COUNT, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有目录文件数量")

    # ==================== 目录树结构缓存 ====================

    def get_dir_tree(self, dir_path: str) -> Optional[Dict]:
        """
        获取缓存的目录树结构

        Args:
            dir_path: 目录路径

        Returns:
            目录树结构，如果缓存不存在则返回None
        """
        key = self._make_key(self.PREFIX_DIR_TREE, dir_path)
        tree = cache.get(key)
        if tree is not None:
            self.logger.debug(f"缓存命中 - 目录树: {dir_path}")
        return tree

    def set_dir_tree(self, dir_path: str, tree: Dict) -> None:
        """
        设置目录树结构缓存

        Args:
            dir_path: 目录路径
            tree: 目录树结构
        """
        key = self._make_key(self.PREFIX_DIR_TREE, dir_path)
        cache.set(key, tree, self.TIMEOUT_DIR_TREE)
        self.logger.debug(f"缓存设置 - 目录树: {dir_path}")

    def clear_dir_tree(self, dir_path: Optional[str] = None) -> None:
        """
        清除目录树结构缓存

        Args:
            dir_path: 目录路径，如果为None则清除所有
        """
        if dir_path:
            key = self._make_key(self.PREFIX_DIR_TREE, dir_path)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 目录树: {dir_path}")
        else:
            pattern = self._make_key(self.PREFIX_DIR_TREE, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有目录树")

    # ==================== 文件内容缓存 ====================

    def get_file_content(self, file_path: str) -> Optional[Tuple[str, str]]:
        """
        获取缓存的文件内容

        Args:
            file_path: 文件路径

        Returns:
            (内容, 内容类型)元组，如果缓存不存在则返回None
        """
        key = self._make_key(self.PREFIX_FILE_CONTENT, file_path)
        content = cache.get(key)
        if content is not None:
            self.logger.debug(f"缓存命中 - 文件内容: {file_path}")
        return content

    def set_file_content(self, file_path: str, content: str, content_type: str) -> None:
        """
        设置文件内容缓存

        Args:
            file_path: 文件路径
            content: 文件内容
            content_type: 内容类型
        """
        key = self._make_key(self.PREFIX_FILE_CONTENT, file_path)
        cache.set(key, (content, content_type), self.TIMEOUT_FILE_CONTENT)
        self.logger.debug(f"缓存设置 - 文件内容: {file_path}")

    def clear_file_content(self, file_path: Optional[str] = None) -> None:
        """
        清除文件内容缓存

        Args:
            file_path: 文件路径，如果为None则清除所有
        """
        if file_path:
            key = self._make_key(self.PREFIX_FILE_CONTENT, file_path)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 文件内容: {file_path}")
        else:
            pattern = self._make_key(self.PREFIX_FILE_CONTENT, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有文件内容")

    # ==================== 评价模板缓存 ====================

    def get_comment_templates(self, template_type: str, identifier: str) -> Optional[list]:
        """
        获取缓存的评价模板列表

        Args:
            template_type: 模板类型 (personal/system/recommended)
            identifier: 标识符（如teacher_id或tenant_id）

        Returns:
            评价模板列表，如果缓存不存在则返回None
        """
        key = self._make_key(self.PREFIX_COMMENT_TEMPLATE, f"{template_type}_{identifier}")
        templates = cache.get(key)
        if templates is not None:
            self.logger.debug(f"缓存命中 - 评价模板: {template_type}_{identifier}")
        return templates

    def set_comment_templates(self, template_type: str, identifier: str, templates: list) -> None:
        """
        设置评价模板缓存

        Args:
            template_type: 模板类型 (personal/system/recommended)
            identifier: 标识符（如teacher_id或tenant_id）
            templates: 评价模板列表
        """
        key = self._make_key(self.PREFIX_COMMENT_TEMPLATE, f"{template_type}_{identifier}")
        cache.set(key, templates, self.TIMEOUT_COMMENT_TEMPLATE)
        self.logger.debug(
            f"缓存设置 - 评价模板: {template_type}_{identifier}, " f"数量={len(templates)}"
        )

    def clear_comment_templates(
        self, template_type: Optional[str] = None, identifier: Optional[str] = None
    ) -> None:
        """
        清除评价模板缓存

        Args:
            template_type: 模板类型（可选）
            identifier: 标识符（可选）
        """
        if template_type and identifier:
            key = self._make_key(self.PREFIX_COMMENT_TEMPLATE, f"{template_type}_{identifier}")
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 评价模板: {template_type}_{identifier}")
        else:
            pattern = self._make_key(self.PREFIX_COMMENT_TEMPLATE, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有评价模板")

    # ==================== 课程列表缓存 ====================

    def get_course_list(self, teacher_id: int, semester_id: Optional[int] = None) -> Optional[list]:
        """
        获取缓存的课程列表

        Args:
            teacher_id: 教师ID
            semester_id: 学期ID（可选）

        Returns:
            课程列表，如果缓存不存在则返回None
        """
        identifier = f"teacher_{teacher_id}"
        if semester_id:
            identifier += f"_semester_{semester_id}"
        key = self._make_key(self.PREFIX_COURSE_LIST, identifier)
        courses = cache.get(key)
        if courses is not None:
            self.logger.debug(f"缓存命中 - 课程列表: {identifier}")
        return courses

    def set_course_list(
        self, teacher_id: int, courses: list, semester_id: Optional[int] = None
    ) -> None:
        """
        设置课程列表缓存

        Args:
            teacher_id: 教师ID
            courses: 课程列表
            semester_id: 学期ID（可选）
        """
        identifier = f"teacher_{teacher_id}"
        if semester_id:
            identifier += f"_semester_{semester_id}"
        key = self._make_key(self.PREFIX_COURSE_LIST, identifier)
        cache.set(key, courses, self.TIMEOUT_COURSE_LIST)
        self.logger.debug(f"缓存设置 - 课程列表: {identifier}, 数量={len(courses)}")

    def clear_course_list(
        self, teacher_id: Optional[int] = None, semester_id: Optional[int] = None
    ) -> None:
        """
        清除课程列表缓存

        Args:
            teacher_id: 教师ID（可选）
            semester_id: 学期ID（可选）
        """
        if teacher_id:
            identifier = f"teacher_{teacher_id}"
            if semester_id:
                identifier += f"_semester_{semester_id}"
            key = self._make_key(self.PREFIX_COURSE_LIST, identifier)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 课程列表: {identifier}")
        else:
            pattern = self._make_key(self.PREFIX_COURSE_LIST, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有课程列表")

    # ==================== 班级列表缓存 ====================

    def get_class_list(
        self, course_id: Optional[int] = None, teacher_id: Optional[int] = None
    ) -> Optional[list]:
        """
        获取缓存的班级列表

        Args:
            course_id: 课程ID（可选）
            teacher_id: 教师ID（可选）

        Returns:
            班级列表，如果缓存不存在则返回None
        """
        if course_id:
            identifier = f"course_{course_id}"
        elif teacher_id:
            identifier = f"teacher_{teacher_id}"
        else:
            identifier = "all"
        key = self._make_key(self.PREFIX_CLASS_LIST, identifier)
        classes = cache.get(key)
        if classes is not None:
            self.logger.debug(f"缓存命中 - 班级列表: {identifier}")
        return classes

    def set_class_list(
        self,
        classes: list,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
    ) -> None:
        """
        设置班级列表缓存

        Args:
            classes: 班级列表
            course_id: 课程ID（可选）
            teacher_id: 教师ID（可选）
        """
        if course_id:
            identifier = f"course_{course_id}"
        elif teacher_id:
            identifier = f"teacher_{teacher_id}"
        else:
            identifier = "all"
        key = self._make_key(self.PREFIX_CLASS_LIST, identifier)
        cache.set(key, classes, self.TIMEOUT_CLASS_LIST)
        self.logger.debug(f"缓存设置 - 班级列表: {identifier}, 数量={len(classes)}")

    def clear_class_list(
        self, course_id: Optional[int] = None, teacher_id: Optional[int] = None
    ) -> None:
        """
        清除班级列表缓存

        Args:
            course_id: 课程ID（可选）
            teacher_id: 教师ID（可选）
        """
        if course_id:
            identifier = f"course_{course_id}"
            key = self._make_key(self.PREFIX_CLASS_LIST, identifier)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 班级列表: {identifier}")
        elif teacher_id:
            identifier = f"teacher_{teacher_id}"
            key = self._make_key(self.PREFIX_CLASS_LIST, identifier)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 班级列表: {identifier}")
        else:
            pattern = self._make_key(self.PREFIX_CLASS_LIST, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有班级列表")

    # ==================== 文件元数据缓存 ====================

    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """
        获取缓存的文件元数据

        Args:
            file_path: 文件路径

        Returns:
            文件元数据字典，如果缓存不存在则返回None
        """
        key = self._make_key(self.PREFIX_FILE_METADATA, file_path)
        metadata = cache.get(key)
        if metadata is not None:
            self.logger.debug(f"缓存命中 - 文件元数据: {file_path}")
        return metadata

    def set_file_metadata(self, file_path: str, metadata: Dict) -> None:
        """
        设置文件元数据缓存

        Args:
            file_path: 文件路径
            metadata: 文件元数据
        """
        key = self._make_key(self.PREFIX_FILE_METADATA, file_path)
        cache.set(key, metadata, self.TIMEOUT_FILE_METADATA)
        self.logger.debug(f"缓存设置 - 文件元数据: {file_path}")

    def clear_file_metadata(self, file_path: Optional[str] = None) -> None:
        """
        清除文件元数据缓存

        Args:
            file_path: 文件路径，如果为None则清除所有
        """
        if file_path:
            key = self._make_key(self.PREFIX_FILE_METADATA, file_path)
            cache.delete(key)
            self.logger.debug(f"缓存清除 - 文件元数据: {file_path}")
        else:
            pattern = self._make_key(self.PREFIX_FILE_METADATA, "*")
            self._clear_by_pattern(pattern)
            self.logger.debug("缓存清除 - 所有文件元数据")

    # ==================== 批量操作 ====================

    def clear_all(self) -> None:
        """清除所有缓存"""
        self.clear_file_count()
        self.clear_dir_tree()
        self.clear_file_content()
        self.clear_file_metadata()
        self.clear_comment_templates()
        self.clear_course_list()
        self.clear_class_list()
        self.logger.info("缓存清除 - 所有缓存")

    def clear_user_cache(self) -> None:
        """清除当前用户的所有缓存"""
        if not self.user_id:
            self.logger.warning("无法清除用户缓存：未指定用户ID")
            return

        # 清除用户相关的所有缓存
        for prefix in [
            self.PREFIX_FILE_COUNT,
            self.PREFIX_DIR_TREE,
            self.PREFIX_FILE_CONTENT,
            self.PREFIX_FILE_METADATA,
            self.PREFIX_COMMENT_TEMPLATE,
            self.PREFIX_COURSE_LIST,
            self.PREFIX_CLASS_LIST,
        ]:
            pattern = self._make_key(prefix, "*")
            self._clear_by_pattern(pattern)

        self.logger.info(f"缓存清除 - 用户 {self.user_id} 的所有缓存")

    def clear_tenant_cache(self) -> None:
        """清除当前租户的所有缓存"""
        if not self.tenant_id:
            self.logger.warning("无法清除租户缓存：未指定租户ID")
            return

        # 清除租户相关的所有缓存
        for prefix in [
            self.PREFIX_FILE_COUNT,
            self.PREFIX_DIR_TREE,
            self.PREFIX_FILE_CONTENT,
            self.PREFIX_FILE_METADATA,
            self.PREFIX_COMMENT_TEMPLATE,
            self.PREFIX_COURSE_LIST,
            self.PREFIX_CLASS_LIST,
        ]:
            pattern = self._make_key(prefix, "*")
            self._clear_by_pattern(pattern)

        self.logger.info(f"缓存清除 - 租户 {self.tenant_id} 的所有缓存")

    # ==================== 性能检查 ====================

    def check_file_count_threshold(self, file_count: int) -> Dict[str, Any]:
        """
        检查文件数量是否超过阈值

        Args:
            file_count: 文件数量

        Returns:
            检查结果字典
        """
        result = {
            "file_count": file_count,
            "warning": False,
            "error": False,
            "message": None,
            "suggestion": None,
        }

        if file_count > self.MAX_FILES_WARNING:
            result["warning"] = True
            result["message"] = f"文件数量较多（{file_count}个），处理可能需要较长时间"
            result["suggestion"] = "建议分批处理或在非高峰时段操作"

        if file_count > self.MAX_FILES_BATCH:
            result["error"] = True
            result["message"] = f"文件数量过多（{file_count}个），不建议批量处理"
            result["suggestion"] = f"建议将文件数量控制在{self.MAX_FILES_BATCH}个以内"

        return result

    def check_file_size(self, file_path: str) -> Dict[str, Any]:
        """
        检查文件大小是否超过限制

        Args:
            file_path: 文件路径

        Returns:
            检查结果字典
        """
        result = {
            "file_path": file_path,
            "file_size": 0,
            "warning": False,
            "error": False,
            "message": None,
        }

        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                result["file_size"] = file_size

                if file_size > self.MAX_FILE_SIZE:
                    result["error"] = True
                    result["message"] = (
                        f"文件过大（{file_size / 1024 / 1024:.2f}MB），"
                        f"超过限制（{self.MAX_FILE_SIZE / 1024 / 1024:.2f}MB）"
                    )
                elif file_size > self.MAX_FILE_SIZE * 0.8:
                    result["warning"] = True
                    result["message"] = (
                        f"文件较大（{file_size / 1024 / 1024:.2f}MB），" "处理可能较慢"
                    )
        except Exception as e:
            self.logger.error(f"检查文件大小失败: {file_path} - {str(e)}")
            result["error"] = True
            result["message"] = f"无法检查文件大小: {str(e)}"

        return result

    # ==================== 缓存统计 ====================

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        stats = {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "cache_backend": settings.CACHES.get("default", {}).get("BACKEND", "unknown"),
            "timeouts": {
                "file_count": self.TIMEOUT_FILE_COUNT,
                "dir_tree": self.TIMEOUT_DIR_TREE,
                "file_content": self.TIMEOUT_FILE_CONTENT,
                "file_metadata": self.TIMEOUT_FILE_METADATA,
                "comment_template": self.TIMEOUT_COMMENT_TEMPLATE,
                "course_list": self.TIMEOUT_COURSE_LIST,
                "class_list": self.TIMEOUT_CLASS_LIST,
            },
            "thresholds": {
                "max_files_warning": self.MAX_FILES_WARNING,
                "max_files_batch": self.MAX_FILES_BATCH,
                "max_file_size_mb": self.MAX_FILE_SIZE / 1024 / 1024,
            },
        }

        return stats

    # ==================== 私有方法 ====================

    def _clear_by_pattern(self, pattern: str) -> None:
        """
        根据模式清除缓存

        Args:
            pattern: 缓存键模式（支持通配符）
        """
        try:
            # Django的cache框架不直接支持模式删除
            # 这里使用delete_pattern（如果可用）或记录警告
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern(pattern)
            else:
                self.logger.warning(
                    f"缓存后端不支持模式删除: {pattern}，" "建议使用Redis或Memcached"
                )
        except Exception as e:
            self.logger.error(f"清除缓存失败: {pattern} - {str(e)}")


# ==================== 便捷函数 ====================


def get_cache_manager(request=None, user_id=None, tenant_id=None) -> CacheManager:
    """
    获取缓存管理器实例

    Args:
        request: Django请求对象
        user_id: 用户ID
        tenant_id: 租户ID

    Returns:
        CacheManager实例
    """
    if request:
        user_id = request.user.id if request.user.is_authenticated else None
        tenant_id = getattr(request, "tenant", None)
        if tenant_id:
            tenant_id = tenant_id.id

    return CacheManager(user_id=user_id, tenant_id=tenant_id)


def clear_all_cache():
    """清除所有缓存（管理员功能）"""
    manager = CacheManager()
    manager.clear_all()
    logger.info("管理员操作：清除所有缓存")
