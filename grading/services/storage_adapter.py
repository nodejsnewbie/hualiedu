"""
存储适配器抽象接口 (Storage Adapter Interface)

本模块定义统一的存储访问接口，用于抽象 Git 仓库和文件系统的差异。

设计模式：适配器模式 (Adapter Pattern)
- 为不同的存储方式提供统一的接口
- 业务逻辑层无需关心底层存储实现
- 便于扩展新的存储方式（如云存储）

支持的存储方式：
1. Git 仓库：通过 GitStorageAdapter 实现，直接访问远程仓库
2. 文件系统：通过 FileSystemStorageAdapter 实现，访问本地文件

核心接口：
- list_directory: 列出目录内容
- read_file: 读取文件内容
- write_file: 写入文件
- create_directory: 创建目录
- delete_file: 删除文件
- file_exists: 检查文件是否存在
- directory_exists: 检查目录是否存在

异常类型：
- StorageError: 存储访问异常基类
- ValidationError: 验证错误
- RemoteAccessError: 远程仓库访问错误
- FileSystemError: 文件系统错误

使用示例：
    # 使用 Git 适配器
    adapter = GitStorageAdapter(
        git_url="https://github.com/user/repo.git",
        branch="main"
    )
    entries = adapter.list_directory("第一次作业")
    content = adapter.read_file("第一次作业/张三-作业1.docx")

    # 使用文件系统适配器
    adapter = FileSystemStorageAdapter(base_path="/path/to/assignments")
    adapter.create_directory("第二次作业")
    adapter.write_file("第二次作业/李四-作业2.pdf", content)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class StorageAdapter(ABC):
    """存储适配器抽象基类

    定义统一的存储访问接口，用于抽象 Git 仓库和文件系统的差异。
    所有具体的存储适配器都应该继承此类并实现其抽象方法。

    设计原则：
    1. 接口统一：所有存储方式使用相同的方法签名
    2. 路径相对：所有路径参数都是相对路径，由适配器处理绝对路径
    3. 异常处理：使用自定义异常类型，提供用户友好的错误消息
    4. 类型安全：使用类型注解，便于IDE提示和类型检查

    实现要求：
    - 所有抽象方法必须实现
    - 路径参数使用 "/" 作为分隔符（跨平台兼容）
    - 文件内容使用 bytes 类型（支持二进制文件）
    - 异常应包含技术消息和用户友好消息

    子类：
    - GitStorageAdapter: Git 仓库存储适配器
    - FileSystemStorageAdapter: 文件系统存储适配器
    """

    @abstractmethod
    def list_directory(self, path: str = "") -> List[Dict]:
        """列出目录内容

        Args:
            path: 相对路径，空字符串表示根目录

        Returns:
            目录条目列表，每个条目包含以下字段：
            - name: 文件或目录名称
            - type: "file" 或 "dir"
            - size: 文件大小（字节），目录为 0
            - modified: 修改时间（可选）

        Raises:
            StorageError: 访问失败时抛出
        """
        pass

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """读取文件内容

        Args:
            path: 文件相对路径

        Returns:
            文件内容（字节）

        Raises:
            StorageError: 文件不存在或读取失败时抛出
        """
        pass

    @abstractmethod
    def write_file(self, path: str, content: bytes) -> bool:
        """写入文件

        Args:
            path: 文件相对路径
            content: 文件内容（字节）

        Returns:
            成功返回 True，失败返回 False

        Raises:
            StorageError: 写入失败时抛出
        """
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """创建目录

        Args:
            path: 目录相对路径

        Returns:
            成功返回 True，失败返回 False

        Raises:
            StorageError: 创建失败时抛出
        """
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """删除文件

        Args:
            path: 文件相对路径

        Returns:
            成功返回 True，失败返回 False

        Raises:
            StorageError: 删除失败时抛出
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """检查文件是否存在

        Args:
            path: 文件相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        pass

    @abstractmethod
    def directory_exists(self, path: str) -> bool:
        """检查目录是否存在

        Args:
            path: 目录相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        pass


class StorageError(Exception):
    """存储访问异常基类"""

    def __init__(self, message: str, user_message: str = None, details: Dict = None):
        """初始化存储异常

        Args:
            message: 技术错误消息（用于日志）
            user_message: 用户友好的错误消息（用于显示）
            details: 详细信息字典
        """
        self.message = message
        self.user_message = user_message or "操作失败，请稍后重试"
        self.details = details or {}
        super().__init__(self.message)

        # 记录异常日志
        logger.error(f"StorageError: {message}", extra={"details": self.details})

    def to_dict(self):
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
        }


class ValidationError(StorageError):
    """验证错误"""

    pass


class RemoteAccessError(StorageError):
    """远程仓库访问错误"""

    pass


class FileSystemError(StorageError):
    """文件系统错误"""

    pass
