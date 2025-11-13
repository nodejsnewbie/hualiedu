"""
Git处理工具测试
"""
import os
import tempfile
import shutil
from django.test import TestCase
from unittest.mock import patch, MagicMock
from grading.utils import GitHandler


class GitHandlerTestCase(TestCase):
    """GitHandler工具类测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_repo_path = os.path.join(self.temp_dir, "test_repo")

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_is_git_repo_valid(self, mock_run):
        """测试检查有效的Git仓库"""
        mock_run.return_value = MagicMock(returncode=0)
        result = GitHandler.is_git_repo(self.test_repo_path)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_is_git_repo_invalid(self, mock_run):
        """测试检查无效的Git仓库"""
        mock_run.return_value = MagicMock(returncode=1)
        result = GitHandler.is_git_repo(self.test_repo_path)
        self.assertFalse(result)

    @patch('grading.utils.GitHandler.ensure_branch', return_value=True)
    @patch('subprocess.run')
    def test_pull_repo_with_changes(self, mock_run, mock_ensure):
        """测试拉取仓库时有本地更改"""
        # 模拟git status返回有更改
        mock_status = MagicMock(returncode=0, stdout=" M file.txt\n")
        # 模拟git add成功
        mock_add = MagicMock(returncode=0)
        # 模拟git commit成功
        mock_commit = MagicMock(returncode=0)
        # 模拟git push成功
        mock_push = MagicMock(returncode=0)
        # 模拟git pull成功
        mock_pull = MagicMock(returncode=0)
        
        mock_run.side_effect = [mock_status, mock_add, mock_commit, mock_push, mock_pull]
        
        result = GitHandler.pull_repo(self.test_repo_path, branch="main")
        self.assertTrue(result)
        mock_ensure.assert_called_once_with(self.test_repo_path, "main")
        self.assertEqual(mock_run.call_count, 5)

    @patch('grading.utils.GitHandler.ensure_branch', return_value=True)
    @patch('subprocess.run')
    def test_pull_repo_without_changes(self, mock_run, mock_ensure):
        """测试拉取仓库时没有本地更改"""
        # 模拟git status返回无更改
        mock_status = MagicMock(returncode=0, stdout="")
        # 模拟git pull成功
        mock_pull = MagicMock(returncode=0)
        
        mock_run.side_effect = [mock_status, mock_pull]
        
        result = GitHandler.pull_repo(self.test_repo_path, branch="develop")
        self.assertTrue(result)
        mock_ensure.assert_called_once_with(self.test_repo_path, "develop")
        self.assertEqual(mock_run.call_count, 2)

    @patch('grading.utils.GitHandler.ensure_branch', return_value=True)
    @patch('subprocess.run')
    def test_pull_repo_commit_failed(self, mock_run, mock_ensure):
        """测试提交失败的情况"""
        mock_status = MagicMock(returncode=0, stdout=" M file.txt\n")
        mock_add = MagicMock(returncode=0)
        mock_commit = MagicMock(returncode=1, stderr="commit failed")
        
        mock_run.side_effect = [mock_status, mock_add, mock_commit]
        
        result = GitHandler.pull_repo(self.test_repo_path, branch="feature")
        self.assertFalse(result)
        mock_ensure.assert_called_once_with(self.test_repo_path, "feature")

    @patch('grading.utils.GitHandler.ensure_branch', return_value=False)
    def test_pull_repo_branch_switch_failed(self, mock_ensure):
        result = GitHandler.pull_repo(self.test_repo_path, branch="dev")
        self.assertFalse(result)
        mock_ensure.assert_called_once_with(self.test_repo_path, "dev")

    @patch('subprocess.run')
    def test_clone_repo_remote_success(self, mock_run):
        """测试克隆远程仓库成功"""
        mock_run.return_value = MagicMock(returncode=0)
        result = GitHandler.clone_repo_remote("git@example.com:repo.git", self.test_repo_path)
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_clone_repo_remote_failed(self, mock_run):
        """测试克隆远程仓库失败"""
        mock_run.return_value = MagicMock(returncode=1)
        result = GitHandler.clone_repo_remote("git@example.com:repo.git", self.test_repo_path)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_get_branches(self, mock_run):
        """测试获取分支列表"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="  origin/main\n  origin/dev\n  origin/feature\n"
        )
        branches = GitHandler.get_branches(self.test_repo_path)
        self.assertEqual(len(branches), 3)
        self.assertIn("origin/main", branches)
        self.assertIn("origin/dev", branches)

    def test_is_git_repository(self):
        """测试检查是否为Git仓库（通过.git目录）"""
        # 创建.git目录
        git_dir = os.path.join(self.test_repo_path, ".git")
        os.makedirs(git_dir)
        
        result = GitHandler.is_git_repository(self.test_repo_path)
        self.assertTrue(result)
        
        # 删除.git目录
        shutil.rmtree(git_dir)
        result = GitHandler.is_git_repository(self.test_repo_path)
        self.assertFalse(result)
    @patch('subprocess.run')
    def test_clone_repo_remote_with_branch(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = GitHandler.clone_repo_remote("git@example.com:repo.git", self.test_repo_path, branch="dev")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "clone", "-b", "dev", "git@example.com:repo.git", self.test_repo_path],
            capture_output=True,
            text=True,
        )
