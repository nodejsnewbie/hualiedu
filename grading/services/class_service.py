"""
班级管理服务模块

提供班级的创建、查询和管理功能，包括：
- 创建班级（验证课程关联）
- 列出班级
- 获取班级学生列表
"""

import logging
from typing import List, Optional

from django.contrib.auth.models import User
from django.db import transaction

from grading.cache_manager import CacheManager
from grading.models import Class, Course, Tenant

# 配置日志
logger = logging.getLogger(__name__)


class ClassService:
    """班级管理服务

    负责班级的创建、查询和管理，确保课程关联验证。
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """初始化服务

        Args:
            cache_manager: 缓存管理器（可选）
        """
        self.cache_manager = cache_manager

    @transaction.atomic
    def create_class(
        self,
        course: Course,
        name: str,
        student_count: int = 0,
        tenant: Optional[Tenant] = None,
    ) -> Class:
        """创建班级（验证课程关联）

        Args:
            course: 所属课程
            name: 班级名称
            student_count: 学生人数
            tenant: 所属租户

        Returns:
            创建的班级对象

        Raises:
            ValueError: 如果参数无效
        """
        # 验证必需参数
        if not course:
            raise ValueError("必须指定所属课程")

        if not name or not name.strip():
            raise ValueError("班级名称不能为空")

        if student_count < 0:
            raise ValueError("学生人数不能为负数")

        # 如果没有提供租户，使用课程的租户
        if not tenant:
            tenant = course.tenant

        if not tenant:
            raise ValueError("无法确定租户信息")

        # 验证课程和租户的一致性
        if course.tenant and course.tenant != tenant:
            raise ValueError("课程和班级必须属于同一租户")

        # 创建班级
        class_obj = Class.objects.create(
            course=course,
            name=name.strip(),
            student_count=student_count,
            tenant=tenant,
        )

        logger.info(
            f"创建班级成功: {class_obj.name} "
            f"(课程: {course.name}, 学生人数: {student_count}, 租户: {tenant.name})"
        )

        # 清除班级列表缓存
        if self.cache_manager:
            self.cache_manager.clear_class_list(course_id=course.id)
            self.cache_manager.clear_class_list(teacher_id=course.teacher.id)
            logger.debug(f"清除课程 {course.name} 的班级列表缓存")

        return class_obj

    def list_classes(
        self, course: Optional[Course] = None, tenant: Optional[Tenant] = None
    ) -> List[Class]:
        """列出班级

        Args:
            course: 课程（可选，用于过滤特定课程的班级）
            tenant: 租户（可选，用于过滤特定租户的班级）

        Returns:
            班级列表
        """
        # 尝试从缓存获取（仅当指定了课程时）
        if course and self.cache_manager:
            cached = self.cache_manager.get_class_list(course_id=course.id)
            if cached is not None:
                logger.debug(f"从缓存获取课程 {course.name} 的班级列表")
                return cached

        # 基础查询
        queryset = Class.objects.all()

        # 如果提供了课程，过滤特定课程的班级
        if course:
            queryset = queryset.filter(course=course)

        # 如果提供了租户，过滤特定租户的班级
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        # 使用 select_related 优化查询
        queryset = queryset.select_related("course", "course__teacher", "tenant")

        # 按课程和名称排序
        classes = list(queryset.order_by("course__name", "name"))

        # 缓存结果（仅当指定了课程时）
        if course and self.cache_manager:
            self.cache_manager.set_class_list(classes, course_id=course.id)

        logger.info(
            f"查询班级，共 {len(classes)} 个"
            + (f" (课程: {course.name})" if course else "")
            + (f" (租户: {tenant.name})" if tenant else "")
        )

        return classes

    def get_class_students(self, class_id: int) -> List[User]:
        """获取班级学生列表

        Args:
            class_id: 班级ID

        Returns:
            学生用户列表

        Raises:
            Class.DoesNotExist: 如果班级不存在
        """
        # 获取班级
        class_obj = Class.objects.select_related("course", "tenant").get(id=class_id)

        # 查询该班级的所有学生
        # 通过提交记录关联查找学生
        from grading.models import Submission

        student_ids = (
            Submission.objects.filter(homework__class_obj=class_obj)
            .values_list("student_id", flat=True)
            .distinct()
        )

        students = list(User.objects.filter(id__in=student_ids).order_by("username"))

        logger.info(f"查询班级 {class_obj.name} 的学生，共 {len(students)} 人")

        return students

    def get_class_by_id(self, class_id: int) -> Class:
        """根据ID获取班级

        Args:
            class_id: 班级ID

        Returns:
            班级对象

        Raises:
            Class.DoesNotExist: 如果班级不存在
        """
        class_obj = Class.objects.select_related("course", "course__teacher", "tenant").get(
            id=class_id
        )

        return class_obj

    def get_classes_by_course(self, course: Course) -> List[Class]:
        """获取指定课程的所有班级

        Args:
            course: 课程对象

        Returns:
            班级列表
        """
        return self.list_classes(course=course)

    def list_classes_by_teacher(
        self, teacher: User, tenant: Optional[Tenant] = None
    ) -> List[Class]:
        """列出教师的所有班级

        Args:
            teacher: 教师用户
            tenant: 租户（可选，用于额外过滤）

        Returns:
            班级列表
        """
        # 尝试从缓存获取
        if self.cache_manager:
            cached = self.cache_manager.get_class_list(teacher_id=teacher.id)
            if cached is not None:
                logger.debug(f"从缓存获取教师 {teacher.username} 的班级列表")
                return cached

        # 基础查询：通过课程关联查找教师的班级
        queryset = Class.objects.filter(course__teacher=teacher)

        # 如果提供了租户，额外过滤
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        # 使用 select_related 优化查询
        queryset = queryset.select_related("course", "course__teacher", "tenant")

        # 按课程和名称排序
        classes = list(queryset.order_by("course__name", "name"))

        # 缓存结果
        if self.cache_manager:
            self.cache_manager.set_class_list(classes, teacher_id=teacher.id)

        logger.info(
            f"查询教师 {teacher.username} 的班级，共 {len(classes)} 个"
            + (f" (租户: {tenant.name})" if tenant else "")
        )

        return classes

    @transaction.atomic
    def update_class(
        self,
        class_id: int,
        name: Optional[str] = None,
        student_count: Optional[int] = None,
    ) -> Class:
        """更新班级信息

        Args:
            class_id: 班级ID
            name: 新的班级名称（可选）
            student_count: 新的学生人数（可选）

        Returns:
            更新后的班级对象

        Raises:
            ValueError: 如果参数无效
            Class.DoesNotExist: 如果班级不存在
        """
        class_obj = self.get_class_by_id(class_id)

        updated_fields = []

        # 更新名称
        if name is not None:
            if not name.strip():
                raise ValueError("班级名称不能为空")
            class_obj.name = name.strip()
            updated_fields.append("name")

        # 更新学生人数
        if student_count is not None:
            if student_count < 0:
                raise ValueError("学生人数不能为负数")
            class_obj.student_count = student_count
            updated_fields.append("student_count")

        if updated_fields:
            class_obj.save(update_fields=updated_fields + ["updated_at"])
            logger.info(f"更新班级 {class_obj.name}: {', '.join(updated_fields)}")

            # 清除班级列表缓存
            if self.cache_manager:
                self.cache_manager.clear_class_list(course_id=class_obj.course.id)
                self.cache_manager.clear_class_list(teacher_id=class_obj.course.teacher.id)
                logger.debug(f"清除班级 {class_obj.name} 的缓存")

        return class_obj

    @transaction.atomic
    def delete_class(self, class_id: int) -> None:
        """删除班级

        Args:
            class_id: 班级ID

        Raises:
            Class.DoesNotExist: 如果班级不存在
        """
        class_obj = self.get_class_by_id(class_id)

        class_name = class_obj.name
        course_name = class_obj.course.name

        class_obj.delete()

        # 清除班级列表缓存
        if self.cache_manager:
            self.cache_manager.clear_class_list(course_id=class_obj.course.id)
            self.cache_manager.clear_class_list(teacher_id=class_obj.course.teacher.id)
            logger.debug(f"清除班级 {class_name} 的缓存")

        logger.info(f"删除班级: {class_name} (课程: {course_name})")
