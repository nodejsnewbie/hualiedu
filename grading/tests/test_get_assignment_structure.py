"""
Comprehensive pytest tests for get_assignment_structure method

Tests cover:
- Filesystem storage adapter integration
- Git storage adapter integration
- Error handling and user-friendly messages
- Edge cases and boundary conditions
- Requirements validation (3.2, 3.3, 3.5, 3.6)
"""

import os
import shutil
import tempfile
from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService
from grading.services.storage_adapter import RemoteAccessError, StorageError


class TestGetAssignmentStructureFilesystem(TestCase):
    """Test get_assignment_structure with filesystem storage"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant", is_active=True)

        # Create teacher user
        self.teacher = User.objects.create_user(
            username="test_teacher", password="pass123", email="teacher@test.com"
        )
        self.profile = UserProfile.objects.create(user=self.teacher, tenant=self.tenant)

        # Create semester
        self.semester = Semester.objects.create(
            name="Test Semester",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            is_active=True,
        )

        # Create course
        self.course = Course.objects.create(
            semester=self.semester, teacher=self.teacher, name="Test Course", tenant=self.tenant
        )

        # Create class
        self.class_obj = Class.objects.create(
            course=self.course, name="Test Class", tenant=self.tenant
        )

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Create service instance
        self.service = AssignmentManagementService()

    def tearDown(self):
        """Clean up test data"""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_assignment_structure_empty_directory(self):
        """Test getting structure of empty directory"""
        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Empty Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "")
        self.assertEqual(len(result["entries"]), 0)
        self.assertIsInstance(result["entries"], list)

    def test_get_assignment_structure_with_directories(self):
        """Test getting structure with multiple directories"""
        # Create test directories
        os.makedirs(os.path.join(self.temp_dir, "第一次作业"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "第二次作业"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "第三次作业"), exist_ok=True)

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 3)

        dir_names = [e["name"] for e in result["entries"] if e["type"] == "dir"]
        self.assertIn("第一次作业", dir_names)
        self.assertIn("第二次作业", dir_names)
        self.assertIn("第三次作业", dir_names)

    def test_get_assignment_structure_with_files(self):
        """Test getting structure with files"""
        # Create test directory and files
        test_dir = os.path.join(self.temp_dir, "第一次作业")
        os.makedirs(test_dir, exist_ok=True)

        with open(os.path.join(test_dir, "张三-作业1.docx"), "w") as f:
            f.write("Test content")
        with open(os.path.join(test_dir, "李四-作业1.pdf"), "w") as f:
            f.write("Test content")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure of subdirectory
        result = self.service.get_assignment_structure(assignment, "第一次作业")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "第一次作业")
        self.assertEqual(len(result["entries"]), 2)

        file_names = [e["name"] for e in result["entries"] if e["type"] == "file"]
        self.assertIn("张三-作业1.docx", file_names)
        self.assertIn("李四-作业1.pdf", file_names)

    def test_get_assignment_structure_mixed_content(self):
        """Test getting structure with both directories and files"""
        # Create mixed content
        os.makedirs(os.path.join(self.temp_dir, "第一次作业"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "第二次作业"), exist_ok=True)

        with open(os.path.join(self.temp_dir, "README.txt"), "w") as f:
            f.write("Instructions")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 3)

        dirs = [e for e in result["entries"] if e["type"] == "dir"]
        files = [e for e in result["entries"] if e["type"] == "file"]

        self.assertEqual(len(dirs), 2)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "README.txt")

    def test_get_assignment_structure_nonexistent_path(self):
        """Test getting structure of non-existent path - should return friendly error"""
        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Try to get structure of non-existent path
        result = self.service.get_assignment_structure(assignment, "不存在的目录")

        # Verify - should fail with friendly error (Requirement 3.5)
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("目录不存在", result["error"])

        # Should not contain technical details
        self.assertNotIn("Traceback", result["error"])
        self.assertNotIn("Exception", result["error"])

    def test_get_assignment_structure_nested_path(self):
        """Test getting structure of nested path"""
        # Create nested structure
        nested_path = os.path.join(self.temp_dir, "第一次作业", "提交文件")
        os.makedirs(nested_path, exist_ok=True)

        with open(os.path.join(nested_path, "homework.docx"), "w") as f:
            f.write("Content")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure of nested path
        result = self.service.get_assignment_structure(assignment, "第一次作业/提交文件")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "第一次作业/提交文件")
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["entries"][0]["name"], "homework.docx")

    def test_get_assignment_structure_with_special_characters(self):
        """Test getting structure with special characters in names"""
        # Create directories with special characters
        os.makedirs(os.path.join(self.temp_dir, "第1次作业"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "实验-1"), exist_ok=True)

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 2)

    def test_get_assignment_structure_entry_metadata(self):
        """Test that entries contain required metadata"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify entry metadata
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 1)

        entry = result["entries"][0]
        self.assertIn("name", entry)
        self.assertIn("type", entry)
        self.assertIn("size", entry)
        self.assertEqual(entry["name"], "test.txt")
        self.assertEqual(entry["type"], "file")
        self.assertGreater(entry["size"], 0)


class TestGetAssignmentStructureGit(TestCase):
    """Test get_assignment_structure with Git storage"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant Git", is_active=True)

        # Create teacher user
        self.teacher = User.objects.create_user(
            username="test_teacher_git", password="pass123", email="teacher@test.com"
        )
        self.profile = UserProfile.objects.create(user=self.teacher, tenant=self.tenant)

        # Create semester
        self.semester = Semester.objects.create(
            name="Test Semester Git",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            is_active=True,
        )

        # Create course
        self.course = Course.objects.create(
            semester=self.semester, teacher=self.teacher, name="Test Course Git", tenant=self.tenant
        )

        # Create class
        self.class_obj = Class.objects.create(
            course=self.course, name="Test Class Git", tenant=self.tenant
        )

        # Create service instance
        self.service = AssignmentManagementService()

    def test_get_assignment_structure_git_invalid_url(self):
        """Test Git storage with invalid URL - should return friendly error"""
        # Create assignment with invalid Git URL
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git Assignment",
            storage_type="git",
            git_url="https://github.com/nonexistent/repo.git",
            git_branch="main",
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify - should fail with friendly error (Requirement 3.5)
        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # Error should be user-friendly
        error_msg = result["error"]
        self.assertTrue(
            "仓库" in error_msg or "访问" in error_msg or "网络" in error_msg,
            f"Error should be user-friendly, got: {error_msg}",
        )

        # Should not contain technical details
        self.assertNotIn("Traceback", error_msg)
        self.assertNotIn("Exception", error_msg)
        self.assertNotIn("git ls-tree", error_msg)

    @patch("grading.services.git_storage_adapter.GitStorageAdapter.list_directory")
    def test_get_assignment_structure_git_success(self, mock_list_dir):
        """Test Git storage with successful response"""
        # Mock successful Git response
        mock_list_dir.return_value = [
            {"name": "第一次作业", "type": "dir", "size": 0},
            {"name": "第二次作业", "type": "dir", "size": 0},
            {"name": "README.md", "type": "file", "size": 1024},
        ]

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git Assignment",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 3)

        dir_names = [e["name"] for e in result["entries"] if e["type"] == "dir"]
        self.assertIn("第一次作业", dir_names)
        self.assertIn("第二次作业", dir_names)

    @patch("grading.services.git_storage_adapter.GitStorageAdapter.list_directory")
    def test_get_assignment_structure_git_remote_access_error(self, mock_list_dir):
        """Test Git storage with RemoteAccessError"""
        # Mock RemoteAccessError
        mock_list_dir.side_effect = RemoteAccessError(
            "Git command failed", user_message="无法访问远程仓库，请检查网络连接"
        )

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git Assignment",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "无法访问远程仓库，请检查网络连接")

    @patch("grading.services.git_storage_adapter.GitStorageAdapter.list_directory")
    def test_get_assignment_structure_git_with_path(self, mock_list_dir):
        """Test Git storage with specific path"""
        # Mock successful Git response for subdirectory
        mock_list_dir.return_value = [
            {"name": "张三-作业1.docx", "type": "file", "size": 2048},
            {"name": "李四-作业1.pdf", "type": "file", "size": 3072},
        ]

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git Assignment",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        # Get structure of subdirectory
        result = self.service.get_assignment_structure(assignment, "第一次作业")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "第一次作业")
        self.assertEqual(len(result["entries"]), 2)

        file_names = [e["name"] for e in result["entries"]]
        self.assertIn("张三-作业1.docx", file_names)
        self.assertIn("李四-作业1.pdf", file_names)


class TestGetAssignmentStructureEdgeCases(TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant Edge", is_active=True)

        # Create teacher user
        self.teacher = User.objects.create_user(username="test_teacher_edge", password="pass123")
        self.profile = UserProfile.objects.create(user=self.teacher, tenant=self.tenant)

        # Create semester
        self.semester = Semester.objects.create(
            name="Test Semester Edge",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            is_active=True,
        )

        # Create course
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="Test Course Edge",
            tenant=self.tenant,
        )

        # Create class
        self.class_obj = Class.objects.create(
            course=self.course, name="Test Class Edge", tenant=self.tenant
        )

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Create service instance
        self.service = AssignmentManagementService()

    def tearDown(self):
        """Clean up test data"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_assignment_structure_empty_path_string(self):
        """Test with empty path string (should return root)"""
        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure with empty path
        result = self.service.get_assignment_structure(assignment, "")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "")

    def test_get_assignment_structure_root_path(self):
        """Test with root path"""
        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure with no path argument (default)
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "")

    def test_get_assignment_structure_large_directory(self):
        """Test with directory containing many files"""
        # Create many files
        for i in range(100):
            with open(os.path.join(self.temp_dir, f"file_{i}.txt"), "w") as f:
                f.write(f"Content {i}")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 100)

    def test_get_assignment_structure_unicode_filenames(self):
        """Test with Unicode filenames"""
        # Create files with Unicode names
        os.makedirs(os.path.join(self.temp_dir, "第一次作业"), exist_ok=True)

        unicode_names = ["张三-作业.docx", "李四-实验报告.pdf", "王五-课程设计.zip"]

        for name in unicode_names:
            with open(os.path.join(self.temp_dir, "第一次作业", name), "w") as f:
                f.write("Content")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment, "第一次作业")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 3)

        file_names = [e["name"] for e in result["entries"]]
        for name in unicode_names:
            self.assertIn(name, file_names)

    @patch("grading.services.git_storage_adapter.GitStorageAdapter.list_directory")
    def test_get_assignment_structure_unexpected_exception(self, mock_list_dir):
        """Test handling of unexpected exceptions"""
        # Mock unexpected exception
        mock_list_dir.side_effect = RuntimeError("Unexpected error")

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git Assignment",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        # Get structure
        result = self.service.get_assignment_structure(assignment)

        # Verify - should handle gracefully with friendly error
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("无法访问作业目录", result["error"])

        # Should not expose technical details
        self.assertNotIn("RuntimeError", result["error"])
        self.assertNotIn("Unexpected error", result["error"])

    def test_get_assignment_structure_permission_denied(self):
        """Test handling of permission denied errors"""
        # Create directory with restricted permissions
        restricted_dir = os.path.join(self.temp_dir, "restricted")
        os.makedirs(restricted_dir, exist_ok=True)

        # Create assignment
        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Test Assignment",
            storage_type="filesystem",
            base_path=self.temp_dir,
        )

        # Try to change permissions (may not work on all systems)
        try:
            os.chmod(restricted_dir, 0o000)

            # Get structure
            result = self.service.get_assignment_structure(assignment, "restricted")

            # Verify - should fail with friendly error
            self.assertFalse(result["success"])
            self.assertIn("error", result)

        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_dir, 0o755)


# Pytest fixtures for parametrized tests
@pytest.fixture
def assignment_service():
    """Fixture providing AssignmentManagementService instance"""
    return AssignmentManagementService()


@pytest.fixture
def test_tenant(db):
    """Fixture providing test tenant"""
    return Tenant.objects.create(name="Pytest Tenant", is_active=True)


@pytest.fixture
def test_teacher(db, test_tenant):
    """Fixture providing test teacher with profile"""
    teacher = User.objects.create_user(username="pytest_teacher", password="pass123")
    UserProfile.objects.create(user=teacher, tenant=test_tenant)
    return teacher


@pytest.fixture
def test_course(db, test_teacher, test_tenant):
    """Fixture providing test course"""
    semester = Semester.objects.create(
        name="Pytest Semester",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        is_active=True,
    )
    return Course.objects.create(
        semester=semester, teacher=test_teacher, name="Pytest Course", tenant=test_tenant
    )


@pytest.fixture
def test_class(db, test_course, test_tenant):
    """Fixture providing test class"""
    return Class.objects.create(course=test_course, name="Pytest Class", tenant=test_tenant)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "storage_type,expected_success",
    [
        ("filesystem", True),
        ("git", False),  # Will fail without valid repo
    ],
)
def test_get_assignment_structure_storage_types(
    assignment_service,
    test_teacher,
    test_course,
    test_class,
    test_tenant,
    storage_type,
    expected_success,
    tmp_path,
):
    """Parametrized test for different storage types"""
    # Create assignment based on storage type
    if storage_type == "filesystem":
        assignment = Assignment.objects.create(
            owner=test_teacher,
            tenant=test_tenant,
            course=test_course,
            class_obj=test_class,
            name="Parametrized Assignment",
            storage_type=storage_type,
            base_path=str(tmp_path),
        )
    else:  # git
        assignment = Assignment.objects.create(
            owner=test_teacher,
            tenant=test_tenant,
            course=test_course,
            class_obj=test_class,
            name="Parametrized Assignment",
            storage_type=storage_type,
            git_url="https://github.com/invalid/repo.git",
            git_branch="main",
        )

    # Get structure
    result = assignment_service.get_assignment_structure(assignment)

    # Verify
    assert result["success"] == expected_success
    if not expected_success:
        assert "error" in result
        assert isinstance(result["error"], str)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,should_succeed",
    [
        ("", True),  # Root path
        ("第一次作业", False),  # Non-existent
        ("../../../etc", False),  # Path traversal attempt
    ],
)
def test_get_assignment_structure_path_validation(
    assignment_service,
    test_teacher,
    test_course,
    test_class,
    test_tenant,
    path,
    should_succeed,
    tmp_path,
):
    """Parametrized test for path validation"""
    # Create assignment
    assignment = Assignment.objects.create(
        owner=test_teacher,
        tenant=test_tenant,
        course=test_course,
        class_obj=test_class,
        name="Path Test Assignment",
        storage_type="filesystem",
        base_path=str(tmp_path),
    )

    # Get structure
    result = assignment_service.get_assignment_structure(assignment, path)

    # Verify
    assert result["success"] == should_succeed
    if not should_succeed:
        assert "error" in result
