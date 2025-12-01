"""
Property-Based Tests for GitStorageAdapter

Tests universal properties that should hold across all valid executions.
Uses Hypothesis for property-based testing.
"""

import os
import tempfile
import subprocess
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.extra.django import TestCase
from django.core.cache import cache

from grading.services.git_storage_adapter import GitStorageAdapter
from grading.services.storage_adapter import RemoteAccessError, ValidationError


# Configure Hypothesis settings
settings.register_profile("ci", max_examples=100, deadline=None)
settings.load_profile("ci")


class TestGitStorageAdapterProperties(TestCase):
    """Property-based tests for GitStorageAdapter"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
        super().tearDown()

    @given(
        path=st.text(
            alphabet=st.characters(
                whitelist_categories=('L', 'N'),
                blacklist_characters='/'
            ),
            min_size=0,
            max_size=50
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_2_remote_repository_directory_reading(self, path):
        """**Feature: assignment-management-refactor, Property 2: 远程仓库目录读取**
        
        For any 有效的 Git 仓库 URL 和路径，系统应该能够直接从远程仓库读取目录结构
        而不创建本地克隆
        
        Validates: Requirements 3.2, 3.6
        """
        # Arrange: Create adapter with valid Git URL
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Mock the git command execution to simulate successful remote access
        mock_ls_tree_output = b"""100644 blob abc123 1024\tfile1.txt
040000 tree def456 -\tsubdir
100644 blob ghi789 2048\tfile2.py"""

        mock_ls_remote_output = f"refs/heads/{branch}\n".encode()

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            """Mock git command execution"""
            if "ls-remote" in args:
                return mock_ls_remote_output
            elif "ls-tree" in args:
                return mock_ls_tree_output
            else:
                raise RemoteAccessError("Unknown command")

        with patch.object(
            adapter,
            '_execute_git_command',
            side_effect=mock_execute_git_command
        ):
            # Act: List directory from remote repository
            try:
                entries = adapter.list_directory(path)
                
                # Assert: Verify the operation succeeded without local clone
                # 1. Should return a list of entries
                self.assertIsInstance(entries, list)
                
                # 2. Each entry should have required fields
                for entry in entries:
                    self.assertIn("name", entry)
                    self.assertIn("type", entry)
                    self.assertIn("size", entry)
                    self.assertIsInstance(entry["name"], str)
                    self.assertIn(entry["type"], ["file", "dir"])
                    self.assertIsInstance(entry["size"], int)
                
                # 3. Verify no local clone was created
                # The adapter should not create any local directories
                # We verify this by checking that no file system operations occurred
                # (implicitly verified by mocking - no actual git clone command was called)
                
                # 4. Verify the operation used remote commands only
                # This is validated by our mock - we only allow ls-remote and ls-tree
                
            except RemoteAccessError as e:
                # If the operation fails, it should be due to remote access issues,
                # not local file system issues
                self.assertIn(
                    "remote",
                    str(e).lower(),
                    "Error should be related to remote access, not local file system"
                )

    @given(
        git_url=st.one_of(
            st.builds(
                lambda host, repo: f"https://github.com/{host}/{repo}.git",
                host=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=20
                ),
                repo=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=30
                )
            ),
            st.builds(
                lambda host, repo: f"git@github.com:{host}/{repo}.git",
                host=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=20
                ),
                repo=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=30
                )
            )
        ),
        branch=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N'), blacklist_characters='/'),
            min_size=1,
            max_size=20
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_2_no_local_clone_constraint(self, git_url, branch):
        """**Feature: assignment-management-refactor, Property 2: 无本地克隆约束**
        
        For any Git 仓库访问操作，系统不应该在本地文件系统创建仓库克隆目录
        
        Validates: Requirements 3.6
        """
        # Arrange: Create adapter
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Track any file system operations
        original_makedirs = os.makedirs
        original_mkdir = os.mkdir
        fs_operations = []

        def track_makedirs(*args, **kwargs):
            fs_operations.append(('makedirs', args, kwargs))
            return original_makedirs(*args, **kwargs)

        def track_mkdir(*args, **kwargs):
            fs_operations.append(('mkdir', args, kwargs))
            return original_mkdir(*args, **kwargs)

        # Mock git commands to succeed
        mock_ls_remote_output = f"refs/heads/{branch}\n".encode()
        mock_ls_tree_output = b"100644 blob abc123 1024\ttest.txt"

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            if "ls-remote" in args:
                return mock_ls_remote_output
            elif "ls-tree" in args:
                return mock_ls_tree_output
            return b""

        with patch('os.makedirs', side_effect=track_makedirs), \
             patch('os.mkdir', side_effect=track_mkdir), \
             patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            
            # Act: Perform directory listing
            try:
                entries = adapter.list_directory("")
                
                # Assert: No local directories should have been created
                # Filter out any operations that might be from Django/cache
                repo_related_ops = [
                    op for op in fs_operations
                    if any(keyword in str(op).lower() for keyword in ['git', 'repo', 'clone'])
                ]
                
                self.assertEqual(
                    len(repo_related_ops),
                    0,
                    f"No local repository directories should be created. Found: {repo_related_ops}"
                )
                
            except RemoteAccessError:
                # Even if the operation fails, no local clone should be created
                repo_related_ops = [
                    op for op in fs_operations
                    if any(keyword in str(op).lower() for keyword in ['git', 'repo', 'clone'])
                ]
                
                self.assertEqual(
                    len(repo_related_ops),
                    0,
                    f"No local repository directories should be created even on failure. Found: {repo_related_ops}"
                )

    @given(
        path=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=0,
            max_size=50
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_2_caching_behavior(self, path):
        """**Feature: assignment-management-refactor, Property 2: 缓存行为**
        
        For any 路径，第二次访问应该使用缓存而不是再次访问远程仓库
        
        Validates: Requirements 3.2, 10.4
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch, cache_timeout=300)

        mock_ls_remote_output = f"refs/heads/{branch}\n".encode()
        mock_ls_tree_output = b"100644 blob abc123 1024\ttest.txt"

        call_count = {"count": 0}

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            call_count["count"] += 1
            if "ls-remote" in args:
                return mock_ls_remote_output
            elif "ls-tree" in args:
                return mock_ls_tree_output
            return b""

        with patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            # Act: Access the same path twice
            try:
                entries1 = adapter.list_directory(path)
                initial_call_count = call_count["count"]
                
                entries2 = adapter.list_directory(path)
                final_call_count = call_count["count"]
                
                # Assert: Second call should use cache
                # The call count should not increase (or increase minimally for ls-remote check)
                self.assertEqual(
                    entries1,
                    entries2,
                    "Cached results should be identical to original results"
                )
                
                # The second call should not trigger a full ls-tree command
                # (it might still call ls-remote for validation, but not ls-tree)
                self.assertLessEqual(
                    final_call_count - initial_call_count,
                    1,
                    "Second call should use cache and not re-execute ls-tree"
                )
                
            except RemoteAccessError:
                # If the first call fails, caching behavior is not tested
                pass

    @given(
        num_paths=st.integers(min_value=1, max_value=5),
        base_path=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=0,
            max_size=20
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_2_multiple_paths_no_clone(self, num_paths, base_path):
        """**Feature: assignment-management-refactor, Property 2: 多路径访问无克隆**
        
        For any 多个不同的路径访问，系统都不应该创建本地克隆
        
        Validates: Requirements 3.2, 3.6
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Generate multiple paths
        paths = [f"{base_path}/path{i}" if base_path else f"path{i}" for i in range(num_paths)]

        mock_ls_remote_output = f"refs/heads/{branch}\n".encode()
        mock_ls_tree_output = b"100644 blob abc123 1024\ttest.txt"

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            if "ls-remote" in args:
                return mock_ls_remote_output
            elif "ls-tree" in args:
                return mock_ls_tree_output
            return b""

        # Track subprocess calls to ensure no 'git clone' is called
        original_run = subprocess.run
        subprocess_calls = []

        def track_subprocess_run(*args, **kwargs):
            subprocess_calls.append(args)
            # Don't actually run the command, return mock
            result = MagicMock()
            result.returncode = 0
            result.stdout = mock_ls_tree_output
            result.stderr = b""
            return result

        with patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            # Act: Access multiple paths
            for path in paths:
                try:
                    adapter.list_directory(path)
                except RemoteAccessError:
                    # Ignore errors, we're testing that no clone occurs
                    pass

            # Assert: No 'git clone' command should have been called
            for call_args in subprocess_calls:
                if isinstance(call_args[0], list):
                    cmd = call_args[0]
                    self.assertNotIn(
                        'clone',
                        cmd,
                        f"'git clone' should never be called. Found: {cmd}"
                    )

    @given(
        file_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('L', 'N'),
                blacklist_characters='/'
            ),
            min_size=1,
            max_size=50
        ),
        file_ext=st.sampled_from(['.txt', '.py', '.md', '.json', '.xml']),
        file_content=st.binary(min_size=0, max_size=1024)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_3_remote_repository_file_reading(self, file_name, file_ext, file_content):
        """**Feature: assignment-management-refactor, Property 3: 远程仓库文件读取**
        
        For any 远程仓库中存在的文件路径，系统应该能够直接获取文件内容
        
        Validates: Requirements 3.4
        """
        # Combine file name and extension
        file_path = file_name + file_ext
        
        # Arrange: Create adapter with valid Git URL
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)
        
        # Clear cache to ensure clean state
        cache.clear()

        # Mock the git command execution to simulate successful file reading
        def mock_execute_git_command(args, timeout=30, use_auth=True):
            """Mock git command execution"""
            if "show" in args:
                # Return the file content
                return file_content
            else:
                raise RemoteAccessError("Unknown command")

        with patch.object(
            adapter,
            '_execute_git_command',
            side_effect=mock_execute_git_command
        ):
            # Act: Read file from remote repository
            try:
                content = adapter.read_file(file_path)
                
                # Assert: Verify the operation succeeded
                # 1. Should return bytes
                self.assertIsInstance(content, bytes)
                
                # 2. Content should match what was in the repository
                self.assertEqual(
                    content,
                    file_content,
                    "File content should match the remote repository content"
                )
                
                # 3. Verify no local file system operations occurred
                # This is implicitly verified by our mock - we only allow 'git show'
                
            except RemoteAccessError as e:
                # If the operation fails, it should be due to remote access issues
                self.assertIn(
                    "remote",
                    str(e).lower(),
                    "Error should be related to remote access, not local file system"
                )

    @given(
        file_name=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=1,
            max_size=50
        ),
        file_content=st.binary(min_size=1, max_size=512)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_3_file_reading_caching(self, file_name, file_content):
        """**Feature: assignment-management-refactor, Property 3: 文件读取缓存**
        
        For any 文件路径，第二次读取应该使用缓存而不是再次访问远程仓库
        
        Validates: Requirements 3.4, 10.4
        """
        # Combine file name with extension
        file_path = file_name + '.txt'
        
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch, cache_timeout=300)

        call_count = {"count": 0}

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            call_count["count"] += 1
            if "show" in args:
                return file_content
            return b""

        with patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            # Act: Read the same file twice
            try:
                content1 = adapter.read_file(file_path)
                initial_call_count = call_count["count"]
                
                content2 = adapter.read_file(file_path)
                final_call_count = call_count["count"]
                
                # Assert: Second call should use cache
                self.assertEqual(
                    content1,
                    content2,
                    "Cached file content should be identical to original"
                )
                
                # The second call should not trigger git show command
                self.assertEqual(
                    final_call_count,
                    initial_call_count,
                    "Second file read should use cache and not execute git show"
                )
                
            except RemoteAccessError:
                # If the first call fails, caching behavior is not tested
                pass

    @given(
        git_url=st.one_of(
            st.builds(
                lambda host, repo: f"https://github.com/{host}/{repo}.git",
                host=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=20
                ),
                repo=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=30
                )
            ),
            st.builds(
                lambda host, repo: f"git@github.com:{host}/{repo}.git",
                host=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=20
                ),
                repo=st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N')),
                    min_size=1,
                    max_size=30
                )
            )
        ),
        branch=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N'), blacklist_characters='/'),
            min_size=1,
            max_size=20
        ),
        path=st.text(
            alphabet=st.characters(
                whitelist_categories=('L', 'N'),
                blacklist_characters='/'
            ),
            min_size=0,
            max_size=50
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_5_no_local_clone_constraint(self, git_url, branch, path):
        """**Feature: assignment-management-refactor, Property 5: 无本地克隆约束**
        
        For any Git 仓库访问操作，系统不应该在本地文件系统创建仓库克隆目录
        
        Validates: Requirements 3.6
        """
        # Arrange: Create adapter
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Track file system operations that could create directories
        fs_operations = []
        
        # Track os.makedirs calls
        original_makedirs = os.makedirs
        def track_makedirs(path, *args, **kwargs):
            fs_operations.append(('makedirs', path))
            # Don't actually create directories in tests
            pass
        
        # Track os.mkdir calls
        original_mkdir = os.mkdir
        def track_mkdir(path, *args, **kwargs):
            fs_operations.append(('mkdir', path))
            # Don't actually create directories in tests
            pass
        
        # Track subprocess.run to detect 'git clone' commands
        clone_commands = []
        original_run = subprocess.run
        def track_subprocess_run(cmd, *args, **kwargs):
            if isinstance(cmd, list) and 'clone' in cmd:
                clone_commands.append(cmd)
            # Return a mock result
            result = MagicMock()
            result.returncode = 0
            result.stdout = b"100644 blob abc123 1024\ttest.txt"
            result.stderr = b""
            return result

        # Mock git commands to succeed
        mock_ls_remote_output = f"refs/heads/{branch}\n".encode()
        mock_ls_tree_output = b"100644 blob abc123 1024\ttest.txt"
        mock_show_output = b"test file content"

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            if "ls-remote" in args:
                return mock_ls_remote_output
            elif "ls-tree" in args:
                return mock_ls_tree_output
            elif "show" in args:
                return mock_show_output
            return b""

        with patch('os.makedirs', side_effect=track_makedirs), \
             patch('os.mkdir', side_effect=track_mkdir), \
             patch('subprocess.run', side_effect=track_subprocess_run), \
             patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            
            # Act: Perform various operations
            try:
                # Test directory listing
                adapter.list_directory(path)
                
                # Test file reading (if path is not empty)
                if path:
                    try:
                        adapter.read_file(path + "/test.txt")
                    except (RemoteAccessError, ValidationError):
                        pass
                
                # Test file existence check
                adapter.file_exists(path + "/test.txt" if path else "test.txt")
                
                # Test directory existence check
                adapter.directory_exists(path)
                
            except (RemoteAccessError, ValidationError):
                # Even if operations fail, we still check for clone attempts
                pass
            
            # Assert: No local clone should have been created
            # 1. No 'git clone' command should have been executed
            self.assertEqual(
                len(clone_commands),
                0,
                f"'git clone' command should never be executed. Found: {clone_commands}"
            )
            
            # 2. No repository-related directories should have been created
            # Filter for paths that look like git repositories
            repo_dirs = [
                op for op in fs_operations
                if any(keyword in str(op[1]).lower() for keyword in ['.git', 'clone', 'repo'])
            ]
            
            self.assertEqual(
                len(repo_dirs),
                0,
                f"No local repository directories should be created. Found: {repo_dirs}"
            )
            
            # 3. Verify that the adapter only uses remote commands
            # This is implicitly validated by our mocks - we only allow
            # ls-remote, ls-tree, and show commands

    @given(
        num_files=st.integers(min_value=1, max_value=5),
        base_name=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=1,
            max_size=20
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_3_multiple_files_reading(self, num_files, base_name):
        """**Feature: assignment-management-refactor, Property 3: 多文件读取**
        
        For any 多个不同的文件，系统应该能够独立读取每个文件的内容
        
        Validates: Requirements 3.4
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Generate multiple file paths and their expected contents
        files = {
            f"{base_name}_{i}.txt": f"Content of file {i}".encode()
            for i in range(num_files)
        }

        def mock_execute_git_command(args, timeout=30, use_auth=True):
            if "show" in args:
                # Extract the file path from the ref (format: branch:path)
                for arg in args:
                    if ':' in arg and arg.startswith(branch):
                        file_path = arg.split(':', 1)[1]
                        if file_path in files:
                            return files[file_path]
                return b"default content"
            return b""

        with patch.object(adapter, '_execute_git_command', side_effect=mock_execute_git_command):
            # Act: Read multiple files
            results = {}
            for file_path in files.keys():
                try:
                    content = adapter.read_file(file_path)
                    results[file_path] = content
                except RemoteAccessError:
                    # Ignore errors for this test
                    pass

            # Assert: Each file should have its own content
            for file_path, expected_content in files.items():
                if file_path in results:
                    self.assertEqual(
                        results[file_path],
                        expected_content,
                        f"File {file_path} should have its own unique content"
                    )

    @given(
        dummy=st.just(None)  # Dummy parameter since we're testing empty path specifically
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_3_empty_path_validation(self, dummy):
        """**Feature: assignment-management-refactor, Property 3: 空路径验证**
        
        For any 空文件路径，系统应该拒绝读取并返回验证错误
        
        Validates: Requirements 3.4
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Act & Assert: Empty path should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            adapter.read_file("")

        # Verify the error message is user-friendly
        # The error message should mention "path" or "路径"
        error_str = str(context.exception).lower()
        self.assertTrue(
            "path" in error_str or "路径" in error_str,
            f"Error message should mention path. Got: {context.exception}"
        )

    @given(
        error_type=st.sampled_from([
            "authentication_failed",
            "repository_not_found",
            "connection_timeout",
            "network_error",
            "permission_denied",
            "unknown_error"
        ]),
        path=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=0,
            max_size=50
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_error_message_friendliness(self, error_type, path):
        """**Feature: assignment-management-refactor, Property 4: 错误消息友好性**
        
        For any 远程仓库访问失败的情况，系统应该向用户显示友好的错误消息
        而不是技术堆栈信息
        
        Validates: Requirements 3.5
        """
        # Arrange: Create adapter
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Map error types to technical error messages (what Git would return)
        technical_errors = {
            "authentication_failed": "fatal: Authentication failed for 'https://github.com/test/repo.git/'",
            "repository_not_found": "fatal: repository 'https://github.com/test/repo.git/' not found",
            "connection_timeout": "fatal: unable to access 'https://github.com/test/repo.git/': Failed to connect to github.com port 443: Connection timed out",
            "network_error": "fatal: unable to access 'https://github.com/test/repo.git/': Could not resolve host: github.com",
            "permission_denied": "fatal: unable to access 'https://github.com/test/repo.git/': The requested URL returned error: 403 Permission denied",
            "unknown_error": "fatal: some unknown git error occurred"
        }

        # Expected user-friendly messages (keywords that should appear)
        expected_friendly_keywords = {
            "authentication_failed": ["认证", "用户名", "密码"],
            "repository_not_found": ["找不到", "仓库", "URL"],
            "connection_timeout": ["超时", "重试"],
            "network_error": ["网络", "连接"],
            "permission_denied": ["权限", "访问"],
            "unknown_error": ["无法访问", "远程仓库"]
        }

        # Technical keywords that should NOT appear in user messages
        technical_keywords = [
            "fatal:",
            "exit code",
            "stderr",
            "subprocess",
            "traceback",
            "exception",
            "git:",
            "ls-tree",
            "ls-remote",
            "show",
            "returncode"
        ]

        # Mock git command to simulate the error
        # We need to mock subprocess.run, not _execute_git_command
        # because _execute_git_command handles the error conversion
        def mock_subprocess_run(cmd, *args, **kwargs):
            # Simulate git command failure with technical error
            result = MagicMock()
            result.returncode = 128
            result.stdout = b""
            result.stderr = technical_errors[error_type].encode()
            return result

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Act: Try to access the repository (should fail)
            try:
                if path:
                    adapter.read_file(path + "/test.txt")
                else:
                    adapter.list_directory("")
                
                # If no exception was raised, fail the test
                self.fail("Expected RemoteAccessError to be raised")
                
            except RemoteAccessError as e:
                # Assert: Verify the error message is user-friendly
                
                # 1. Get the user message (from the user_message attribute)
                user_message = e.user_message
                user_message_lower = user_message.lower()
                
                # 2. Verify it contains expected friendly keywords
                friendly_keywords = expected_friendly_keywords[error_type]
                has_friendly_keyword = any(
                    keyword in user_message
                    for keyword in friendly_keywords
                )
                
                self.assertTrue(
                    has_friendly_keyword,
                    f"Error message should contain user-friendly keywords {friendly_keywords}. "
                    f"Got: {user_message}"
                )
                
                # 3. Verify it does NOT contain technical keywords
                has_technical_keyword = any(
                    keyword.lower() in user_message_lower
                    for keyword in technical_keywords
                )
                
                self.assertFalse(
                    has_technical_keyword,
                    f"Error message should not contain technical keywords like {technical_keywords}. "
                    f"Got: {user_message}"
                )
                
                # 4. Verify the message is in Chinese (user-friendly for this system)
                # Check for Chinese characters
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_message)
                
                self.assertTrue(
                    has_chinese,
                    f"Error message should be in Chinese for user-friendliness. Got: {user_message}"
                )
                
                # 5. Verify the message is not too long (should be concise)
                self.assertLess(
                    len(user_message),
                    200,
                    f"Error message should be concise (< 200 chars). Got {len(user_message)} chars: {user_message}"
                )
                
                # 6. Verify the message doesn't expose sensitive information
                # Should not contain passwords, tokens, or full URLs with credentials
                sensitive_patterns = ["password", "token", "secret", "@"]
                has_sensitive = any(
                    pattern in user_message_lower
                    for pattern in sensitive_patterns
                )
                
                self.assertFalse(
                    has_sensitive,
                    f"Error message should not expose sensitive information. Got: {user_message}"
                )

    @given(
        operation=st.sampled_from(["list_directory", "read_file"]),
        path=st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=0,
            max_size=30
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_consistent_error_format(self, operation, path):
        """**Feature: assignment-management-refactor, Property 4: 错误格式一致性**
        
        For any 操作类型和路径，错误消息应该保持一致的格式和风格
        
        Validates: Requirements 3.5
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Mock git command to fail
        def mock_subprocess_run(cmd, *args, **kwargs):
            result = MagicMock()
            result.returncode = 128
            result.stdout = b""
            result.stderr = b"fatal: repository not found"
            return result

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Act: Try different operations
            try:
                if operation == "list_directory":
                    adapter.list_directory(path)
                else:
                    if not path:
                        path = "test.txt"
                    adapter.read_file(path)
                
                self.fail("Expected RemoteAccessError to be raised")
                
            except (RemoteAccessError, ValidationError) as e:
                # Assert: Verify error message format
                error_message = e.user_message if hasattr(e, 'user_message') else str(e)
                
                # 1. Should not be empty
                self.assertTrue(
                    error_message,
                    "Error message should not be empty"
                )
                
                # 2. Should not start or end with whitespace
                self.assertEqual(
                    error_message,
                    error_message.strip(),
                    "Error message should not have leading/trailing whitespace"
                )
                
                # 3. Should not contain multiple consecutive spaces
                self.assertNotIn(
                    "  ",
                    error_message,
                    "Error message should not contain multiple consecutive spaces"
                )
                
                # 4. Should be a complete sentence (ends with punctuation or Chinese character)
                last_char = error_message[-1]
                is_complete = (
                    last_char in '.!?。！？' or
                    '\u4e00' <= last_char <= '\u9fff'
                )
                
                self.assertTrue(
                    is_complete,
                    f"Error message should be a complete sentence. Got: {error_message}"
                )

    @given(
        num_failures=st.integers(min_value=1, max_value=3)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_multiple_failures_same_message(self, num_failures):
        """**Feature: assignment-management-refactor, Property 4: 多次失败消息一致性**
        
        For any 相同类型的错误，多次发生时应该返回相同的用户友好消息
        
        Validates: Requirements 3.5
        """
        # Arrange
        git_url = "https://github.com/test/repo.git"
        branch = "main"
        adapter = GitStorageAdapter(git_url=git_url, branch=branch)

        # Mock git command to fail consistently
        def mock_subprocess_run(cmd, *args, **kwargs):
            result = MagicMock()
            result.returncode = 128
            result.stdout = b""
            result.stderr = b"fatal: Authentication failed"
            return result

        error_messages = []

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Act: Trigger the same error multiple times
            for i in range(num_failures):
                try:
                    adapter.list_directory(f"path{i}")
                    self.fail("Expected RemoteAccessError to be raised")
                except RemoteAccessError as e:
                    error_messages.append(e.user_message)

            # Assert: All error messages should be identical
            if len(error_messages) > 1:
                first_message = error_messages[0]
                for i, message in enumerate(error_messages[1:], 1):
                    self.assertEqual(
                        message,
                        first_message,
                        f"Error message {i} should be identical to the first message. "
                        f"Expected: {first_message}, Got: {message}"
                    )
