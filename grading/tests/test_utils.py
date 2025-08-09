"""
Django tests for utility functions in the grading app.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from grading.utils import FileHandler, GitHandler


class FileHandlerTest(TestCase):
    """Test cases for FileHandler utility class."""

    def setUp(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        
        # Create test file
        with open(self.test_file_path, 'w') as f:
            f.write("Test content")

    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_mime_type_text_file(self):
        """Test getting MIME type for text file."""
        mime_type = FileHandler.get_mime_type(self.test_file_path)
        self.assertEqual(mime_type, "text/plain")

    def test_get_mime_type_docx_file(self):
        """Test getting MIME type for DOCX file."""
        docx_path = os.path.join(self.temp_dir, "test.docx")
        with open(docx_path, 'w') as f:
            f.write("Test DOCX content")
        
        mime_type = FileHandler.get_mime_type(docx_path)
        self.assertIn("wordprocessingml.document", mime_type)

    def test_get_mime_type_pdf_file(self):
        """Test getting MIME type for PDF file."""
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("Test PDF content")
        
        mime_type = FileHandler.get_mime_type(pdf_path)
        self.assertEqual(mime_type, "application/pdf")

    def test_get_mime_type_nonexistent_file(self):
        """Test getting MIME type for nonexistent file."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        mime_type = FileHandler.get_mime_type(nonexistent_path)
        self.assertIsNone(mime_type)

    def test_is_safe_path(self):
        """Test path safety validation."""
        # Test safe path
        safe_path = os.path.join(settings.MEDIA_ROOT, "grades", "test.docx")
        self.assertTrue(FileHandler.is_safe_path(safe_path))
        
        # Test unsafe path (outside media directory)
        unsafe_path = "/etc/passwd"
        self.assertFalse(FileHandler.is_safe_path(unsafe_path))
        
        # Test path with directory traversal
        traversal_path = os.path.join(settings.MEDIA_ROOT, "grades", "..", "..", "etc", "passwd")
        self.assertFalse(FileHandler.is_safe_path(traversal_path))

    def test_validate_file_extension(self):
        """Test file extension validation."""
        # Test valid extensions
        valid_extensions = ['.txt', '.pdf', '.docx', '.doc']
        for ext in valid_extensions:
            file_path = f"test{ext}"
            self.assertTrue(FileHandler.validate_file_extension(file_path))
        
        # Test invalid extensions
        invalid_extensions = ['.exe', '.bat', '.sh', '.py']
        for ext in invalid_extensions:
            file_path = f"test{ext}"
            self.assertFalse(FileHandler.validate_file_extension(file_path))

    def test_get_file_size(self):
        """Test getting file size."""
        file_size = FileHandler.get_file_size(self.test_file_path)
        self.assertIsInstance(file_size, int)
        self.assertGreater(file_size, 0)

    def test_get_file_size_nonexistent(self):
        """Test getting file size for nonexistent file."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        file_size = FileHandler.get_file_size(nonexistent_path)
        self.assertEqual(file_size, 0)

    def test_create_directory_if_not_exists(self):
        """Test creating directory if it doesn't exist."""
        new_dir = os.path.join(self.temp_dir, "new_directory")
        FileHandler.create_directory_if_not_exists(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))

    def test_create_directory_if_exists(self):
        """Test creating directory when it already exists."""
        # Create directory first
        existing_dir = os.path.join(self.temp_dir, "existing_directory")
        os.makedirs(existing_dir, exist_ok=True)
        
        # Try to create it again
        FileHandler.create_directory_if_not_exists(existing_dir)
        self.assertTrue(os.path.exists(existing_dir))


class GitHandlerTest(TestCase):
    """Test cases for GitHandler utility class."""

    def setUp(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_name = "test-repo"
        self.repo_path = os.path.join(self.temp_dir, self.repo_name)

    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('grading.utils.subprocess.run')
    def test_clone_repo_success(self, mock_run):
        """Test successful repository cloning."""
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)
        
        result = GitHandler.clone_repo(self.repo_name, self.repo_path)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_clone_repo_failure(self, mock_run):
        """Test failed repository cloning."""
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(returncode=1)
        
        result = GitHandler.clone_repo(self.repo_name, self.repo_path)
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_pull_repo_success(self, mock_run):
        """Test successful repository pulling."""
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)
        
        result = GitHandler.pull_repo(self.repo_path)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_pull_repo_failure(self, mock_run):
        """Test failed repository pulling."""
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(returncode=1)
        
        result = GitHandler.pull_repo(self.repo_path)
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_checkout_branch_success(self, mock_run):
        """Test successful branch checkout."""
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)
        
        result = GitHandler.checkout_branch(self.repo_path, "main")
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_checkout_branch_failure(self, mock_run):
        """Test failed branch checkout."""
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(returncode=1)
        
        result = GitHandler.checkout_branch(self.repo_path, "nonexistent")
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch('grading.utils.subprocess.run')
    def test_get_branches_success(self, mock_run):
        """Test getting repository branches."""
        # Mock successful subprocess run with branch output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"* main\n  develop\n  feature-branch\n"
        )
        
        branches = GitHandler.get_branches(self.repo_path)
        self.assertIsInstance(branches, list)
        self.assertIn("main", branches)
        self.assertIn("develop", branches)
        self.assertIn("feature-branch", branches)

    @patch('grading.utils.subprocess.run')
    def test_get_branches_failure(self, mock_run):
        """Test getting branches when command fails."""
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(returncode=1)
        
        branches = GitHandler.get_branches(self.repo_path)
        self.assertEqual(branches, [])

    def test_is_git_repository(self):
        """Test checking if directory is a git repository."""
        # Test non-git directory
        self.assertFalse(GitHandler.is_git_repository(self.temp_dir))
        
        # Test with .git directory
        git_dir = os.path.join(self.temp_dir, ".git")
        os.makedirs(git_dir, exist_ok=True)
        self.assertTrue(GitHandler.is_git_repository(self.temp_dir))

    def test_get_current_branch(self):
        """Test getting current branch."""
        # Create .git directory and HEAD file
        git_dir = os.path.join(self.temp_dir, ".git")
        os.makedirs(git_dir, exist_ok=True)
        
        head_file = os.path.join(git_dir, "HEAD")
        with open(head_file, 'w') as f:
            f.write("ref: refs/heads/main")
        
        current_branch = GitHandler.get_current_branch(self.temp_dir)
        self.assertEqual(current_branch, "main")

    def test_get_current_branch_nonexistent(self):
        """Test getting current branch for non-git directory."""
        current_branch = GitHandler.get_current_branch(self.temp_dir)
        self.assertIsNone(current_branch)


class UtilityIntegrationTest(TestCase):
    """Integration tests for utility functions."""

    def setUp(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_handler_and_git_handler_integration(self):
        """Test FileHandler and GitHandler working together."""
        # Create a test repository structure
        repo_path = os.path.join(self.temp_dir, "test-repo")
        FileHandler.create_directory_if_not_exists(repo_path)
        
        # Create some files in the repository
        test_file = os.path.join(repo_path, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Test file operations
        self.assertTrue(FileHandler.validate_file_extension(test_file))
        self.assertGreater(FileHandler.get_file_size(test_file), 0)
        self.assertEqual(FileHandler.get_mime_type(test_file), "text/plain")
        
        # Test path safety
        self.assertTrue(FileHandler.is_safe_path(test_file))

    @patch('grading.utils.subprocess.run')
    def test_git_operations_with_file_operations(self, mock_run):
        """Test Git operations with file operations."""
        # Mock successful git operations
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create repository directory
        repo_path = os.path.join(self.temp_dir, "git-repo")
        FileHandler.create_directory_if_not_exists(repo_path)
        
        # Test git operations
        self.assertTrue(GitHandler.clone_repo("test-repo", repo_path))
        self.assertTrue(GitHandler.pull_repo(repo_path))
        self.assertTrue(GitHandler.checkout_branch(repo_path, "main"))
        
        # Verify directory exists
        self.assertTrue(os.path.exists(repo_path))
        self.assertTrue(os.path.isdir(repo_path))
