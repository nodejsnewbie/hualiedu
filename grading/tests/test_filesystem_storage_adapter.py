"""
FileSystemStorageAdapter 单元测试

测试文件系统存储适配器的核心功能：
- 路径验证
- 文件读写
- 目录创建
"""

import os
import shutil
import tempfile
from django.test import TestCase

from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter
from grading.services.storage_adapter import (
    FileSystemError,
    ValidationError,
)


class FileSystemStorageAdapterTest(TestCase):
    """FileSystemStorageAdapter 单元测试"""

    def setUp(self):
        """测试前设置"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        self.adapter = FileSystemStorageAdapter(self.test_dir)

    def tearDown(self):
        """测试后清理"""
        # 删除临时测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # ========== 路径验证测试 ==========

    def test_path_validation_prevents_traversal(self):
        """测试路径验证防止路径遍历攻击"""
        # 尝试访问父目录
        with self.assertRaises(ValidationError) as context:
            self.adapter.read_file("../etc/passwd")
        
        self.assertIn("无效的路径", context.exception.user_message)

    def test_path_validation_prevents_absolute_path(self):
        """测试路径验证防止绝对路径访问"""
        # 尝试使用绝对路径
        with self.assertRaises(ValidationError):
            self.adapter.read_file("/etc/passwd")

    def test_path_validation_allows_valid_relative_path(self):
        """测试路径验证允许有效的相对路径"""
        # 创建测试文件
        test_file = "subdir/test.txt"
        self.adapter.write_file(test_file, b"test content")
        
        # 应该能够读取
        content = self.adapter.read_file(test_file)
        self.assertEqual(content, b"test content")

    def test_path_validation_with_dots_in_filename(self):
        """测试路径验证允许文件名中包含点"""
        # 文件名中的点应该被允许
        test_file = "test.file.txt"
        self.adapter.write_file(test_file, b"content")
        
        content = self.adapter.read_file(test_file)
        self.assertEqual(content, b"content")

    def test_empty_path_refers_to_base_directory(self):
        """测试空路径指向基础目录"""
        # 空路径应该指向基础目录
        entries = self.adapter.list_directory("")
        self.assertIsInstance(entries, list)

    # ========== 文件读写测试 ==========

    def test_write_and_read_file(self):
        """测试文件写入和读取"""
        test_path = "test_file.txt"
        test_content = b"Hello, World!"
        
        # 写入文件
        result = self.adapter.write_file(test_path, test_content)
        self.assertTrue(result)
        
        # 读取文件
        content = self.adapter.read_file(test_path)
        self.assertEqual(content, test_content)

    def test_write_file_with_nested_path(self):
        """测试写入嵌套路径的文件"""
        test_path = "dir1/dir2/dir3/test.txt"
        test_content = b"Nested content"
        
        # 写入文件（应该自动创建父目录）
        result = self.adapter.write_file(test_path, test_content)
        self.assertTrue(result)
        
        # 验证文件存在
        self.assertTrue(self.adapter.file_exists(test_path))
        
        # 读取文件
        content = self.adapter.read_file(test_path)
        self.assertEqual(content, test_content)

    def test_write_file_overwrites_existing(self):
        """测试写入文件覆盖已存在的文件"""
        test_path = "overwrite.txt"
        
        # 第一次写入
        self.adapter.write_file(test_path, b"Original")
        
        # 第二次写入（覆盖）
        self.adapter.write_file(test_path, b"Updated")
        
        # 验证内容已更新
        content = self.adapter.read_file(test_path)
        self.assertEqual(content, b"Updated")

    def test_write_binary_file(self):
        """测试写入二进制文件"""
        test_path = "binary.bin"
        test_content = bytes(range(256))
        
        self.adapter.write_file(test_path, test_content)
        content = self.adapter.read_file(test_path)
        
        self.assertEqual(content, test_content)

    def test_write_empty_file(self):
        """测试写入空文件"""
        test_path = "empty.txt"
        
        self.adapter.write_file(test_path, b"")
        content = self.adapter.read_file(test_path)
        
        self.assertEqual(content, b"")

    def test_read_nonexistent_file_raises_error(self):
        """测试读取不存在的文件抛出错误"""
        with self.assertRaises(FileSystemError) as context:
            self.adapter.read_file("nonexistent.txt")
        
        self.assertIn("文件不存在", context.exception.user_message)

    def test_read_directory_as_file_raises_error(self):
        """测试将目录作为文件读取抛出错误"""
        # 创建目录
        self.adapter.create_directory("testdir")
        
        # 尝试作为文件读取
        with self.assertRaises(FileSystemError) as context:
            self.adapter.read_file("testdir")
        
        self.assertIn("不是文件", context.exception.user_message)

    def test_write_file_with_empty_path_raises_error(self):
        """测试空路径写入文件抛出错误"""
        with self.assertRaises(ValidationError) as context:
            self.adapter.write_file("", b"content")
        
        self.assertIn("文件路径不能为空", context.exception.user_message)

    def test_read_file_with_empty_path_raises_error(self):
        """测试空路径读取文件抛出错误"""
        with self.assertRaises(ValidationError) as context:
            self.adapter.read_file("")
        
        self.assertIn("文件路径不能为空", context.exception.user_message)

    # ========== 目录创建测试 ==========

    def test_create_directory(self):
        """测试创建目录"""
        test_dir = "new_directory"
        
        result = self.adapter.create_directory(test_dir)
        self.assertTrue(result)
        
        # 验证目录存在
        self.assertTrue(self.adapter.directory_exists(test_dir))

    def test_create_nested_directory(self):
        """测试创建嵌套目录"""
        test_dir = "parent/child/grandchild"
        
        result = self.adapter.create_directory(test_dir)
        self.assertTrue(result)
        
        # 验证所有层级的目录都存在
        self.assertTrue(self.adapter.directory_exists("parent"))
        self.assertTrue(self.adapter.directory_exists("parent/child"))
        self.assertTrue(self.adapter.directory_exists(test_dir))

    def test_create_existing_directory_succeeds(self):
        """测试创建已存在的目录成功（幂等性）"""
        test_dir = "existing_dir"
        
        # 第一次创建
        self.adapter.create_directory(test_dir)
        
        # 第二次创建应该成功
        result = self.adapter.create_directory(test_dir)
        self.assertTrue(result)

    def test_create_directory_with_empty_path(self):
        """测试空路径创建目录（基础目录）"""
        # 空路径应该成功（基础目录已存在）
        result = self.adapter.create_directory("")
        self.assertTrue(result)

    def test_create_directory_where_file_exists_raises_error(self):
        """测试在文件位置创建目录抛出错误"""
        # 先创建文件
        self.adapter.write_file("testfile.txt", b"content")
        
        # 尝试在同一位置创建目录
        with self.assertRaises(FileSystemError) as context:
            self.adapter.create_directory("testfile.txt")
        
        self.assertIn("不是目录", context.exception.user_message)

    # ========== 目录列表测试 ==========

    def test_list_empty_directory(self):
        """测试列出空目录"""
        test_dir = "empty_dir"
        self.adapter.create_directory(test_dir)
        
        entries = self.adapter.list_directory(test_dir)
        self.assertEqual(entries, [])

    def test_list_directory_with_files(self):
        """测试列出包含文件的目录"""
        # 创建测试文件
        self.adapter.write_file("file1.txt", b"content1")
        self.adapter.write_file("file2.txt", b"content2")
        
        entries = self.adapter.list_directory("")
        
        # 验证返回的条目
        self.assertEqual(len(entries), 2)
        
        names = [entry["name"] for entry in entries]
        self.assertIn("file1.txt", names)
        self.assertIn("file2.txt", names)
        
        # 验证条目结构
        for entry in entries:
            self.assertIn("name", entry)
            self.assertIn("type", entry)
            self.assertIn("size", entry)
            self.assertIn("modified", entry)
            self.assertEqual(entry["type"], "file")

    def test_list_directory_with_subdirectories(self):
        """测试列出包含子目录的目录"""
        # 创建子目录
        self.adapter.create_directory("subdir1")
        self.adapter.create_directory("subdir2")
        
        entries = self.adapter.list_directory("")
        
        # 验证返回的条目
        self.assertEqual(len(entries), 2)
        
        names = [entry["name"] for entry in entries]
        self.assertIn("subdir1", names)
        self.assertIn("subdir2", names)
        
        # 验证类型为目录
        for entry in entries:
            self.assertEqual(entry["type"], "dir")
            self.assertEqual(entry["size"], 0)

    def test_list_directory_mixed_content(self):
        """测试列出包含文件和目录的混合内容"""
        # 创建文件和目录
        self.adapter.write_file("file.txt", b"content")
        self.adapter.create_directory("directory")
        
        entries = self.adapter.list_directory("")
        
        self.assertEqual(len(entries), 2)
        
        # 按名称查找条目
        file_entry = next(e for e in entries if e["name"] == "file.txt")
        dir_entry = next(e for e in entries if e["name"] == "directory")
        
        self.assertEqual(file_entry["type"], "file")
        self.assertGreater(file_entry["size"], 0)
        
        self.assertEqual(dir_entry["type"], "dir")
        self.assertEqual(dir_entry["size"], 0)

    def test_list_nonexistent_directory_raises_error(self):
        """测试列出不存在的目录抛出错误"""
        with self.assertRaises(FileSystemError) as context:
            self.adapter.list_directory("nonexistent")
        
        self.assertIn("目录不存在", context.exception.user_message)

    def test_list_file_as_directory_raises_error(self):
        """测试将文件作为目录列出抛出错误"""
        # 创建文件
        self.adapter.write_file("file.txt", b"content")
        
        # 尝试作为目录列出
        with self.assertRaises(FileSystemError) as context:
            self.adapter.list_directory("file.txt")
        
        self.assertIn("不是目录", context.exception.user_message)

    # ========== 文件存在性检查测试 ==========

    def test_file_exists_returns_true_for_existing_file(self):
        """测试文件存在时返回 True"""
        test_path = "exists.txt"
        self.adapter.write_file(test_path, b"content")
        
        self.assertTrue(self.adapter.file_exists(test_path))

    def test_file_exists_returns_false_for_nonexistent_file(self):
        """测试文件不存在时返回 False"""
        self.assertFalse(self.adapter.file_exists("nonexistent.txt"))

    def test_file_exists_returns_false_for_directory(self):
        """测试目录不被识别为文件"""
        self.adapter.create_directory("testdir")
        
        self.assertFalse(self.adapter.file_exists("testdir"))

    def test_file_exists_with_empty_path(self):
        """测试空路径的文件存在性检查"""
        self.assertFalse(self.adapter.file_exists(""))

    def test_directory_exists_returns_true_for_existing_directory(self):
        """测试目录存在时返回 True"""
        test_dir = "testdir"
        self.adapter.create_directory(test_dir)
        
        self.assertTrue(self.adapter.directory_exists(test_dir))

    def test_directory_exists_returns_false_for_nonexistent_directory(self):
        """测试目录不存在时返回 False"""
        self.assertFalse(self.adapter.directory_exists("nonexistent"))

    def test_directory_exists_returns_false_for_file(self):
        """测试文件不被识别为目录"""
        self.adapter.write_file("file.txt", b"content")
        
        self.assertFalse(self.adapter.directory_exists("file.txt"))

    def test_directory_exists_for_base_path(self):
        """测试基础路径的目录存在性检查"""
        self.assertTrue(self.adapter.directory_exists(""))

    # ========== 文件删除测试 ==========

    def test_delete_existing_file(self):
        """测试删除存在的文件"""
        test_path = "to_delete.txt"
        self.adapter.write_file(test_path, b"content")
        
        # 删除文件
        result = self.adapter.delete_file(test_path)
        self.assertTrue(result)
        
        # 验证文件已删除
        self.assertFalse(self.adapter.file_exists(test_path))

    def test_delete_nonexistent_file_succeeds(self):
        """测试删除不存在的文件成功（幂等性）"""
        result = self.adapter.delete_file("nonexistent.txt")
        self.assertTrue(result)

    def test_delete_directory_as_file_raises_error(self):
        """测试删除目录作为文件抛出错误"""
        self.adapter.create_directory("testdir")
        
        with self.assertRaises(FileSystemError) as context:
            self.adapter.delete_file("testdir")
        
        self.assertIn("不是文件", context.exception.user_message)

    def test_delete_file_with_empty_path_raises_error(self):
        """测试空路径删除文件抛出错误"""
        with self.assertRaises(ValidationError) as context:
            self.adapter.delete_file("")
        
        self.assertIn("文件路径不能为空", context.exception.user_message)

    # ========== 文件大小测试 ==========

    def test_get_file_size(self):
        """测试获取文件大小"""
        test_path = "sized_file.txt"
        test_content = b"Hello, World!"
        
        self.adapter.write_file(test_path, test_content)
        
        size = self.adapter.get_file_size(test_path)
        self.assertEqual(size, len(test_content))

    def test_get_file_size_for_empty_file(self):
        """测试获取空文件大小"""
        test_path = "empty.txt"
        self.adapter.write_file(test_path, b"")
        
        size = self.adapter.get_file_size(test_path)
        self.assertEqual(size, 0)

    def test_get_file_size_for_nonexistent_file_raises_error(self):
        """测试获取不存在文件的大小抛出错误"""
        with self.assertRaises(FileSystemError) as context:
            self.adapter.get_file_size("nonexistent.txt")
        
        self.assertIn("文件不存在", context.exception.user_message)

    def test_get_file_size_with_empty_path_raises_error(self):
        """测试空路径获取文件大小抛出错误"""
        with self.assertRaises(ValidationError) as context:
            self.adapter.get_file_size("")
        
        self.assertIn("文件路径不能为空", context.exception.user_message)

    # ========== 初始化测试 ==========

    def test_initialization_creates_base_directory(self):
        """测试初始化时创建基础目录"""
        # 创建一个不存在的目录路径
        new_base = os.path.join(self.test_dir, "new_base")
        
        # 初始化适配器（应该自动创建目录）
        adapter = FileSystemStorageAdapter(new_base)
        
        # 验证目录已创建
        self.assertTrue(os.path.exists(new_base))
        self.assertTrue(os.path.isdir(new_base))

    def test_initialization_with_tilde_expands_path(self):
        """测试初始化时展开波浪号路径"""
        # 使用波浪号路径
        tilde_path = "~/test_adapter_dir"
        adapter = FileSystemStorageAdapter(tilde_path)
        
        # 验证路径已展开
        self.assertNotIn("~", adapter.base_path)
        self.assertTrue(os.path.isabs(adapter.base_path))
        
        # 清理
        if os.path.exists(adapter.base_path):
            shutil.rmtree(adapter.base_path)

    def test_initialization_converts_to_absolute_path(self):
        """测试初始化时转换为绝对路径"""
        # 使用相对路径
        relative_path = "relative_test_dir"
        adapter = FileSystemStorageAdapter(relative_path)
        
        # 验证路径是绝对路径
        self.assertTrue(os.path.isabs(adapter.base_path))
        
        # 清理
        if os.path.exists(adapter.base_path):
            shutil.rmtree(adapter.base_path)
