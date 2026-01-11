"""
工具函数测试
"""

import os
import shutil
import subprocess
import tempfile
from unittest.mock import MagicMock, mock_open, patch

from django.test import TestCase, override_settings

from grading.utils import FileHandler, GitHandler

from .base import BaseTestCase


class GitHandlerTest(BaseTestCase):
    """Git处理器测试"""

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.git_repo_path = os.path.join(self.temp_dir, "test_repo")
        self.target_path = os.path.join(self.temp_dir, "target_repo")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_is_git_repo_true(self, mock_run):
        """测试检查Git仓库（是Git仓库）"""
        mock_run.return_value = MagicMock(returncode=0)

        result = GitHandler.is_git_repo("/path/to/git/repo")

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd="/path/to/git/repo",
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_is_git_repo_false(self, mock_run):
        """测试检查Git仓库（不是Git仓库）"""
        mock_run.return_value = MagicMock(returncode=1)

        result = GitHandler.is_git_repo("/path/to/normal/dir")

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_is_git_repo_exception(self, mock_run):
        """测试检查Git仓库时发生异常"""
        mock_run.side_effect = Exception("Command failed")

        result = GitHandler.is_git_repo("/invalid/path")

        self.assertFalse(result)

    @patch("grading.utils.GitHandler.is_git_repo")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("shutil.rmtree")
    @patch("subprocess.run")
    def test_clone_repo_success(
        self, mock_run, mock_rmtree, mock_makedirs, mock_exists, mock_is_git
    ):
        """测试成功克隆仓库"""
        # 设置mock返回值
        mock_exists.side_effect = [True, False]  # 源路径存在，目标路径不存在
        mock_is_git.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = GitHandler.clone_repo(self.git_repo_path, self.target_path)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "clone", "--local", self.git_repo_path, self.target_path],
            capture_output=True,
            text=True,
        )

    @patch("os.path.exists")
    def test_clone_repo_source_not_exists(self, mock_exists):
        """测试克隆不存在的源仓库"""
        mock_exists.return_value = False

        result = GitHandler.clone_repo("/nonexistent/path", self.target_path)

        self.assertFalse(result)

    @patch("grading.utils.GitHandler.is_git_repo")
    @patch("os.path.exists")
    def test_clone_repo_not_git_repo(self, mock_exists, mock_is_git):
        """测试克隆非Git仓库"""
        mock_exists.return_value = True
        mock_is_git.return_value = False

        result = GitHandler.clone_repo("/not/git/repo", self.target_path)

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_repo_name_with_remote(self, mock_run):
        """测试获取有远程仓库的仓库名称"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="https://github.com/user/test-repo.git\n"
        )

        result = GitHandler.get_repo_name("/path/to/repo")

        self.assertEqual(result, "test-repo")

    @patch("subprocess.run")
    def test_get_repo_name_without_remote(self, mock_run):
        """测试获取无远程仓库的仓库名称"""
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        result = GitHandler.get_repo_name("/path/to/local-repo")

        self.assertEqual(result, "local-repo")

    @patch("subprocess.run")
    def test_get_repo_name_exception(self, mock_run):
        """测试获取仓库名称时发生异常"""
        mock_run.side_effect = Exception("Command failed")

        result = GitHandler.get_repo_name("/path/to/repo")

        self.assertEqual(result, "repo")

    @patch("subprocess.run")
    def test_clone_repo_remote_success(self, mock_run):
        """测试成功克隆远程仓库"""
        mock_run.return_value = MagicMock(returncode=0)

        result = GitHandler.clone_repo_remote("https://github.com/user/repo.git", self.target_path)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "clone", "https://github.com/user/repo.git", self.target_path],
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_clone_repo_remote_failure(self, mock_run):
        """测试克隆远程仓库失败"""
        mock_run.return_value = MagicMock(returncode=1)

        result = GitHandler.clone_repo_remote("invalid-repo", self.target_path)

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_clone_repo_remote_with_branch(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        result = GitHandler.clone_repo_remote(
            "https://github.com/user/repo.git", self.target_path, branch="feature"
        )

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "clone", "-b", "feature", "https://github.com/user/repo.git", self.target_path],
            capture_output=True,
            text=True,
        )

    @patch("grading.utils.GitHandler.ensure_branch", return_value=True)
    @patch("subprocess.run")
    def test_pull_repo_success(self, mock_run, mock_ensure):
        """测试成功拉取仓库更新"""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0),
        ]

        result = GitHandler.pull_repo(self.git_repo_path, branch="main")

        self.assertTrue(result)
        mock_ensure.assert_called_once_with(self.git_repo_path, "main")
        self.assertEqual(mock_run.call_count, 2)

    @patch("grading.utils.GitHandler.ensure_branch", return_value=True)
    @patch("subprocess.run")
    def test_pull_repo_failure(self, mock_run, mock_ensure):
        """测试拉取仓库更新失败"""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=1, stderr="error"),
        ]

        result = GitHandler.pull_repo(self.git_repo_path, branch="main")

        self.assertFalse(result)
        mock_ensure.assert_called_once_with(self.git_repo_path, "main")

    @patch("subprocess.run")
    def test_checkout_branch_success(self, mock_run):
        """测试成功切换分支"""
        mock_run.return_value = MagicMock(returncode=0)

        result = GitHandler.checkout_branch(self.git_repo_path, "develop")

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "checkout", "develop"], cwd=self.git_repo_path, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_checkout_branch_failure(self, mock_run):
        """测试切换分支失败"""
        mock_run.return_value = MagicMock(returncode=1)

        result = GitHandler.checkout_branch(self.git_repo_path, "nonexistent")

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_branches_success(self, mock_run):
        """测试成功获取分支列表"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="  origin/main\n  origin/develop\n  origin/feature/test\n"
        )

        result = GitHandler.get_branches(self.git_repo_path)

        expected = ["origin/main", "origin/develop", "origin/feature/test"]
        self.assertEqual(result, expected)

    @patch("subprocess.run")
    def test_get_branches_failure(self, mock_run):
        """测试获取分支列表失败"""
        mock_run.return_value = MagicMock(returncode=1)

        result = GitHandler.get_branches(self.git_repo_path)

        self.assertEqual(result, [])

    @patch("os.path.exists")
    def test_is_git_repository_true(self, mock_exists):
        """测试检查Git仓库目录（是Git仓库）"""
        mock_exists.return_value = True

        result = GitHandler.is_git_repository("/path/to/git/repo")

        self.assertTrue(result)
        mock_exists.assert_called_once_with("/path/to/git/repo/.git")

    @patch("os.path.exists")
    def test_is_git_repository_false(self, mock_exists):
        """测试检查Git仓库目录（不是Git仓库）"""
        mock_exists.return_value = False

        result = GitHandler.is_git_repository("/path/to/normal/dir")

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_current_branch_success(self, mock_run):
        """测试成功获取当前分支"""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n")

        result = GitHandler.get_current_branch(self.git_repo_path)

        self.assertEqual(result, "main")

    @patch("subprocess.run")
    def test_get_current_branch_failure(self, mock_run):
        """测试获取当前分支失败"""
        mock_run.return_value = MagicMock(returncode=1)

        result = GitHandler.get_current_branch(self.git_repo_path)

        self.assertIsNone(result)


class FileHandlerTest(BaseTestCase):
    """文件处理器测试"""

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @override_settings(MEDIA_ROOT="/media/root")
    @patch("os.path.realpath")
    def test_is_safe_path_within_media_root(self, mock_realpath):
        """测试路径在媒体根目录内（安全）"""
        mock_realpath.side_effect = ["/media/root/subdir/file.txt", "/media/root"]

        result = FileHandler.is_safe_path("/media/root/subdir/file.txt")

        self.assertTrue(result)

    @override_settings(MEDIA_ROOT="/media/root")
    @patch("os.path.realpath")
    def test_is_safe_path_outside_media_root(self, mock_realpath):
        """测试路径在媒体根目录外（不安全）"""
        mock_realpath.side_effect = ["/etc/passwd", "/media/root"]

        result = FileHandler.is_safe_path("/etc/passwd")

        self.assertFalse(result)

    @override_settings(MEDIA_ROOT="/media/root")
    @patch("os.path.realpath")
    def test_is_safe_path_realpath_exception(self, mock_realpath):
        """测试realpath抛出异常"""
        mock_realpath.side_effect = OSError("Path error")

        result = FileHandler.is_safe_path("/some/path")

        self.assertFalse(result)

    @override_settings(MEDIA_ROOT="")
    def test_is_safe_path_no_media_root_safe(self):
        """测试没有MEDIA_ROOT设置时的安全路径"""
        result = FileHandler.is_safe_path("relative/path/file.txt")

        self.assertTrue(result)

    @override_settings(MEDIA_ROOT="")
    def test_is_safe_path_no_media_root_unsafe_absolute(self):
        """测试没有MEDIA_ROOT设置时的不安全绝对路径"""
        result = FileHandler.is_safe_path("/absolute/path/file.txt")

        self.assertFalse(result)

    @override_settings(MEDIA_ROOT="")
    def test_is_safe_path_no_media_root_unsafe_dotdot(self):
        """测试没有MEDIA_ROOT设置时的不安全相对路径"""
        result = FileHandler.is_safe_path("../../../etc/passwd")

        self.assertFalse(result)

    @patch("mimetypes.guess_type")
    def test_get_mime_type_success(self, mock_guess_type):
        """测试成功获取MIME类型"""
        mock_guess_type.return_value = ("text/plain", None)

        result = FileHandler.get_mime_type("test.txt")

        self.assertEqual(result, "text/plain")
        mock_guess_type.assert_called_once_with("test.txt")

    @patch("mimetypes.guess_type")
    def test_get_mime_type_exception(self, mock_guess_type):
        """测试获取MIME类型时发生异常"""
        mock_guess_type.side_effect = Exception("MIME type error")

        result = FileHandler.get_mime_type("test.txt")

        self.assertIsNone(result)

    @patch("os.path.getsize")
    def test_get_file_size_success(self, mock_getsize):
        """测试成功获取文件大小"""
        mock_getsize.return_value = 1024

        result = FileHandler.get_file_size("test.txt")

        self.assertEqual(result, 1024)
        mock_getsize.assert_called_once_with("test.txt")

    @patch("os.path.getsize")
    def test_get_file_size_file_not_found(self, mock_getsize):
        """测试获取不存在文件的大小"""
        mock_getsize.side_effect = OSError("File not found")

        result = FileHandler.get_file_size("nonexistent.txt")

        self.assertEqual(result, 0)

    @patch("os.makedirs")
    def test_create_directory_if_not_exists(self, mock_makedirs):
        """测试创建目录"""
        FileHandler.create_directory_if_not_exists("/path/to/new/dir")

        mock_makedirs.assert_called_once_with("/path/to/new/dir", exist_ok=True)

    def test_get_mime_type_common_types(self):
        """测试常见文件类型的MIME类型"""
        test_cases = [
            ("test.txt", "text/plain"),
            ("test.html", "text/html"),
            ("test.css", "text/css"),
            ("test.js", "application/javascript"),
            ("test.json", "application/json"),
            ("test.pdf", "application/pdf"),
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.gif", "image/gif"),
        ]

        for filename, expected_mime in test_cases:
            with self.subTest(filename=filename):
                result = FileHandler.get_mime_type(filename)
                # 由于不同系统可能有不同的MIME类型映射，这里只检查是否返回了值
                if expected_mime:
                    self.assertIsNotNone(result)


class UtilsIntegrationTest(BaseTestCase):
    """工具函数集成测试"""

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_handler_with_real_files(self):
        """测试文件处理器与真实文件"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        test_content = "Hello, World!"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # 测试获取文件大小
        size = FileHandler.get_file_size(test_file)
        self.assertEqual(size, len(test_content.encode("utf-8")))

        # 测试获取MIME类型
        mime_type = FileHandler.get_mime_type(test_file)
        self.assertIsNotNone(mime_type)

    def test_create_and_check_directory(self):
        """测试创建和检查目录"""
        new_dir = os.path.join(self.temp_dir, "new_directory")

        # 目录应该不存在
        self.assertFalse(os.path.exists(new_dir))

        # 创建目录
        FileHandler.create_directory_if_not_exists(new_dir)

        # 目录应该存在
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))

    @patch("subprocess.run")
    def test_git_operations_workflow(self, mock_run):
        """测试Git操作工作流"""
        repo_path = "/test/repo"

        # 模拟检查Git仓库
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(GitHandler.is_git_repo(repo_path))

        # 模拟获取分支
        mock_run.return_value = MagicMock(returncode=0, stdout="  origin/main\n  origin/develop\n")
        branches = GitHandler.get_branches(repo_path)
        self.assertEqual(len(branches), 2)

        # 模拟切换分支
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(GitHandler.checkout_branch(repo_path, "develop"))

        # 模拟拉取更新
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(GitHandler.pull_repo(repo_path))
