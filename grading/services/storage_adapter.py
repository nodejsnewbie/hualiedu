"""
存储适配器抽象接口

定义统一的存储访问接口，支持 Git 仓库和文件系统两种存储方式。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StorageAdapter(ABC):
    """存储适配器抽象基类
    
    定义统一的存储访问接口，用于抽象 Git 仓库和文件系统的差异。
    所有具体的存储适配器都应该继承此类并实现其抽象方法。
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
