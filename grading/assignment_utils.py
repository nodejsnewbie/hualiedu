"""
作业管理工具类

提供路径验证、凭据加密和缓存管理等功能。
"""

import base64
import hashlib
import logging
import os
import re
from typing import List, Optional

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AssignmentError(Exception):
    """作业管理基础异常"""

    def __init__(self, message: str, user_message: str = None):
        self.message = message
        self.user_message = user_message or "操作失败，请稍后重试"
        super().__init__(self.message)


class ValidationError(AssignmentError):
    """验证错误"""

    pass


class PathValidator:
    """路径验证器"""

    # 文件系统非法字符
    ILLEGAL_CHARS = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]

    # 替换映射
    CHAR_REPLACEMENTS = {
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "-",
    }

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """清理名称中的非法字符

        Args:
            name: 原始名称

        Returns:
            清理后的名称

        Raises:
            ValidationError: 如果名称为空或清理后为空
        """
        if not name:
            raise ValidationError("名称不能为空", "请输入有效的名称")

        # 去除首尾空格
        name = name.strip()

        # 替换非法字符
        for char, replacement in cls.CHAR_REPLACEMENTS.items():
            name = name.replace(char, replacement)

        # 去除连续的连字符
        name = re.sub(r"-+", "-", name)

        # 去除首尾连字符
        name = name.strip("-")

        if not name:
            raise ValidationError("清理后的名称为空", "名称包含过多特殊字符，请使用字母和数字")

        return name

    @classmethod
    def validate_path(cls, path: str, base_path: str) -> bool:
        """验证路径安全性

        Args:
            path: 要验证的路径
            base_path: 基础路径

        Returns:
            是否安全

        Raises:
            ValidationError: 如果路径不安全
        """
        # 解析为绝对路径
        abs_path = os.path.abspath(os.path.join(base_path, path))
        abs_base = os.path.abspath(base_path)

        # 确保路径在基础目录内
        if not abs_path.startswith(abs_base):
            raise ValidationError(f"Path traversal attempt: {path}", "无效的路径")

        return True

    @classmethod
    def validate_assignment_number_format(cls, name: str) -> bool:
        """验证作业次数格式

        Args:
            name: 作业次数名称

        Returns:
            是否符合格式要求

        Note:
            支持的格式：
            - "第N次作业" (N为中文数字或阿拉伯数字)
            - "第N次实验" (N为中文数字或阿拉伯数字)
            - "第N次练习" (N为中文数字或阿拉伯数字)
        """
        if not name or not isinstance(name, str):
            return False

        # 定义支持的格式模式
        # 支持：第一次作业、第1次作业、第十次实验、第10次实验等
        patterns = [
            r"^第[一二三四五六七八九十\d]+次作业$",
            r"^第[一二三四五六七八九十\d]+次实验$",
            r"^第[一二三四五六七八九十\d]+次练习$",
        ]

        for pattern in patterns:
            if re.match(pattern, name):
                return True

        return False

    @classmethod
    def generate_assignment_number_name(cls, existing_numbers: List[int]) -> str:
        """生成作业次数名称

        Args:
            existing_numbers: 已存在的作业次数列表

        Returns:
            新的作业次数名称，格式为"第N次作业"
        """
        if not existing_numbers:
            next_number = 1
        else:
            next_number = max(existing_numbers) + 1

        return f"第{cls._number_to_chinese(next_number)}次作业"

    @classmethod
    def _number_to_chinese(cls, num: int) -> str:
        """数字转中文

        Args:
            num: 数字

        Returns:
            中文数字字符串
        """
        chinese_nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

        if num <= 10:
            return chinese_nums[num]
        elif num < 20:
            return f"十{chinese_nums[num - 10]}"
        else:
            return str(num)  # 大于20使用阿拉伯数字


class CredentialEncryption:
    """凭据加密工具"""

    @classmethod
    def _get_key(cls) -> bytes:
        """获取加密密钥

        Returns:
            加密密钥

        Raises:
            ValidationError: 如果无法获取密钥
        """
        # 从 settings 获取密钥，或使用 SECRET_KEY 派生
        key = getattr(settings, "CREDENTIAL_ENCRYPTION_KEY", None)
        if not key:
            # 从 SECRET_KEY 派生
            from django.utils.encoding import force_bytes

            key = base64.urlsafe_b64encode(
                hashlib.sha256(force_bytes(settings.SECRET_KEY)).digest()
            )
        return key

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """加密

        Args:
            plaintext: 明文

        Returns:
            密文
        """
        if not plaintext:
            return ""

        try:
            f = Fernet(cls._get_key())
            encrypted = f.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密失败: {str(e)}")
            raise ValidationError(f"加密失败: {str(e)}", "凭据加密失败")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """解密

        Args:
            ciphertext: 密文

        Returns:
            明文
        """
        if not ciphertext:
            return ""

        try:
            f = Fernet(cls._get_key())
            decrypted = f.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {str(e)}")
            raise ValidationError(f"解密失败: {str(e)}", "凭据解密失败")


class FilenameValidator:
    """文件名验证器"""

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"}

    @classmethod
    def validate_file_format(cls, filename: str) -> bool:
        """验证文件格式是否在允许的列表中

        Args:
            filename: 文件名

        Returns:
            True 如果文件格式被允许，False 否则

        Note:
            这个方法实现 Requirement 9.6:
            "WHEN 学生上传文件 THEN AMS SHALL 支持常见文档格式（docx、pdf、zip 等）"
        """
        if not filename:
            return False

        # 获取文件扩展名（转换为小写）
        ext = os.path.splitext(filename)[1].lower()

        # 检查扩展名是否在允许列表中
        return ext in cls.ALLOWED_EXTENSIONS

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"}

    @classmethod
    def validate_file_format(cls, filename: str) -> bool:
        """验证文件格式是否在允许的列表中

        Args:
            filename: 文件名

        Returns:
            True 如果文件格式被允许，False 否则

        Note:
            这个方法实现 Requirement 9.6:
            "WHEN 学生上传文件 THEN AMS SHALL 支持常见文档格式（docx、pdf、zip 等）"
        """
        if not filename:
            return False

        # 获取文件扩展名（转换为小写）
        ext = os.path.splitext(filename)[1].lower()

        # 检查扩展名是否在允许列表中
        return ext in cls.ALLOWED_EXTENSIONS

    @classmethod
    def validate_student_name_in_filename(cls, filename: str, student_name: str) -> bool:
        """验证文件名是否包含学生姓名

        Args:
            filename: 文件名
            student_name: 学生姓名

        Returns:
            True 如果文件名包含学生姓名，False 否则

        Note:
            这个方法用于验证 Requirement 4.3:
            "WHEN 学生上传作业文件 THEN AMS SHALL 要求文件名包含学生姓名以便区分不同学生的作业"
        """
        if not filename or not student_name:
            return False

        # 检查文件名是否包含学生姓名
        # 支持不同的分隔符和格式
        return student_name in filename

    @classmethod
    def process_student_filename(cls, filename: str, student_name: str) -> str:
        """处理文件名，确保包含学生姓名

        如果文件名不包含学生姓名，自动添加学生姓名前缀。

        Args:
            filename: 原始文件名
            student_name: 学生姓名

        Returns:
            处理后的文件名（确保包含学生姓名）

        Raises:
            ValidationError: 如果文件名或学生姓名为空

        Note:
            这个方法实现 Requirement 9.5:
            "WHEN 学生上传作业文件 THEN AMS SHALL 自动在文件名中添加或验证学生姓名"
        """
        if not filename:
            raise ValidationError("文件名不能为空", "请提供有效的文件名")

        if not student_name:
            raise ValidationError("学生姓名不能为空", "无法处理文件名")

        # 如果文件名已包含学生姓名，直接返回
        if student_name in filename:
            return filename

        # 分离文件名和扩展名
        name, ext = os.path.splitext(filename)

        # 添加学生姓名前缀
        processed_filename = f"{student_name}-{name}{ext}"

        return processed_filename


class CacheManager:
    """缓存管理器"""

    CACHE_PREFIX = "assignment"
    DEFAULT_TIMEOUT = 300  # 5分钟

    @classmethod
    def get_cache_key(cls, assignment_id: int, path: str, operation: str) -> str:
        """生成缓存键

        Args:
            assignment_id: 作业ID
            path: 路径
            operation: 操作类型

        Returns:
            缓存键
        """
        key_data = f"{assignment_id}:{path}:{operation}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{cls.CACHE_PREFIX}:{key_hash}"

    @classmethod
    def get_directory_listing(cls, assignment_id: int, path: str) -> Optional[List]:
        """获取目录列表缓存

        Args:
            assignment_id: 作业ID
            path: 路径

        Returns:
            缓存的目录列表，如果不存在则返回None
        """
        key = cls.get_cache_key(assignment_id, path, "ls")
        return cache.get(key)

    @classmethod
    def set_directory_listing(cls, assignment_id: int, path: str, data: List) -> None:
        """设置目录列表缓存

        Args:
            assignment_id: 作业ID
            path: 路径
            data: 目录列表数据
        """
        key = cls.get_cache_key(assignment_id, path, "ls")
        cache.set(key, data, cls.DEFAULT_TIMEOUT)

    @classmethod
    def get_file_content(cls, assignment_id: int, path: str) -> Optional[bytes]:
        """获取文件内容缓存

        Args:
            assignment_id: 作业ID
            path: 路径

        Returns:
            缓存的文件内容，如果不存在则返回None
        """
        key = cls.get_cache_key(assignment_id, path, "file")
        return cache.get(key)

    @classmethod
    def set_file_content(cls, assignment_id: int, path: str, content: bytes) -> None:
        """设置文件内容缓存

        Args:
            assignment_id: 作业ID
            path: 路径
            content: 文件内容
        """
        key = cls.get_cache_key(assignment_id, path, "file")
        # 文件内容缓存时间更长
        cache.set(key, content, cls.DEFAULT_TIMEOUT * 2)

    @classmethod
    def invalidate_assignment(cls, assignment_id: int) -> None:
        """清除作业相关的所有缓存

        Args:
            assignment_id: 作业ID

        Note:
            Django 缓存不支持按前缀删除，此方法为占位符
            实际实现取决于缓存后端（如 Redis 的 SCAN 命令）
        """
        # Django 缓存不支持按前缀删除，需要记录所有键
        # 或使用 Redis 的 SCAN 命令
        # 这里提供一个基本实现框架
        logger.info(f"清除作业 {assignment_id} 的缓存")
        # 实际实现取决于缓存后端
        pass
