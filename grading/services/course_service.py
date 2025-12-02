"""
课程管理服务模块

提供课程的创建、查询和管理功能，包括：
- 创建课程
- 列出教师的课程（数据隔离）
- 更新课程类型
"""

import logging
from typing import List, Optional

from django.contrib.auth.models import User
from django.db import transaction

from grading.cache_manager import CacheManager
from grading.models import Course, Tenant

# 配置日志
logger = logging.getLogger(__name__)


class CourseService:
    """课程管理服务

    负责课程的创建、查询和管理，确保教师数据隔离。
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """初始化服务

        Args:
            cache_manager: 缓存管理器（可选）
        """
        self.cache_manager = cache_manager

    @transaction.atomic
    def create_course(
        self,
        teacher: User,
        name: str,
        course_type: str,
        description: str = "",
        semester=None,
        tenant: Optional[Tenant] = None,
    ) -> Course:
        """创建课程

        Args:
            teacher: 授课教师
            name: 课程名称
            course_type: 课程类型 (theory/lab/practice/mixed)
            description: 课程描述
            semester: 所属学期
            tenant: 所属租户

        Returns:
            创建的课程对象

        Raises:
            ValueError: 如果参数无效
        """
        # 验证课程类型
        valid_types = ["theory", "lab", "practice", "mixed"]
        if course_type not in valid_types:
            raise ValueError(
                f"无效的课程类型: {course_type}. 必须是以下之一: {', '.join(valid_types)}"
            )

        # 验证必需参数
        if not name or not name.strip():
            raise ValueError("课程名称不能为空")

        if not teacher:
            raise ValueError("必须指定授课教师")

        if not semester:
            raise ValueError("必须指定所属学期")

        # 如果没有提供租户，尝试从教师的用户配置中获取
        if not tenant and hasattr(teacher, "profile"):
            tenant = teacher.profile.tenant

        if not tenant:
            raise ValueError("无法确定租户信息")

        # 创建课程
        course = Course.objects.create(
            teacher=teacher,
            name=name.strip(),
            course_type=course_type,
            description=description.strip() if description else "",
            semester=semester,
            tenant=tenant,
        )

        logger.info(
            f"创建课程成功: {course.name} (类型: {course.get_course_type_display()}, "
            f"教师: {teacher.username}, 租户: {tenant.name})"
        )

        # 清除课程列表缓存
        if self.cache_manager:
            self.cache_manager.clear_course_list(teacher_id=teacher.id)
            if semester:
                self.cache_manager.clear_course_list(teacher_id=teacher.id, semester_id=semester.id)
            logger.debug(f"清除教师 {teacher.username} 的课程列表缓存")

        return course

    def list_courses(
        self, teacher: User, tenant: Optional[Tenant] = None, semester=None
    ) -> List[Course]:
        """列出教师的所有课程（教师数据隔离）

        Args:
            teacher: 教师用户
            tenant: 租户（可选，用于额外过滤）
            semester: 学期（可选，用于过滤特定学期的课程）

        Returns:
            课程列表
        """
        # 尝试从缓存获取
        semester_id = semester.id if semester else None
        if self.cache_manager:
            cached = self.cache_manager.get_course_list(
                teacher_id=teacher.id, semester_id=semester_id
            )
            if cached is not None:
                logger.debug(
                    f"从缓存获取教师 {teacher.username} 的课程列表"
                    + (f" (学期: {semester.name})" if semester else "")
                )
                return cached

        # 基础查询：只返回该教师的课程
        queryset = Course.objects.filter(teacher=teacher)

        # 如果提供了租户，额外过滤
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        # 如果提供了学期，过滤特定学期
        if semester:
            queryset = queryset.filter(semester=semester)

        # 使用 select_related 优化查询
        queryset = queryset.select_related("semester", "teacher", "tenant")

        # 按学期和名称排序
        courses = list(queryset.order_by("-semester__start_date", "name"))

        # 缓存结果
        if self.cache_manager:
            self.cache_manager.set_course_list(
                teacher_id=teacher.id, courses=courses, semester_id=semester_id
            )

        logger.info(
            f"查询教师 {teacher.username} 的课程，共 {len(courses)} 门"
            + (f" (学期: {semester.name})" if semester else "")
        )

        return courses

    @transaction.atomic
    def update_course_type(self, course_id: int, course_type: str) -> Course:
        """更新课程类型

        Args:
            course_id: 课程ID
            course_type: 新的课程类型 (theory/lab/practice/mixed)

        Returns:
            更新后的课程对象

        Raises:
            ValueError: 如果参数无效
            Course.DoesNotExist: 如果课程不存在
        """
        # 验证课程类型
        valid_types = ["theory", "lab", "practice", "mixed"]
        if course_type not in valid_types:
            raise ValueError(
                f"无效的课程类型: {course_type}. 必须是以下之一: {', '.join(valid_types)}"
            )

        # 获取课程
        course = Course.objects.select_related("teacher", "semester").get(id=course_id)

        # 记录旧类型
        old_type = course.course_type
        old_type_display = course.get_course_type_display()

        # 更新类型
        course.course_type = course_type
        course.save()

        new_type_display = course.get_course_type_display()

        logger.info(
            f"更新课程类型: {course.name} "
            f"从 {old_type_display} ({old_type}) 改为 {new_type_display} ({course_type})"
        )

        # 清除课程列表缓存
        if self.cache_manager:
            self.cache_manager.clear_course_list(teacher_id=course.teacher.id)
            if course.semester:
                self.cache_manager.clear_course_list(
                    teacher_id=course.teacher.id, semester_id=course.semester.id
                )
            logger.debug(f"清除教师 {course.teacher.username} 的课程列表缓存")

        return course

    def get_course_by_id(self, course_id: int, teacher: Optional[User] = None) -> Course:
        """根据ID获取课程

        Args:
            course_id: 课程ID
            teacher: 教师用户（可选，用于验证权限）

        Returns:
            课程对象

        Raises:
            Course.DoesNotExist: 如果课程不存在或教师无权访问
        """
        queryset = Course.objects.select_related("semester", "teacher", "tenant")

        # 如果提供了教师，确保只能访问自己的课程
        if teacher:
            queryset = queryset.filter(teacher=teacher)

        course = queryset.get(id=course_id)

        return course

    def get_courses_by_semester(
        self, semester, teacher: Optional[User] = None, tenant: Optional[Tenant] = None
    ) -> List[Course]:
        """获取指定学期的课程

        Args:
            semester: 学期对象
            teacher: 教师用户（可选，用于过滤）
            tenant: 租户（可选，用于过滤）

        Returns:
            课程列表
        """
        queryset = Course.objects.filter(semester=semester)

        if teacher:
            queryset = queryset.filter(teacher=teacher)

        if tenant:
            queryset = queryset.filter(tenant=tenant)

        queryset = queryset.select_related("semester", "teacher", "tenant")

        courses = list(queryset.order_by("name"))

        logger.info(
            f"查询学期 {semester.name} 的课程，共 {len(courses)} 门"
            + (f" (教师: {teacher.username})" if teacher else "")
        )

        return courses

    def delete_course(self, course_id: int, teacher: Optional[User] = None) -> None:
        """删除课程

        Args:
            course_id: 课程ID
            teacher: 教师用户（可选，用于验证权限）

        Raises:
            Course.DoesNotExist: 如果课程不存在或教师无权访问
        """
        course = self.get_course_by_id(course_id, teacher)

        course_name = course.name
        teacher_name = course.teacher.username

        course.delete()

        # 清除课程列表缓存
        if self.cache_manager:
            self.cache_manager.clear_course_list(teacher_id=course.teacher.id)
            if course.semester:
                self.cache_manager.clear_course_list(
                    teacher_id=course.teacher.id, semester_id=course.semester.id
                )
            logger.debug(f"清除教师 {teacher_name} 的课程列表缓存")

        logger.info(f"删除课程: {course_name} (教师: {teacher_name})")

    def update_course(
        self,
        course_id: int,
        name: Optional[str] = None,
        course_type: Optional[str] = None,
        description: Optional[str] = None,
        teacher: Optional[User] = None,
    ) -> Course:
        """更新课程信息

        Args:
            course_id: 课程ID
            name: 新的课程名称（可选）
            course_type: 新的课程类型（可选）
            description: 新的课程描述（可选）
            teacher: 教师用户（可选，用于验证权限）

        Returns:
            更新后的课程对象

        Raises:
            ValueError: 如果参数无效
            Course.DoesNotExist: 如果课程不存在或教师无权访问
        """
        course = self.get_course_by_id(course_id, teacher)

        updated_fields = []

        # 更新名称
        if name is not None:
            if not name.strip():
                raise ValueError("课程名称不能为空")
            course.name = name.strip()
            updated_fields.append("name")

        # 更新类型
        if course_type is not None:
            valid_types = ["theory", "lab", "practice", "mixed"]
            if course_type not in valid_types:
                raise ValueError(
                    f"无效的课程类型: {course_type}. 必须是以下之一: {', '.join(valid_types)}"
                )
            course.course_type = course_type
            updated_fields.append("course_type")

        # 更新描述
        if description is not None:
            course.description = description.strip() if description else ""
            updated_fields.append("description")

        if updated_fields:
            course.save(update_fields=updated_fields + ["updated_at"])
            logger.info(f"更新课程 {course.name}: {', '.join(updated_fields)}")

            # 清除课程列表缓存
            if self.cache_manager:
                self.cache_manager.clear_course_list(teacher_id=course.teacher.id)
                if course.semester:
                    self.cache_manager.clear_course_list(
                        teacher_id=course.teacher.id, semester_id=course.semester.id
                    )
                logger.debug(f"清除教师 {course.teacher.username} 的课程列表缓存")

        return course
