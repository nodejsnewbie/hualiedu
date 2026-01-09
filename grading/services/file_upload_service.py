"""
文件上传服务模块

提供学生作业文件上传功能，包括：
- 上传作业文件
- 验证文件格式和大小
- 保存文件到指定路径
- 创建提交记录
- 版本管理
"""

import logging
import os
from typing import Optional, Tuple

from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from grading.models import Homework, Repository, Submission

# 配置日志
logger = logging.getLogger(__name__)

# 支持的文件格式
SUPPORTED_FILE_FORMATS = [
    ".docx",  # Word文档
    ".doc",  # 旧版Word文档
    ".txt",  # 文本文件
    ".pdf",  # PDF文件
    ".xlsx",  # Excel文件
    ".xls",  # 旧版Excel文件
    ".zip",  # 压缩文件
    ".rar",  # 压缩文件
]

# 默认最大文件大小（50MB）
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


class FileUploadService:
    """文件上传服务

    负责学生作业文件的上传、验证和管理。
    仅支持文件系统方式的仓库。
    """

    def __init__(self, max_file_size: Optional[int] = None):
        """初始化文件上传服务

        Args:
            max_file_size: 最大文件大小（字节），默认50MB
        """
        self.max_file_size = max_file_size or DEFAULT_MAX_FILE_SIZE

    @transaction.atomic
    def upload_submission(
        self,
        student: User,
        homework: Homework,
        file: UploadedFile,
        repository: Optional[Repository] = None,
    ) -> Submission:
        """上传作业文件

        Args:
            student: 提交作业的学生
            homework: 作业对象
            file: 上传的文件对象
            repository: 仓库对象（可选，如果不提供则从homework获取）

        Returns:
            创建的提交记录

        Raises:
            ValueError: 如果参数无效或验证失败
        """
        # 验证必需参数
        if not student:
            raise ValueError("必须指定学生")

        if not homework:
            raise ValueError("必须指定作业")

        if not file:
            raise ValueError("必须提供文件")

        # 获取仓库
        if not repository:
            # 从作业的班级获取仓库
            if not homework.class_obj:
                raise ValueError("作业未关联班级，无法确定仓库")

            # 获取该班级的文件系统仓库
            repositories = Repository.objects.filter(
                class_obj=homework.class_obj, repo_type="filesystem", is_active=True
            )

            if not repositories.exists():
                raise ValueError("该班级没有配置文件系统仓库")

            repository = repositories.first()

        # 验证仓库类型
        if repository.repo_type != "filesystem":
            raise ValueError("只有文件系统方式的仓库支持文件上传")

        # 验证文件
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise ValueError(error_msg)

        # 检查是否已有提交记录（用于版本管理）
        existing_submission = (
            Submission.objects.filter(homework=homework, student=student)
            .order_by("-version")
            .first()
        )

        version = 1
        if existing_submission:
            version = existing_submission.version + 1

        # 生成文件保存路径
        file_path = self._generate_file_path(repository, homework, student, file.name)

        # 保存文件
        self.save_file(file, file_path)

        # 创建提交记录
        submission = self.create_submission_record(
            student=student,
            homework=homework,
            repository=repository,
            file_path=file_path,
            file_name=file.name,
            file_size=file.size,
            version=version,
        )

        logger.info(
            f"学生 {student.username} 成功上传作业: {homework.title} "
            f"(文件: {file.name}, 大小: {file.size} bytes, 版本: {version})"
        )

        return submission

    def validate_file(self, file: UploadedFile) -> Tuple[bool, str]:
        """验证文件格式和大小

        Args:
            file: 上传的文件对象

        Returns:
            (是否有效, 错误信息)
        """
        # 验证文件是否存在
        if not file:
            return False, "未提供文件"

        # 验证文件名
        if not file.name:
            return False, "文件名为空"

        # 验证文件大小
        if file.size <= 0:
            return False, "文件大小为0"

        if file.size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            actual_size_mb = file.size / (1024 * 1024)
            return (
                False,
                f"文件大小超过限制 (最大: {max_size_mb:.1f}MB, 实际: {actual_size_mb:.1f}MB)",
            )

        # 验证文件格式
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in SUPPORTED_FILE_FORMATS:
            supported_formats = ", ".join(SUPPORTED_FILE_FORMATS)
            return (
                False,
                f"不支持的文件格式: {file_ext} (支持的格式: {supported_formats})",
            )

        logger.debug(f"文件验证通过: {file.name} (大小: {file.size} bytes, 格式: {file_ext})")
        return True, ""

    def save_file(self, file: UploadedFile, file_path: str) -> str:
        """保存文件到指定路径

        Args:
            file: 上传的文件对象
            file_path: 文件保存路径（相对路径）

        Returns:
            完整的文件路径

        Raises:
            ValueError: 如果保存失败
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            # 保存文件
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            logger.info(f"文件保存成功: {file_path}")
            return file_path

        except PermissionError as e:
            error_msg = f"无权限写入文件: {file_path}"
            logger.error(f"{error_msg}, 错误: {e}")
            raise ValueError(error_msg)
        except OSError as e:
            error_msg = f"保存文件失败: {file_path}"
            logger.error(f"{error_msg}, 错误: {e}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"保存文件时发生未知错误: {file_path}"
            logger.error(f"{error_msg}, 错误: {e}")
            raise ValueError(error_msg)

    def create_submission_record(
        self,
        student: User,
        homework: Homework,
        repository: Repository,
        file_path: str,
        file_name: str,
        file_size: int,
        version: int = 1,
    ) -> Submission:
        """创建提交记录

        Args:
            student: 提交学生
            homework: 作业对象
            repository: 仓库对象
            file_path: 文件路径
            file_name: 文件名
            file_size: 文件大小（字节）
            version: 版本号

        Returns:
            创建的提交记录
        """
        # 获取租户
        tenant = None
        if hasattr(student, "profile") and student.profile:
            tenant = student.profile.tenant
        elif homework.tenant:
            tenant = homework.tenant

        # 创建提交记录
        submission = Submission.objects.create(
            tenant=tenant,
            homework=homework,
            student=student,
            repository=repository,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            version=version,
            submitted_at=timezone.now(),
        )

        logger.info(
            f"创建提交记录: 学生={student.username}, 作业={homework.title}, "
            f"文件={file_name}, 版本={version}"
        )

        return submission

    def _generate_file_path(
        self, repository: Repository, homework: Homework, student: User, filename: str
    ) -> str:
        """生成文件保存路径

        路径格式：<仓库路径>/课程/班级/作业批次/学号_姓名/文件名

        Args:
            repository: 仓库对象
            homework: 作业对象
            student: 学生用户
            filename: 原始文件名

        Returns:
            完整的文件路径
        """
        # 获取仓库根目录
        repo_path = repository.get_full_path()

        # 获取课程名称
        course_name = homework.course.name if homework.course else "未知课程"

        # 获取班级名称
        class_name = homework.class_obj.name if homework.class_obj else "未知班级"

        # 获取作业批次名称
        homework_folder = homework.folder_name

        # 生成学生目录名：学号_姓名
        student_id = getattr(student, "username", "unknown")
        student_name = getattr(student, "first_name", "") or getattr(student, "last_name", "")
        if student_name:
            student_folder = f"{student_id}_{student_name}"
        else:
            student_folder = student_id

        # 清理文件名中的特殊字符
        safe_filename = self._sanitize_filename(filename)

        # 构建完整路径
        file_path = os.path.join(
            repo_path,
            self._sanitize_filename(course_name),
            self._sanitize_filename(class_name),
            self._sanitize_filename(homework_folder),
            self._sanitize_filename(student_folder),
            safe_filename,
        )

        return file_path

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全的字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 移除路径分隔符和其他不安全字符
        # 使用临时占位符来处理".."，避免与"/"替换后的"_"冲突
        safe_name = filename.replace("..", "<<<DOTDOT>>>")

        unsafe_chars = ["/", "\\", "\0", "\n", "\r", "\t"]
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, "_")

        # 将占位符替换为".._"
        safe_name = safe_name.replace("<<<DOTDOT>>>", ".._")

        # 移除首尾空格
        safe_name = safe_name.strip()

        # 如果文件名为空，使用默认名称
        if not safe_name:
            safe_name = "unnamed_file"

        return safe_name

    def get_submission_history(self, homework: Homework, student: User) -> list[Submission]:
        """获取学生的作业提交历史

        Args:
            homework: 作业对象
            student: 学生用户

        Returns:
            提交记录列表，按版本号降序排列
        """
        submissions = Submission.objects.filter(homework=homework, student=student).order_by(
            "-version"
        )

        return list(submissions)

    def get_latest_submission(self, homework: Homework, student: User) -> Optional[Submission]:
        """获取学生的最新提交

        Args:
            homework: 作业对象
            student: 学生用户

        Returns:
            最新的提交记录，如果没有则返回None
        """
        return (
            Submission.objects.filter(homework=homework, student=student)
            .order_by("-version")
            .first()
        )

    def check_storage_space(self, repository: Repository) -> Tuple[int, int, float]:
        """检查仓库存储空间使用情况

        Args:
            repository: 仓库对象

        Returns:
            (已使用空间(MB), 总空间(MB), 使用百分比)
        """
        if repository.repo_type != "filesystem":
            return 0, 0, 0.0

        # 获取仓库路径
        repo_path = repository.get_full_path()

        # 计算已使用空间
        used_space_bytes = 0
        if os.path.exists(repo_path):
            for dirpath, _, filenames in os.walk(repo_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        used_space_bytes += os.path.getsize(filepath)
                    except OSError:
                        # 忽略无法访问的文件
                        pass

        # 转换为MB
        used_space_mb = used_space_bytes / (1024 * 1024)
        total_space_mb = repository.allocated_space_mb

        # 计算使用百分比
        usage_percentage = (used_space_mb / total_space_mb * 100) if total_space_mb > 0 else 0.0

        logger.debug(
            f"仓库 {repository.name} 空间使用情况: "
            f"{used_space_mb:.2f}MB / {total_space_mb}MB ({usage_percentage:.1f}%)"
        )

        return int(used_space_mb), total_space_mb, usage_percentage
