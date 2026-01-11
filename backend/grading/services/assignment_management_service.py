"""
作业管理服务 (Assignment Management Service)

本服务提供作业配置的完整生命周期管理，包括创建、查询、更新和删除功能。

核心功能：
1. 创建作业配置：支持Git仓库和文件上传两种提交方式
2. 查询作业列表：支持按课程和班级筛选，教师隔离
3. 获取作业结构：直接从远程仓库或本地文件系统读取目录结构
4. 更新作业配置：保护已提交的学生作业数据
5. 删除作业配置：软删除，保留学生作业数据

设计原则：
- 用户友好：隐藏技术细节，使用教育领域术语
- 远程优先：Git方式直接访问远程仓库，无需本地克隆
- 数据隔离：教师只能访问自己创建的作业配置
- 数据保护：编辑和删除操作保护已提交的学生作业

术语说明：
- Assignment（作业配置）：原名 Repository（仓库）
- Storage Type（提交方式）：原名 Repo Type（仓库类型）
- 界面显示为"作业管理"而非"仓库管理"
"""

import logging
import os
from typing import Any, Dict, List, Optional

from django.contrib.auth.models import User
from django.db.models import Q, QuerySet

from grading.models import Assignment, Class, Course

logger = logging.getLogger(__name__)


class AssignmentManagementService:
    """作业管理服务类

    提供作业配置的CRUD操作和业务逻辑处理。

    主要方法：
    - create_assignment: 创建新的作业配置
    - list_assignments: 获取教师的作业配置列表
    - get_assignment_structure: 获取作业目录结构（远程或本地）
    - update_assignment: 更新作业配置
    - delete_assignment: 删除作业配置（软删除）

    使用示例：
        service = AssignmentManagementService()

        # 创建Git方式的作业配置
        assignment = service.create_assignment(
            teacher=teacher_user,
            course=course,
            class_obj=class_obj,
            name="数据结构作业",
            storage_type="git",
            git_url="https://github.com/user/repo.git",
            git_branch="main"
        )

        # 获取作业列表
        assignments = service.list_assignments(teacher=teacher_user, course=course)

        # 获取作业结构（直接从远程仓库读取）
        structure = service.get_assignment_structure(assignment, path="第一次作业")
    """

    def create_assignment(
        self,
        teacher: User,
        course: Course,
        class_obj: Class,
        name: str,
        storage_type: str,
        **kwargs,
    ) -> Assignment:
        """创建作业配置

        验证输入并创建作业配置记录。对于文件系统类型，自动生成并创建目录结构。

        实现需求:
        - Requirements 2.1: 提供两个清晰的选项："Git 仓库"和"文件上传"
        - Requirements 2.2: 只显示该方式相关的配置字段
        - Requirements 2.3: 文件上传方式要求输入课程名称、班级名称和作业次数
        - Requirements 2.4: Git 仓库方式要求输入 Git 仓库 URL 和分支名称
        - Requirements 2.5: 验证所有必填字段已填写
        - Requirements 4.1: 根据课程名称和班级名称生成基础目录路径

        Args:
            teacher: 创建作业的教师用户
            course: 关联的课程
            class_obj: 关联的班级
            name: 作业名称
            storage_type: 存储类型（git/filesystem）
            **kwargs: 其他配置参数
                - description: 作业描述（可选）
                - git_url: Git仓库URL（Git类型必填）
                - git_branch: Git分支（Git类型，默认"main"）
                - git_username: Git用户名（Git类型，可选）
                - git_password: Git密码明文（Git类型，可选，会自动加密）

        Returns:
            创建的 Assignment 对象

        Raises:
            ValidationError: 输入验证失败
            PermissionError: 权限不足

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 创建文件上传类型作业
            >>> assignment = service.create_assignment(
            ...     teacher, course, class_obj,
            ...     name="第一次作业",
            ...     storage_type="filesystem"
            ... )
            >>> # 创建Git类型作业
            >>> assignment = service.create_assignment(
            ...     teacher, course, class_obj,
            ...     name="算法作业",
            ...     storage_type="git",
            ...     git_url="https://github.com/user/repo.git",
            ...     git_branch="main"
            ... )
        """
        from grading.assignment_utils import CredentialEncryption, PathValidator, ValidationError
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter

        # 验证教师权限
        if not teacher or not teacher.is_authenticated:
            raise PermissionError("用户未认证")

        # 验证租户
        try:
            tenant = teacher.profile.tenant
        except AttributeError:
            raise PermissionError("用户没有关联的租户")

        # 验证作业名称
        if not name or not name.strip():
            raise ValidationError("作业名称不能为空", "请输入作业名称")

        # 清理作业名称
        try:
            clean_name = PathValidator.sanitize_name(name)
        except ValidationError as e:
            raise ValidationError(f"作业名称验证失败: {e.message}", e.user_message)

        # 验证存储类型
        if storage_type not in ["git", "filesystem"]:
            raise ValidationError(
                f"Invalid storage_type: {storage_type}", "存储类型必须是 'git' 或 'filesystem'"
            )

        # 验证课程和班级关联
        if class_obj.course != course:
            raise ValidationError(
                f"班级 {class_obj.name} 不属于课程 {course.name}",
                "所选班级不属于该课程，请重新选择",
            )

        # 验证课程和班级的租户
        if course.tenant != tenant:
            raise ValidationError(
                f"课程 {course.name} 不属于租户 {tenant.name}", "所选课程不属于您的租户"
            )

        if class_obj.tenant != tenant:
            raise ValidationError(
                f"班级 {class_obj.name} 不属于租户 {tenant.name}", "所选班级不属于您的租户"
            )

        # 检查重复配置（Requirement 8.5）
        duplicate = Assignment.objects.filter(
            owner=teacher, course=course, class_obj=class_obj, name=clean_name, is_active=True
        ).exists()

        if duplicate:
            raise ValidationError(
                f"Duplicate assignment: {clean_name}",
                f"该课程和班级下已存在名为'{clean_name}'的作业配置",
            )

        # 准备创建参数
        create_params = {
            "owner": teacher,
            "tenant": tenant,
            "course": course,
            "class_obj": class_obj,
            "name": clean_name,
            "storage_type": storage_type,
            "description": kwargs.get("description", ""),
            "is_active": True,
        }

        # 根据存储类型验证和设置特定字段
        if storage_type == "git":
            # Git类型必填字段验证
            git_url = kwargs.get("git_url", "").strip()
            if not git_url:
                raise ValidationError(
                    "Git URL is required for git storage type", "Git类型作业必须提供仓库URL"
                )

            # 简单的URL格式验证（Requirement 8.4）
            # 支持 http://, https://, git://, ssh://, git@
            if not (
                git_url.startswith("http://")
                or git_url.startswith("https://")
                or git_url.startswith("git@")
                or git_url.startswith("git://")
                or git_url.startswith("ssh://")
            ):
                raise ValidationError(
                    f"Invalid Git URL format: {git_url}",
                    "Git URL格式不正确，应以 http://, https://, git@, git:// 或 ssh:// 开头",
                )

            create_params["git_url"] = git_url
            create_params["git_branch"] = kwargs.get("git_branch", "main").strip() or "main"
            create_params["git_username"] = kwargs.get("git_username", "").strip()

            # 处理Git密码加密
            git_password = kwargs.get("git_password", "").strip()
            if git_password:
                try:
                    create_params["git_password_encrypted"] = CredentialEncryption.encrypt(
                        git_password
                    )
                except Exception as e:
                    logger.error(f"Failed to encrypt git password: {str(e)}")
                    raise ValidationError(f"密码加密失败: {str(e)}", "密码加密失败，请重试")
            else:
                create_params["git_password_encrypted"] = ""

        elif storage_type == "filesystem":
            # 文件系统类型：生成基础路径（Requirement 4.1）
            base_path = self.get_class_assignment_path(course, class_obj)
            create_params["base_path"] = base_path

        # 创建作业记录
        try:
            assignment = Assignment.objects.create(**create_params)

            logger.info(
                f"Assignment created: id={assignment.id}, name={assignment.name}, "
                f"storage_type={storage_type}, teacher={teacher.username}, "
                f"course={course.name}, class={class_obj.name}"
            )

            # 如果是文件系统类型，创建基础目录
            if storage_type == "filesystem":
                try:
                    adapter = FileSystemStorageAdapter(base_path)
                    adapter.create_directory("")  # 创建基础目录
                    logger.info(
                        f"Created base directory for assignment {assignment.id}: {base_path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create base directory for assignment {assignment.id}: {e}. "
                        f"Directory will be created on first file upload."
                    )
                    # 不抛出异常，目录会在首次上传时创建

            return assignment

        except Exception as e:
            logger.error(f"Failed to create assignment: {str(e)}", exc_info=True)
            raise ValidationError(f"创建作业配置失败: {str(e)}", "创建失败，请重试")

    def list_assignments(
        self,
        teacher: User,
        course_id: Optional[int] = None,
        class_id: Optional[int] = None,
        storage_type: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> QuerySet[Assignment]:
        """获取作业列表，支持教师隔离和筛选

        实现需求:
        - Requirements 5.1: 教师只能看到自己创建的作业
        - Requirements 7.4: 支持按课程和班级筛选

        Args:
            teacher: 教师用户对象
            course_id: 可选的课程ID筛选
            class_id: 可选的班级ID筛选
            storage_type: 可选的存储类型筛选 ("git" 或 "filesystem")
            is_active: 是否只显示激活的作业，默认True

        Returns:
            QuerySet[Assignment]: 作业配置查询集，已按创建时间倒序排列

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 获取教师的所有作业
            >>> assignments = service.list_assignments(teacher)
            >>> # 获取特定课程的作业
            >>> assignments = service.list_assignments(teacher, course_id=1)
            >>> # 获取特定班级的作业
            >>> assignments = service.list_assignments(teacher, class_id=2)
            >>> # 获取Git类型的作业
            >>> assignments = service.list_assignments(teacher, storage_type="git")
        """
        # 基础查询：只返回该教师创建的作业（教师隔离）
        # 同时确保租户隔离
        queryset = Assignment.objects.filter(owner=teacher, tenant=teacher.profile.tenant)

        # 应用激活状态筛选
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        # 应用课程筛选
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)

        # 应用班级筛选
        if class_id is not None:
            queryset = queryset.filter(class_obj_id=class_id)

        # 应用存储类型筛选
        if storage_type is not None:
            if storage_type not in ["git", "filesystem"]:
                logger.warning(
                    f"Invalid storage_type filter: {storage_type}. "
                    f"Must be 'git' or 'filesystem'"
                )
            else:
                queryset = queryset.filter(storage_type=storage_type)

        # 优化查询：预加载关联对象以减少数据库查询
        queryset = queryset.select_related("owner", "tenant", "course", "class_obj")

        # 按创建时间倒序排列（最新的在前）
        queryset = queryset.order_by("-created_at")

        logger.info(
            f"Listed {queryset.count()} assignments for teacher {teacher.username} "
            f"(course_id={course_id}, class_id={class_id}, "
            f"storage_type={storage_type}, is_active={is_active})"
        )

        return queryset

    def get_teacher_courses(self, teacher: User) -> QuerySet[Course]:
        """获取教师的课程列表

        用于在作业列表页面提供课程筛选选项。

        Args:
            teacher: 教师用户对象

        Returns:
            QuerySet[Course]: 教师创建的作业所关联的课程列表（去重）
        """
        # 获取该教师所有作业关联的课程ID
        course_ids = (
            Assignment.objects.filter(owner=teacher, tenant=teacher.profile.tenant)
            .values_list("course_id", flat=True)
            .distinct()
        )

        # 返回这些课程
        return Course.objects.filter(id__in=course_ids).order_by("name")

    def get_teacher_classes(
        self, teacher: User, course_id: Optional[int] = None
    ) -> QuerySet[Class]:
        """获取教师的班级列表

        用于在作业列表页面提供班级筛选选项。
        如果指定了课程ID，则只返回该课程下的班级。

        Args:
            teacher: 教师用户对象
            course_id: 可选的课程ID，用于筛选特定课程的班级

        Returns:
            QuerySet[Class]: 教师创建的作业所关联的班级列表（去重）
        """
        # 基础查询
        queryset = Assignment.objects.filter(owner=teacher, tenant=teacher.profile.tenant)

        # 如果指定了课程，则筛选该课程的作业
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)

        # 获取班级ID列表
        class_ids = queryset.values_list("class_obj_id", flat=True).distinct()

        # 返回这些班级
        return Class.objects.filter(id__in=class_ids).order_by("name")

    def get_assignment_summary(self, teacher: User) -> Dict[str, Any]:
        """获取教师的作业统计摘要

        提供作业总数、各类型作业数量等统计信息。

        Args:
            teacher: 教师用户对象

        Returns:
            Dict[str, Any]: 包含统计信息的字典
            {
                'total': 总作业数,
                'active': 激活的作业数,
                'git_count': Git类型作业数,
                'filesystem_count': 文件系统类型作业数,
                'courses_count': 涉及的课程数,
                'classes_count': 涉及的班级数
            }
        """
        base_queryset = Assignment.objects.filter(owner=teacher, tenant=teacher.profile.tenant)

        return {
            "total": base_queryset.count(),
            "active": base_queryset.filter(is_active=True).count(),
            "git_count": base_queryset.filter(storage_type="git").count(),
            "filesystem_count": base_queryset.filter(storage_type="filesystem").count(),
            "courses_count": base_queryset.values("course").distinct().count(),
            "classes_count": base_queryset.values("class_obj").distinct().count(),
        }

    def update_assignment(
        self, assignment: Assignment, teacher: User, **update_fields
    ) -> Assignment:
        """更新作业配置

        实现需求:
        - Requirements 5.3: 允许查看和编辑配置详情
        - Requirements 5.4: 保留已提交的学生作业数据

        Args:
            assignment: 要更新的作业对象
            teacher: 执行更新的教师用户
            **update_fields: 要更新的字段，支持的字段包括:
                - name: 作业名称
                - description: 作业描述
                - is_active: 是否激活
                - git_url: Git仓库URL (仅Git类型)
                - git_branch: Git分支 (仅Git类型)
                - git_username: Git用户名 (仅Git类型)
                - git_password: Git密码明文 (仅Git类型，会自动加密)

        Returns:
            Assignment: 更新后的作业对象

        Raises:
            PermissionError: 如果教师不是作业的所有者
            ValidationError: 如果更新的字段值无效

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 更新作业名称和描述
            >>> assignment = service.update_assignment(
            ...     assignment,
            ...     teacher,
            ...     name="新作业名称",
            ...     description="更新后的描述"
            ... )
            >>> # 更新Git配置
            >>> assignment = service.update_assignment(
            ...     assignment,
            ...     teacher,
            ...     git_url="https://github.com/user/repo.git",
            ...     git_branch="develop"
            ... )
            >>> # 停用作业
            >>> assignment = service.update_assignment(
            ...     assignment,
            ...     teacher,
            ...     is_active=False
            ... )

        Note:
            - 不允许更改存储类型 (storage_type)
            - 不允许更改关联的课程和班级 (course, class_obj)
            - 这些限制是为了保护已提交的学生作业数据完整性
            - Git密码会自动加密存储
        """
        from grading.assignment_utils import CredentialEncryption, PathValidator, ValidationError

        # 权限检查：确保教师是作业的所有者
        if assignment.owner != teacher:
            logger.warning(
                f"Teacher {teacher.username} attempted to update assignment {assignment.id} "
                f"owned by {assignment.owner.username}"
            )
            raise PermissionError("您没有权限编辑此作业配置")

        # 租户检查：确保租户一致
        if assignment.tenant != teacher.profile.tenant:
            logger.warning(
                f"Teacher {teacher.username} attempted to update assignment {assignment.id} "
                f"from different tenant"
            )
            raise PermissionError("您没有权限编辑此作业配置")

        # 定义允许更新的字段
        # 注意：不允许更改 storage_type, course, class_obj, owner, tenant
        # 这些字段的更改可能会破坏已提交的学生作业数据
        allowed_fields = {
            "name",
            "description",
            "is_active",
            "git_url",
            "git_branch",
            "git_username",
            "git_password",
            "base_path",
        }

        # 过滤出有效的更新字段
        valid_updates = {}
        for field, value in update_fields.items():
            if field in allowed_fields:
                valid_updates[field] = value
            else:
                logger.warning(
                    f"Attempted to update restricted field '{field}' "
                    f"for assignment {assignment.id}"
                )

        # 如果没有有效的更新字段，直接返回
        if not valid_updates:
            logger.info(f"No valid fields to update for assignment {assignment.id}")
            return assignment

        # 验证和处理各个字段
        if "name" in valid_updates:
            name = valid_updates["name"]
            if not name or not name.strip():
                raise ValidationError("作业名称不能为空", "请输入有效的作业名称")

            # 清理名称中的特殊字符
            try:
                valid_updates["name"] = PathValidator.sanitize_name(name)
            except ValidationError as e:
                raise ValidationError(f"作业名称验证失败: {e.message}", e.user_message)

            # 检查名称唯一性（同一教师、课程、班级下不能有重名作业）
            duplicate = (
                Assignment.objects.filter(
                    owner=teacher,
                    course=assignment.course,
                    class_obj=assignment.class_obj,
                    name=valid_updates["name"],
                )
                .exclude(id=assignment.id)
                .exists()
            )

            if duplicate:
                raise ValidationError(
                    f"Duplicate assignment name: {valid_updates['name']}",
                    f"该课程和班级下已存在名为'{valid_updates['name']}'的作业配置",
                )

        # 处理Git密码加密
        if "git_password" in valid_updates:
            password = valid_updates.pop("git_password")  # 移除明文密码
            if password:
                try:
                    valid_updates["git_password_encrypted"] = CredentialEncryption.encrypt(password)
                except Exception as e:
                    logger.error(f"Failed to encrypt git password: {str(e)}")
                    raise ValidationError(f"密码加密失败: {str(e)}", "密码加密失败，请重试")
            else:
                # 如果密码为空，清空加密字段
                valid_updates["git_password_encrypted"] = ""

        # 验证Git配置（如果是Git类型作业）
        if assignment.storage_type == "git":
            if "git_url" in valid_updates:
                git_url = valid_updates["git_url"]
                if not git_url or not git_url.strip():
                    raise ValidationError("Git URL不能为空", "Git类型作业必须提供仓库URL")
                # 简单的URL格式验证
                if not (
                    git_url.startswith("http://")
                    or git_url.startswith("https://")
                    or git_url.startswith("git@")
                    or git_url.startswith("git://")
                    or git_url.startswith("ssh://")
                ):
                    raise ValidationError(
                        f"Invalid Git URL format: {git_url}",
                        "Git URL格式不正确，应以 http://, https://, git@ 或 git:// 开头",
                    )

        # 应用更新
        for field, value in valid_updates.items():
            setattr(assignment, field, value)

        # 保存更新
        try:
            assignment.save()
            logger.info(
                f"Assignment {assignment.id} updated by teacher {teacher.username}. "
                f"Updated fields: {list(valid_updates.keys())}"
            )
        except Exception as e:
            logger.error(f"Failed to save assignment {assignment.id}: {str(e)}", exc_info=True)
            raise ValidationError(f"保存作业配置失败: {str(e)}", "保存失败，请重试")

        return assignment

    def delete_assignment(
        self, assignment: Assignment, teacher: User, confirm: bool = False
    ) -> Dict[str, Any]:
        """删除作业配置

        实现需求:
        - Requirements 5.5: 提示确认并说明对已提交作业的影响

        Args:
            assignment: 要删除的作业对象
            teacher: 执行删除的教师用户
            confirm: 是否已确认删除，默认False

        Returns:
            Dict[str, Any]: 删除结果信息
            {
                'success': bool,  # 是否成功
                'deleted': bool,  # 是否已删除
                'message': str,   # 消息
                'impact': {       # 删除影响（仅在confirm=False时返回）
                    'assignment_name': str,
                    'course_name': str,
                    'class_name': str,
                    'storage_type': str,
                    'has_submissions': bool,  # 是否有提交的作业（未来扩展）
                    'warning': str  # 警告信息
                }
            }

        Raises:
            PermissionError: 如果教师不是作业的所有者

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 第一步：获取删除影响信息
            >>> result = service.delete_assignment(assignment, teacher, confirm=False)
            >>> if not result['deleted']:
            ...     print(result['impact']['warning'])
            ...     # 显示确认对话框
            >>>
            >>> # 第二步：确认删除
            >>> result = service.delete_assignment(assignment, teacher, confirm=True)
            >>> if result['success']:
            ...     print("删除成功")

        Note:
            - 删除是不可逆的操作
            - 删除作业配置不会删除文件系统中的实际文件
            - 对于Git类型作业，不会影响远程仓库
            - 未来如果有学生提交记录，也会一并删除（级联删除）
        """
        from grading.assignment_utils import ValidationError

        # 权限检查：确保教师是作业的所有者
        if assignment.owner != teacher:
            logger.warning(
                f"Teacher {teacher.username} attempted to delete assignment {assignment.id} "
                f"owned by {assignment.owner.username}"
            )
            raise PermissionError("您没有权限删除此作业配置")

        # 租户检查：确保租户一致
        if assignment.tenant != teacher.profile.tenant:
            logger.warning(
                f"Teacher {teacher.username} attempted to delete assignment {assignment.id} "
                f"from different tenant"
            )
            raise PermissionError("您没有权限删除此作业配置")

        # 收集删除影响信息
        impact_info = {
            "assignment_name": assignment.name,
            "course_name": assignment.course.name,
            "class_name": assignment.class_obj.name,
            "storage_type": "Git仓库" if assignment.storage_type == "git" else "文件上传",
            "has_submissions": False,  # 未来扩展：检查是否有学生提交
            "warning": "",
        }

        # 构建警告信息
        warnings = []
        warnings.append(f"您即将删除作业配置：{assignment.name}")
        warnings.append(f"课程：{assignment.course.name}")
        warnings.append(f"班级：{assignment.class_obj.name}")
        warnings.append(f"提交方式：{impact_info['storage_type']}")

        # 检查是否有相关的提交记录（未来扩展）
        # 注意：当前Assignment模型还没有与Submission的直接关联
        # 这是为未来的扩展预留的逻辑
        # 如果未来添加了assignment字段到Submission模型，可以这样检查：
        # submission_count = Submission.objects.filter(assignment=assignment).count()
        # if submission_count > 0:
        #     impact_info['has_submissions'] = True
        #     warnings.append(f"警告：此作业配置下有 {submission_count} 条学生提交记录，删除后将无法恢复！")

        # 添加文件系统说明
        if assignment.storage_type == "filesystem":
            warnings.append("注意：删除作业配置不会删除文件系统中已上传的作业文件。")
        elif assignment.storage_type == "git":
            warnings.append("注意：删除作业配置不会影响远程Git仓库的内容。")

        warnings.append("此操作不可撤销，请确认是否继续？")

        impact_info["warning"] = "\n".join(warnings)

        # 如果未确认，返回影响信息
        if not confirm:
            logger.info(
                f"Delete impact check for assignment {assignment.id} by teacher {teacher.username}"
            )
            return {
                "success": True,
                "deleted": False,
                "message": "请确认删除操作",
                "impact": impact_info,
            }

        # 确认删除，执行删除操作
        assignment_id = assignment.id
        assignment_name = assignment.name

        try:
            # Django的CASCADE会自动处理级联删除
            # 如果未来有Submission等关联模型，它们会被自动删除
            assignment.delete()

            logger.info(
                f"Assignment {assignment_id} ('{assignment_name}') deleted by teacher {teacher.username}. "
                f"Course: {impact_info['course_name']}, Class: {impact_info['class_name']}"
            )

            return {
                "success": True,
                "deleted": True,
                "message": f"作业配置 '{assignment_name}' 已成功删除",
                "impact": impact_info,
            }

        except Exception as e:
            logger.error(f"Failed to delete assignment {assignment_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "deleted": False,
                "message": f"删除失败：{str(e)}",
                "impact": impact_info,
            }

    def get_student_courses(self, student: User) -> QuerySet[Course]:
        """获取学生的课程列表（按学生班级过滤）

        实现需求:
        - Requirements 9.1: 学生只能看到所在班级的课程

        注意：当前实现基于学生租户内的活跃作业配置。
        未来可以扩展为基于学生-班级关联关系。

        Args:
            student: 学生用户对象

        Returns:
            QuerySet[Course]: 学生所在班级的课程列表

        Examples:
            >>> service = AssignmentManagementService()
            >>> courses = service.get_student_courses(student)
            >>> for course in courses:
            ...     print(course.name)
        """
        from grading.models import Class, Submission

        # 方案1：通过作业提交记录反向查找学生的班级
        # 获取学生提交过作业的所有班级
        class_ids = (
            Submission.objects.filter(student=student)
            .values_list("homework__class_obj_id", flat=True)
            .distinct()
        )

        if class_ids:
            # 获取这些班级关联的课程
            courses = (
                Course.objects.filter(classes__id__in=class_ids)
                .distinct()
                .select_related("semester")
                .order_by("-semester__start_date", "name")
            )

            logger.info(
                f"Retrieved {courses.count()} courses for student {student.username} (from submissions)"
            )

            return courses

        # 方案2：如果没有提交记录，返回学生租户内所有有活跃作业配置的课程
        # 这是一个临时方案，直到实现完整的学生-班级关联
        try:
            tenant = student.profile.tenant

            # 获取该租户内所有有活跃作业配置的课程
            courses = (
                Course.objects.filter(tenant=tenant, assignments__is_active=True)
                .distinct()
                .select_related("semester")
                .order_by("-semester__start_date", "name")
            )

            logger.info(
                f"Retrieved {courses.count()} courses for student {student.username} (from tenant assignments)"
            )

            return courses

        except Exception as e:
            logger.warning(f"Could not retrieve courses for student {student.username}: {e}")
            return Course.objects.none()

    def get_assignment_structure(self, assignment: Assignment, path: str = "") -> Dict[str, Any]:
        """获取作业目录结构

        直接从远程仓库或本地文件系统读取目录结构。

        实现需求:
        - Requirements 3.2: 直接从远程 Git 仓库读取该课程的目录结构
        - Requirements 3.3: 列出该课程下的所有作业目录和学生提交情况
        - Requirements 3.5: 向教师用户显示友好的错误消息而不是技术错误信息

        Args:
            assignment: 作业配置对象
            path: 相对路径（默认为根目录）

        Returns:
            包含目录结构的字典，格式：
            {
                "success": True/False,
                "path": "路径",
                "entries": [{"name": "文件名", "type": "file/dir", ...}],
                "error": "错误消息"（仅在失败时）
            }

        Examples:
            >>> service = AssignmentManagementService()
            >>> result = service.get_assignment_structure(assignment)
            >>> if result['success']:
            ...     for entry in result['entries']:
            ...         print(f"{entry['name']} ({entry['type']})")
            >>> else:
            ...     print(result['error'])
        """
        from grading.services.storage_adapter import RemoteAccessError, StorageError

        try:
            # 获取存储适配器
            adapter = self._get_storage_adapter(assignment)

            # 列出目录内容
            entries = adapter.list_directory(path)

            logger.info(
                f"Successfully retrieved assignment structure for assignment {assignment.id}, "
                f"path: '{path}', entries: {len(entries)}"
            )

            return {"success": True, "path": path, "entries": entries}

        except RemoteAccessError as e:
            # 友好的错误消息（Requirement 3.5）
            logger.error(
                f"Remote access error for assignment {assignment.id}: {e.message}",
                extra={
                    "assignment_id": assignment.id,
                    "path": path,
                    "user_message": e.user_message,
                    "details": e.details,
                },
            )
            return {"success": False, "path": path, "error": e.user_message}

        except StorageError as e:
            # 其他存储错误
            logger.error(
                f"Storage error for assignment {assignment.id}: {e.message}",
                extra={
                    "assignment_id": assignment.id,
                    "path": path,
                    "user_message": e.user_message,
                    "details": e.details,
                },
            )
            return {"success": False, "path": path, "error": e.user_message}

        except Exception as e:
            # 未预期的错误
            logger.error(
                f"Unexpected error getting assignment structure for assignment {assignment.id}: {str(e)}",
                exc_info=True,
                extra={"assignment_id": assignment.id, "path": path},
            )
            return {
                "success": False,
                "path": path,
                "error": "无法访问作业目录，请检查配置或稍后重试",
            }

    def _get_storage_adapter(self, assignment: Assignment):
        """获取存储适配器

        根据作业配置的存储类型返回相应的存储适配器实例。
        这是存储抽象层的核心方法，实现了统一的存储访问接口。

        设计模式：
            使用适配器模式（Adapter Pattern）统一Git和文件系统的访问接口。
            这样业务逻辑层无需关心底层存储实现，只需调用统一的接口方法。

        Git存储适配器特性：
            - 直接访问远程仓库，无需本地克隆（Requirements 3.6, 10.1）
            - 使用git ls-tree读取目录结构（Requirements 10.2）
            - 使用git show读取文件内容（Requirements 10.3）
            - 内存缓存提高性能（Requirements 10.4）
            - 密码自动解密处理

        文件系统适配器特性：
            - 访问本地文件系统
            - 自动创建目录结构（Requirements 4.6）
            - 路径安全验证，防止路径遍历攻击

        Args:
            assignment: 作业配置对象

        Returns:
            StorageAdapter: Git 或文件系统存储适配器实例

        Raises:
            ValidationError: 如果存储类型无效或配置不完整

        Examples:
            >>> service = AssignmentManagementService()
            >>> adapter = service._get_storage_adapter(assignment)
            >>> # 使用统一接口访问存储
            >>> entries = adapter.list_directory("")
            >>> content = adapter.read_file("第一次作业/homework.docx")
        """
        from grading.assignment_utils import CredentialEncryption, ValidationError
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter
        from grading.services.git_storage_adapter import GitStorageAdapter

        if assignment.storage_type == "git":
            # Git 存储适配器
            if not assignment.git_url:
                raise ValidationError(
                    f"Git URL not configured for assignment {assignment.id}", "Git 仓库 URL 未配置"
                )

            # 解密密码
            password = ""
            if assignment.git_password_encrypted:
                try:
                    password = CredentialEncryption.decrypt(assignment.git_password_encrypted)
                except Exception as e:
                    logger.warning(
                        f"Failed to decrypt git password for assignment {assignment.id}: {e}"
                    )
                    # 继续使用空密码，可能是公开仓库

            return GitStorageAdapter(
                git_url=assignment.git_url,
                branch=assignment.git_branch or "main",
                username=assignment.git_username or "",
                password=password,
            )

        elif assignment.storage_type == "filesystem":
            # 文件系统存储适配器
            if not assignment.base_path:
                raise ValidationError(
                    f"Base path not configured for assignment {assignment.id}", "文件系统路径未配置"
                )

            return FileSystemStorageAdapter(assignment.base_path)

        else:
            raise ValidationError(
                f"Invalid storage type: {assignment.storage_type}",
                f"不支持的存储类型: {assignment.storage_type}",
            )

    def get_assignment_directories(
        self, assignment: Assignment, path: str = ""
    ) -> List[Dict[str, Any]]:
        """获取作业次数目录列表

        实现需求:
        - Requirements 9.2: 显示现有的作业次数目录列表

        Args:
            assignment: 作业配置对象
            path: 相对路径，默认为根目录

        Returns:
            List[Dict]: 目录列表，每个字典包含:
                - name: 目录名称
                - type: 类型（"dir" 或 "file"）
                - path: 完整路径
                - is_assignment_number: 是否为作业次数目录

        Examples:
            >>> service = AssignmentManagementService()
            >>> dirs = service.get_assignment_directories(assignment)
            >>> for dir in dirs:
            ...     if dir['is_assignment_number']:
            ...         print(dir['name'])
        """
        from grading.assignment_utils import PathValidator

        try:
            # 使用 get_assignment_structure 获取目录结构
            result = self.get_assignment_structure(assignment, path)

            if not result["success"]:
                logger.warning(f"Failed to get assignment structure: {result.get('error')}")
                return []

            # 过滤出目录，并标记是否为作业次数目录
            directories = []
            for entry in result.get("entries", []):
                if entry.get("type") == "dir":
                    dir_name = entry.get("name", "")
                    is_assignment_number = PathValidator.validate_assignment_number_format(dir_name)

                    directories.append(
                        {
                            "name": dir_name,
                            "type": "dir",
                            "path": os.path.join(path, dir_name) if path else dir_name,
                            "is_assignment_number": is_assignment_number,
                            "size": entry.get("size", 0),
                            "modified": entry.get("modified"),
                        }
                    )

            # 按名称排序
            directories.sort(key=lambda x: x["name"])

            logger.info(
                f"Retrieved {len(directories)} directories for assignment {assignment.id}, "
                f"path: {path}"
            )

            return directories

        except Exception as e:
            logger.error(
                f"Failed to get assignment directories for assignment {assignment.id}: {e}",
                exc_info=True,
            )
            return []

    def upload_student_file(
        self,
        assignment: Assignment,
        student: User,
        file: Any,  # UploadedFile
        assignment_number_path: str,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """处理学生文件上传

        实现需求:
        - Requirements 9.5: 自动在文件名中添加或验证学生姓名
        - Requirements 9.6: 验证文件格式
        - Requirements 9.7: 重复上传时覆盖旧文件

        Args:
            assignment: 作业配置对象
            student: 学生用户
            file: 上传的文件对象
            assignment_number_path: 作业次数目录路径（如"第一次作业"）
            filename: 可选的自定义文件名

        Returns:
            Dict[str, Any]: 上传结果
            {
                'success': bool,
                'message': str,
                'file_path': str,  # 文件保存路径
                'file_name': str,  # 最终文件名
                'file_size': int   # 文件大小
            }

        Raises:
            ValidationError: 如果验证失败

        Examples:
            >>> service = AssignmentManagementService()
            >>> result = service.upload_student_file(
            ...     assignment, student, file, "第一次作业"
            ... )
            >>> if result['success']:
            ...     print(f"上传成功: {result['file_name']}")
        """
        from grading.assignment_utils import PathValidator, ValidationError
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter

        # 只支持文件系统存储
        if assignment.storage_type != "filesystem":
            raise ValidationError(
                "Only filesystem storage supports file upload", "只有文件上传方式的作业支持此操作"
            )

        # 验证文件
        if not file:
            raise ValidationError("No file provided", "未提供文件")

        # 获取文件名
        original_filename = filename or getattr(file, "name", "unnamed_file")

        # 验证文件格式
        file_ext = os.path.splitext(original_filename)[1].lower()
        supported_formats = [
            ".docx",
            ".doc",
            ".pdf",
            ".txt",
            ".xlsx",
            ".xls",
            ".zip",
            ".rar",
            ".jpg",
            ".png",
        ]

        if file_ext not in supported_formats:
            raise ValidationError(
                f"Unsupported file format: {file_ext}",
                f"不支持的文件格式: {file_ext}（支持的格式: {', '.join(supported_formats)}）",
            )

        # 验证文件大小
        file_size = getattr(file, "size", 0)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise ValidationError(
                f"File too large: {file_size} bytes",
                f"文件过大（最大: {max_size // (1024*1024)}MB）",
            )

        # 处理文件名：确保包含学生姓名
        student_name = student.get_full_name() or student.username

        # 检查文件名是否已包含学生姓名
        if student_name not in original_filename:
            # 自动添加学生姓名前缀
            base_name, ext = os.path.splitext(original_filename)
            final_filename = f"{student_name}-{base_name}{ext}"
        else:
            final_filename = original_filename

        # 清理文件名
        final_filename = PathValidator.sanitize_name(final_filename)

        # 构建文件路径
        # 格式: <base_path>/<assignment_number_path>/<filename>
        file_path = os.path.join(
            assignment.base_path,
            PathValidator.sanitize_name(assignment_number_path),
            final_filename,
        )

        try:
            # 使用文件系统适配器保存文件
            adapter = FileSystemStorageAdapter(assignment.base_path)

            # 读取文件内容
            if hasattr(file, "read"):
                content = file.read()
                if hasattr(file, "seek"):
                    file.seek(0)  # 重置文件指针
            else:
                raise ValidationError("Invalid file object", "无效的文件对象")

            # 写入文件（会自动覆盖已存在的文件）
            relative_path = os.path.join(
                PathValidator.sanitize_name(assignment_number_path), final_filename
            )
            adapter.write_file(relative_path, content)

            logger.info(
                f"Student {student.username} uploaded file to assignment {assignment.id}: "
                f"{final_filename} ({file_size} bytes)"
            )

            return {
                "success": True,
                "message": "文件上传成功",
                "file_path": file_path,
                "file_name": final_filename,
                "file_size": file_size,
            }

        except Exception as e:
            logger.error(
                f"Failed to upload file for student {student.username}: {e}", exc_info=True
            )
            raise ValidationError(f"File upload failed: {str(e)}", f"文件上传失败: {str(e)}")

    def create_assignment_number_directory(
        self,
        assignment: Assignment,
        auto_generate_name: bool = True,
        custom_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建作业次数目录

        实现需求:
        - Requirements 4.4: 允许学生创建新的作业次数目录
        - Requirements 9.3: 根据已有作业次数自动生成下一个作业目录名称
        - Requirements 9.4: 遵循统一的命名规范
        - Requirements 9.8: 立即显示该目录并允许上传文件

        Args:
            assignment: 作业配置对象
            auto_generate_name: 是否自动生成名称，默认True
            custom_name: 自定义名称（当auto_generate_name=False时使用）

        Returns:
            Dict[str, Any]: 创建结果
            {
                'success': bool,
                'message': str,
                'directory_name': str,  # 创建的目录名称
                'directory_path': str   # 完整路径
            }

        Raises:
            ValidationError: 如果验证失败或创建失败

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 自动生成名称
            >>> result = service.create_assignment_number_directory(assignment)
            >>> print(result['directory_name'])  # "第一次作业"
            >>>
            >>> # 使用自定义名称
            >>> result = service.create_assignment_number_directory(
            ...     assignment, auto_generate_name=False, custom_name="第一次实验"
            ... )
        """
        from grading.assignment_utils import PathValidator, ValidationError
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter

        # 只支持文件系统存储
        if assignment.storage_type != "filesystem":
            raise ValidationError(
                "Only filesystem storage supports directory creation",
                "只有文件上传方式的作业支持此操作",
            )

        try:
            # 获取存储适配器
            adapter = FileSystemStorageAdapter(assignment.base_path)

            # 确定目录名称
            if auto_generate_name:
                # 自动生成名称
                # 首先获取现有的作业次数目录
                existing_dirs = self.get_assignment_directories(assignment)

                # 提取作业次数编号
                existing_numbers = []
                for dir_info in existing_dirs:
                    if dir_info.get("is_assignment_number"):
                        dir_name = dir_info["name"]
                        # 尝试从名称中提取数字
                        # 支持格式：第N次作业、第N次实验等
                        import re

                        match = re.search(r"第([一二三四五六七八九十\d]+)次", dir_name)
                        if match:
                            num_str = match.group(1)
                            # 转换中文数字或阿拉伯数字
                            try:
                                if num_str.isdigit():
                                    existing_numbers.append(int(num_str))
                                else:
                                    # 简单的中文数字转换
                                    chinese_to_num = {
                                        "一": 1,
                                        "二": 2,
                                        "三": 3,
                                        "四": 4,
                                        "五": 5,
                                        "六": 6,
                                        "七": 7,
                                        "八": 8,
                                        "九": 9,
                                        "十": 10,
                                    }
                                    if num_str in chinese_to_num:
                                        existing_numbers.append(chinese_to_num[num_str])
                            except (ValueError, KeyError):
                                pass

                # 生成新的作业次数名称
                directory_name = PathValidator.generate_assignment_number_name(existing_numbers)
            else:
                # 使用自定义名称
                if not custom_name:
                    raise ValidationError(
                        "Custom name required when auto_generate_name=False", "未提供自定义名称"
                    )

                # 验证自定义名称格式
                if not PathValidator.validate_assignment_number_format(custom_name):
                    raise ValidationError(
                        f"Invalid assignment number format: {custom_name}",
                        f"作业次数格式不正确: {custom_name}（应为'第N次作业'格式）",
                    )

                directory_name = custom_name

            # 清理目录名称
            directory_name = PathValidator.sanitize_name(directory_name)

            # 检查目录是否已存在
            existing_dirs = self.get_assignment_directories(assignment)
            if any(d["name"] == directory_name for d in existing_dirs):
                raise ValidationError(
                    f"Directory already exists: {directory_name}", f"目录已存在: {directory_name}"
                )

            # 创建目录
            adapter.create_directory(directory_name)

            # 构建完整路径
            directory_path = os.path.join(assignment.base_path, directory_name)

            logger.info(
                f"Created assignment number directory for assignment {assignment.id}: "
                f"{directory_name}"
            )

            return {
                "success": True,
                "message": f"成功创建作业目录: {directory_name}",
                "directory_name": directory_name,
                "directory_path": directory_path,
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create assignment number directory for assignment {assignment.id}: {e}",
                exc_info=True,
            )
            raise ValidationError(f"Directory creation failed: {str(e)}", f"创建目录失败: {str(e)}")

    def generate_file_storage_path(
        self,
        assignment: Assignment,
        assignment_number: str,
        filename: str,
        student: Optional[User] = None,
    ) -> str:
        """生成文件存储路径

        实现需求:
        - Requirements 4.2: 文件存储在 <课程名称>/<班级名称>/<作业次数>/ 格式的路径中
        - Requirements 7.3: 为每个班级维护独立的作业目录

        Args:
            assignment: 作业配置对象
            assignment_number: 作业次数（如"第一次作业"）
            filename: 文件名
            student: 可选的学生用户（用于生成学生特定的子目录）

        Returns:
            str: 完整的文件存储路径

        Examples:
            >>> service = AssignmentManagementService()
            >>> path = service.generate_file_storage_path(
            ...     assignment, "第一次作业", "homework.docx"
            ... )
            >>> # 返回: "<base_path>/第一次作业/homework.docx"
            >>>
            >>> # 带学生信息
            >>> path = service.generate_file_storage_path(
            ...     assignment, "第一次作业", "homework.docx", student
            ... )
            >>> # 返回: "<base_path>/第一次作业/学生姓名/homework.docx"
        """
        from grading.assignment_utils import PathValidator

        # 清理路径组件
        clean_assignment_number = PathValidator.sanitize_name(assignment_number)
        clean_filename = PathValidator.sanitize_name(filename)

        # 构建路径组件
        path_components = [assignment.base_path, clean_assignment_number]

        # 如果提供了学生信息，添加学生子目录
        if student:
            student_name = student.get_full_name() or student.username
            clean_student_name = PathValidator.sanitize_name(student_name)
            path_components.append(clean_student_name)

        # 添加文件名
        path_components.append(clean_filename)

        # 组合路径
        full_path = os.path.join(*path_components)

        logger.debug(f"Generated file storage path for assignment {assignment.id}: {full_path}")

        return full_path

    def validate_class_directory_isolation(self, assignment: Assignment, path: str) -> bool:
        """验证班级目录隔离

        实现需求:
        - Requirements 7.3: 为每个班级维护独立的作业目录

        确保路径在作业配置的基础路径内，防止跨班级访问。

        Args:
            assignment: 作业配置对象
            path: 要验证的路径

        Returns:
            bool: 是否通过验证

        Raises:
            ValidationError: 如果路径不安全

        Examples:
            >>> service = AssignmentManagementService()
            >>> # 验证路径是否在作业的基础路径内
            >>> is_valid = service.validate_class_directory_isolation(
            ...     assignment, "第一次作业/homework.docx"
            ... )
        """
        from grading.assignment_utils import PathValidator, ValidationError

        # 获取基础路径的绝对路径
        base_path = os.path.abspath(assignment.base_path)

        # 获取目标路径的绝对路径
        if os.path.isabs(path):
            target_path = os.path.abspath(path)
        else:
            target_path = os.path.abspath(os.path.join(assignment.base_path, path))

        # 确保目标路径在基础路径内
        if not target_path.startswith(base_path):
            logger.warning(
                f"Path traversal attempt detected for assignment {assignment.id}: "
                f"base={base_path}, target={target_path}"
            )
            raise ValidationError(
                f"Path traversal attempt: {path}", "无效的路径：不允许访问班级目录之外的文件"
            )

        logger.debug(f"Path validation passed for assignment {assignment.id}: {path}")

        return True

    def get_class_assignment_path(self, course: Course, class_obj: Class) -> str:
        """获取班级作业路径

        根据课程和班级信息生成标准化的作业存储路径。
        这个方法确保了不同班级的作业文件存储在独立的目录中。

        实现需求:
        - Requirements 4.1: 根据课程名称和班级名称生成基础目录路径
        - Requirements 7.3: 为每个班级维护独立的作业目录

        路径生成规则：
        1. 使用PathValidator.sanitize_name()清理课程和班级名称
        2. 移除特殊字符，确保文件系统兼容性（Requirements 4.7）
        3. 格式: <课程名称>/<班级名称>/
        4. 末尾包含斜杠，表示这是一个目录路径

        班级隔离：
        不同班级即使在同一课程下，也会有独立的目录：
        - 数据结构/计算机1班/
        - 数据结构/计算机2班/

        这确保了：
        - 不同班级的学生作业不会混淆
        - 教师可以独立管理每个班级的作业
        - 支持同一课程多个班级的场景

        Args:
            course: 课程对象
            class_obj: 班级对象

        Returns:
            str: 班级作业基础路径，格式为 <课程名称>/<班级名称>/

        Examples:
            >>> service = AssignmentManagementService()
            >>> path = service.get_class_assignment_path(course, class_obj)
            >>> # 返回: "数据结构/计算机1班/"
            >>>
            >>> # 特殊字符会被清理
            >>> # 输入: "C++程序设计", "软件1班"
            >>> # 返回: "C程序设计/软件1班/"
        """
        from grading.assignment_utils import PathValidator

        # 清理课程名称和班级名称
        clean_course_name = PathValidator.sanitize_name(course.name)
        clean_class_name = PathValidator.sanitize_name(class_obj.name)

        # 构建路径
        path = os.path.join(clean_course_name, clean_class_name, "")

        logger.debug(
            f"Generated class assignment path: {path} "
            f"(course={course.name}, class={class_obj.name})"
        )

        return path
