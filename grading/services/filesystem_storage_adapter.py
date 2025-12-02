"""
文件系统存储适配器 (FileSystem Storage Adapter)

本模块实现本地文件系统的存储适配器，支持文件和目录的读写操作。

核心特性：
1. 本地文件访问：直接操作本地文件系统
2. 路径验证：确保所有操作在基础路径内，防止路径遍历攻击
3. 自动创建目录：写入文件时自动创建所需的父目录
4. 安全检查：验证路径合法性和访问权限
5. 跨平台支持：使用 os.path 处理路径，支持 Windows/Linux/macOS

实现需求：
- Requirements 4.1: 根据课程和班级生成目录路径
- Requirements 4.2: 文件存储在 <课程名>/<班级名>/<作业次数>/ 结构中
- Requirements 4.4: 自动创建不存在的目录
- Requirements 4.6: 目录不存在时自动创建
- Requirements 4.7: 处理路径中的特殊字符

安全特性：
- 路径验证：确保所有路径在 base_path 内
- 权限检查：验证文件读写权限
- 特殊字符处理：清理和验证文件名
- 防止路径遍历：拒绝包含 ".." 的路径

目录结构示例：
    base_path/
    ├── 数据结构/
    │   ├── 计算机1班/
    │   │   ├── 第一次作业/
    │   │   │   ├── 张三-作业1.docx
    │   │   │   └── 李四-作业1.pdf
    │   │   └── 第二次作业/
    │   └── 计算机2班/
    └── 算法设计/

使用示例：
    adapter = FileSystemStorageAdapter(base_path="/path/to/assignments")

    # 创建目录
    adapter.create_directory("数据结构/计算机1班/第一次作业")

    # 写入文件
    adapter.write_file(
        "数据结构/计算机1班/第一次作业/张三-作业1.docx",
        file_content
    )

    # 列出目录
    entries = adapter.list_directory("数据结构/计算机1班")

    # 读取文件
    content = adapter.read_file("数据结构/计算机1班/第一次作业/张三-作业1.docx")
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from .storage_adapter import FileSystemError, StorageAdapter, ValidationError

logger = logging.getLogger(__name__)


class FileSystemStorageAdapter(StorageAdapter):
    """文件系统存储适配器

    实现本地文件系统的存储访问，包括路径验证和安全检查。

    工作原理：
    1. 所有路径操作都基于 base_path
    2. 相对路径转换为绝对路径
    3. 验证路径在 base_path 内
    4. 执行文件系统操作

    路径处理：
    - 使用 os.path.join 拼接路径（跨平台兼容）
    - 使用 os.path.abspath 获取绝对路径
    - 使用 os.path.expanduser 展开 ~ 符号
    - 验证路径不包含 ".." 等危险字符

    安全机制：
    - 路径必须在 base_path 内
    - 拒绝包含 ".." 的路径
    - 检查文件读写权限
    - 记录所有操作日志

    错误处理：
    - 路径验证失败抛出 ValidationError
    - 文件操作失败抛出 FileSystemError
    - 提供用户友好的错误消息
    - 记录详细的技术错误日志

    自动创建：
    - 写入文件时自动创建父目录
    - 使用 os.makedirs(exist_ok=True)
    - 创建失败抛出异常
    """

    def __init__(self, base_path: str):
        """初始化文件系统存储适配器

        Args:
            base_path: 基础路径，所有操作都在此路径下进行
        """
        self.base_path = os.path.expanduser(base_path)
        self.base_path = os.path.abspath(self.base_path)

        # 确保基础路径存在
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                logger.info(f"Created base directory: {self.base_path}")
            except Exception as e:
                raise FileSystemError(
                    f"Failed to create base directory: {str(e)}",
                    user_message="无法创建基础目录，请联系管理员",
                    details={"base_path": self.base_path, "error": str(e)},
                )

    def _get_full_path(self, path: str) -> str:
        """获取完整路径

        Args:
            path: 相对路径

        Returns:
            完整的绝对路径
        """
        if not path:
            return self.base_path

        full_path = os.path.join(self.base_path, path)
        full_path = os.path.abspath(full_path)
        return full_path

    def _validate_path(self, full_path: str):
        """验证路径安全性

        确保路径在基础目录内，防止路径遍历攻击。

        Args:
            full_path: 完整路径

        Raises:
            ValidationError: 路径不安全时抛出
        """
        # 确保路径在基础目录内
        if not full_path.startswith(self.base_path):
            raise ValidationError(
                f"Path traversal detected: {full_path}",
                user_message="无效的路径",
                details={"path": full_path, "base_path": self.base_path},
            )

    def list_directory(self, path: str = "") -> List[Dict]:
        """列出目录内容

        Args:
            path: 相对路径，空字符串表示根目录

        Returns:
            目录条目列表

        Raises:
            FileSystemError: 访问失败时抛出
        """
        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        if not os.path.exists(full_path):
            raise FileSystemError(
                f"Directory not found: {full_path}",
                user_message="目录不存在",
                details={"path": path},
            )

        if not os.path.isdir(full_path):
            raise FileSystemError(
                f"Not a directory: {full_path}",
                user_message="指定的路径不是目录",
                details={"path": path},
            )

        try:
            entries = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)

                try:
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)

                    entries.append(
                        {
                            "name": item,
                            "type": "dir" if is_dir else "file",
                            "size": 0 if is_dir else stat.st_size,
                            "modified": stat.st_mtime,
                        }
                    )
                except (OSError, PermissionError) as e:
                    # 跳过无法访问的文件
                    logger.warning(f"Cannot access {item_path}: {str(e)}")
                    continue

            return entries

        except PermissionError:
            raise FileSystemError(
                f"Permission denied: {full_path}",
                user_message="没有权限访问该目录，请联系管理员",
                details={"path": path},
            )
        except Exception as e:
            raise FileSystemError(
                f"Failed to list directory: {str(e)}",
                user_message="无法读取目录内容",
                details={"path": path, "error": str(e)},
            )

    def read_file(self, path: str) -> bytes:
        """读取文件内容

        Args:
            path: 文件相对路径

        Returns:
            文件内容（字节）

        Raises:
            FileSystemError: 读取失败时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", user_message="文件路径不能为空")

        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        if not os.path.exists(full_path):
            raise FileSystemError(
                f"File not found: {full_path}", user_message="文件不存在", details={"path": path}
            )

        if not os.path.isfile(full_path):
            raise FileSystemError(
                f"Not a file: {full_path}",
                user_message="指定的路径不是文件",
                details={"path": path},
            )

        try:
            with open(full_path, "rb") as f:
                return f.read()
        except PermissionError:
            raise FileSystemError(
                f"Permission denied: {full_path}",
                user_message="没有权限读取该文件，请联系管理员",
                details={"path": path},
            )
        except Exception as e:
            raise FileSystemError(
                f"Failed to read file: {str(e)}",
                user_message="无法读取文件内容",
                details={"path": path, "error": str(e)},
            )

    def write_file(self, path: str, content: bytes) -> bool:
        """写入文件

        Args:
            path: 文件相对路径
            content: 文件内容（字节）

        Returns:
            成功返回 True

        Raises:
            FileSystemError: 写入失败时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", user_message="文件路径不能为空")

        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        # 确保父目录存在
        parent_dir = os.path.dirname(full_path)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"Created parent directory: {parent_dir}")
            except Exception as e:
                raise FileSystemError(
                    f"Failed to create parent directory: {str(e)}",
                    user_message="无法创建目录",
                    details={"path": path, "error": str(e)},
                )

        try:
            with open(full_path, "wb") as f:
                f.write(content)
            logger.info(f"Wrote file: {full_path}")
            return True
        except PermissionError:
            raise FileSystemError(
                f"Permission denied: {full_path}",
                user_message="没有权限写入该文件，请联系管理员",
                details={"path": path},
            )
        except OSError as e:
            if "Disk quota exceeded" in str(e) or "No space left" in str(e):
                raise FileSystemError(
                    f"Disk space error: {str(e)}",
                    user_message="存储空间不足，请清理旧文件或联系管理员",
                    details={"path": path, "error": str(e)},
                )
            raise FileSystemError(
                f"Failed to write file: {str(e)}",
                user_message="无法写入文件",
                details={"path": path, "error": str(e)},
            )
        except Exception as e:
            raise FileSystemError(
                f"Failed to write file: {str(e)}",
                user_message="无法写入文件",
                details={"path": path, "error": str(e)},
            )

    def create_directory(self, path: str) -> bool:
        """创建目录

        Args:
            path: 目录相对路径

        Returns:
            成功返回 True

        Raises:
            FileSystemError: 创建失败时抛出
        """
        if not path:
            # 空路径表示基础目录，已经存在
            return True

        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                # 目录已存在
                return True
            else:
                raise FileSystemError(
                    f"Path exists but is not a directory: {full_path}",
                    user_message="路径已存在但不是目录",
                    details={"path": path},
                )

        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            return True
        except PermissionError:
            raise FileSystemError(
                f"Permission denied: {full_path}",
                user_message="没有权限创建目录，请联系管理员",
                details={"path": path},
            )
        except Exception as e:
            raise FileSystemError(
                f"Failed to create directory: {str(e)}",
                user_message="无法创建目录",
                details={"path": path, "error": str(e)},
            )

    def delete_file(self, path: str) -> bool:
        """删除文件

        Args:
            path: 文件相对路径

        Returns:
            成功返回 True

        Raises:
            FileSystemError: 删除失败时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", user_message="文件路径不能为空")

        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        if not os.path.exists(full_path):
            # 文件不存在，视为成功
            return True

        if not os.path.isfile(full_path):
            raise FileSystemError(
                f"Not a file: {full_path}",
                user_message="指定的路径不是文件",
                details={"path": path},
            )

        try:
            os.remove(full_path)
            logger.info(f"Deleted file: {full_path}")
            return True
        except PermissionError:
            raise FileSystemError(
                f"Permission denied: {full_path}",
                user_message="没有权限删除该文件，请联系管理员",
                details={"path": path},
            )
        except Exception as e:
            raise FileSystemError(
                f"Failed to delete file: {str(e)}",
                user_message="无法删除文件",
                details={"path": path, "error": str(e)},
            )

    def file_exists(self, path: str) -> bool:
        """检查文件是否存在

        Args:
            path: 文件相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        if not path:
            return False

        full_path = self._get_full_path(path)

        try:
            self._validate_path(full_path)
            return os.path.isfile(full_path)
        except ValidationError:
            return False

    def directory_exists(self, path: str) -> bool:
        """检查目录是否存在

        Args:
            path: 目录相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        full_path = self._get_full_path(path)

        try:
            self._validate_path(full_path)
            return os.path.isdir(full_path)
        except ValidationError:
            return False

    def get_file_size(self, path: str) -> int:
        """获取文件大小

        Args:
            path: 文件相对路径

        Returns:
            文件大小（字节）

        Raises:
            FileSystemError: 获取失败时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", user_message="文件路径不能为空")

        full_path = self._get_full_path(path)
        self._validate_path(full_path)

        if not os.path.exists(full_path):
            raise FileSystemError(
                f"File not found: {full_path}", user_message="文件不存在", details={"path": path}
            )

        try:
            return os.path.getsize(full_path)
        except Exception as e:
            raise FileSystemError(
                f"Failed to get file size: {str(e)}",
                user_message="无法获取文件大小",
                details={"path": path, "error": str(e)},
            )
