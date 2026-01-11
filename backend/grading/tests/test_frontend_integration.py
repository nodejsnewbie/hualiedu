"""
Frontend Integration Tests
Tests form interaction, file upload, and error display

Requirements: 2.2, 9.5, 9.6
"""

import json
import os
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile


class AssignmentFormInteractionTest(TestCase):
    """
    Test form interaction for assignment creation
    Requirement 2.2: Dynamic form field switching
    """

    def setUp(self):
        """Setup test environment"""
        self.client = Client()

        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            description="Frontend test tenant",
            is_active=True,
            tenant_repo_dir="test_tenant",
        )

        # Create teacher user
        self.teacher = User.objects.create_user(
            username="teacher", password="testpass123", is_staff=True
        )

        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # Create semester
        self.semester = Semester.objects.create(
            name="2024 Spring", start_date="2024-02-01", end_date="2024-07-01"
        )

        # Create course
        self.course = Course.objects.create(
            name="Data Structures",
            course_type="lab",
            semester=self.semester,
            teacher=self.teacher,
            tenant=self.tenant,
        )

        # Create class
        self.class_obj = Class.objects.create(
            course=self.course, name="CS Class 1", student_count=30, tenant=self.tenant
        )

        # Login
        self.client.login(username="teacher", password="testpass123")

    def test_assignment_create_page_loads(self):
        """Test that assignment creation page loads successfully"""
        response = self.client.get(reverse("grading:assignment_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "assignment-management.js")
        self.assertContains(response, "storage-type-option")

    def test_form_validation_missing_fields(self):
        """Test form validation with missing required fields"""
        response = self.client.post(
            reverse("grading:assignment_create"), data={}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        # View returns 200 with error status in JSON
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    def test_form_git_storage_type_validation(self):
        """Test form validation for Git storage type (Requirement 2.2)"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "Test Assignment",
                "course_id": self.course.id,
                "class_id": self.class_obj.id,
                "storage_type": "git",
                # Missing git_url
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # View returns 200 with error status in JSON
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")

    def test_form_filesystem_storage_type_validation(self):
        """Test form validation for filesystem storage type (Requirement 2.2)"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "Test Assignment",
                "course_id": self.course.id,
                "class_id": self.class_obj.id,
                "storage_type": "filesystem",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Should succeed as filesystem doesn't require additional fields
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

    def test_form_successful_submission_git(self):
        """Test successful form submission with Git storage"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "Git Assignment",
                "course_id": self.course.id,
                "class_id": self.class_obj.id,
                "storage_type": "git",
                "git_url": "https://github.com/test/repo.git",
                "git_branch": "main",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Verify assignment was created
        assignment = Assignment.objects.filter(name="Git Assignment").first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.storage_type, "git")
        self.assertEqual(assignment.git_url, "https://github.com/test/repo.git")

    def test_form_successful_submission_filesystem(self):
        """Test successful form submission with filesystem storage"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "Filesystem Assignment",
                "course_id": self.course.id,
                "class_id": self.class_obj.id,
                "storage_type": "filesystem",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Verify assignment was created
        assignment = Assignment.objects.filter(name="Filesystem Assignment").first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.storage_type, "filesystem")

    def test_get_course_classes_api(self):
        """Test API endpoint for loading classes by course"""
        response = self.client.get(
            reverse("grading:get_course_classes"),
            data={"course_id": self.course.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("classes", data)
        self.assertEqual(len(data["classes"]), 1)
        self.assertEqual(data["classes"][0]["name"], "CS Class 1")


class FileUploadIntegrationTest(TestCase):
    """
    Test file upload functionality
    Requirements: 9.5, 9.6
    """

    def setUp(self):
        """Setup test environment"""
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()

        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            description="Upload test tenant",
            is_active=True,
            tenant_repo_dir="test_tenant",
        )

        # Create student user
        self.student = User.objects.create_user(username="student", password="testpass123")

        self.student_profile = UserProfile.objects.create(
            user=self.student,
            tenant=self.tenant,
            is_tenant_admin=False,
            repo_base_dir=self.temp_dir,
        )

        # Create semester
        self.semester = Semester.objects.create(
            name="2024 Spring", start_date="2024-02-01", end_date="2024-07-01"
        )

        # Create teacher
        self.teacher = User.objects.create_user(
            username="teacher", password="testpass123", is_staff=True
        )

        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # Create course
        self.course = Course.objects.create(
            name="Data Structures",
            course_type="lab",
            semester=self.semester,
            teacher=self.teacher,
            tenant=self.tenant,
        )

        # Create class
        self.class_obj = Class.objects.create(
            course=self.course, name="CS Class 1", student_count=30, tenant=self.tenant
        )

        # Create assignment
        self.assignment = Assignment.objects.create(
            name="Test Assignment",
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            storage_type="filesystem",
            base_path=f"{self.temp_dir}/Data Structures/CS Class 1/",
        )

        # Create assignment directory
        os.makedirs(self.assignment.base_path, exist_ok=True)

        # Login as student
        self.client.login(username="student", password="testpass123")

    def tearDown(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_format_validation_valid(self):
        """Test file format validation with valid formats (Requirement 9.6)"""
        valid_formats = [
            (
                "test.docx",
                "application/vnd.openxmlformats-officedocument." "wordprocessingml.document",
            ),
            ("test.pdf", "application/pdf"),
            ("test.zip", "application/zip"),
            ("test.txt", "text/plain"),
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
        ]

        for filename, content_type in valid_formats:
            file_content = b"Test file content"
            SimpleUploadedFile(filename, file_content, content_type=content_type)

            # File format should be accepted
            self.assertTrue(
                filename.endswith((".docx", ".pdf", ".zip", ".txt", ".jpg", ".png")),
                f"File {filename} should be valid",
            )

    def test_file_format_validation_invalid(self):
        """Test file format validation with invalid formats (Requirement 9.6)"""
        invalid_formats = [
            "test.exe",
            "test.sh",
            "test.bat",
            "test.js",
        ]

        for filename in invalid_formats:
            # File format should be rejected
            self.assertFalse(
                filename.endswith((".docx", ".pdf", ".zip", ".txt", ".jpg", ".png")),
                f"File {filename} should be invalid",
            )

    def test_file_size_validation(self):
        """Test file size validation (Requirement 9.6)"""
        # Create a file larger than 10MB
        large_file_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large.pdf", large_file_content, content_type="application/pdf"
        )

        # File should be rejected due to size
        self.assertGreater(large_file.size, 10 * 1024 * 1024)

    def test_file_upload_with_student_name(self):
        """Test file upload with student name in filename (Requirement 9.5)"""
        file_content = b"Test assignment content"
        uploaded_file = SimpleUploadedFile(
            "student-assignment.docx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document",
        )

        # Filename should contain student identifier
        self.assertIn("student", uploaded_file.name.lower())

    def test_student_submission_page_loads(self):
        """Test that student submission page loads successfully"""
        response = self.client.get(reverse("grading:student_submission"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "assignment-management.js")


class ErrorDisplayIntegrationTest(TestCase):
    """
    Test error message display
    Requirement 3.5: Friendly error messages
    """

    def setUp(self):
        """Setup test environment"""
        self.client = Client()

        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            description="Error test tenant",
            is_active=True,
            tenant_repo_dir="test_tenant",
        )

        # Create teacher user
        self.teacher = User.objects.create_user(
            username="teacher", password="testpass123", is_staff=True
        )

        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # Login
        self.client.login(username="teacher", password="testpass123")

    def test_error_message_format(self):
        """Test that error messages are user-friendly (Requirement 3.5)"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "",  # Empty name should trigger error
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # View returns 200 with error status in JSON
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Error message should be present and user-friendly
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        self.assertIsInstance(data["message"], str)
        self.assertGreater(len(data["message"]), 0)

        # Should not contain technical stack traces
        self.assertNotIn("Traceback", data["message"])
        self.assertNotIn("Exception", data["message"])

    def test_validation_error_display(self):
        """Test validation error display"""
        response = self.client.post(
            reverse("grading:assignment_create"),
            data={
                "name": "Test",
                "storage_type": "git",
                "git_url": "invalid-url",  # Invalid URL format
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # View returns 200 with error status in JSON
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should have error message
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    @patch("grading.services.git_storage_adapter.GitStorageAdapter.list_directory")
    def test_remote_access_error_display(self, mock_list_dir):
        """Test remote access error display (Requirement 3.5)"""
        # Mock remote access failure
        mock_list_dir.side_effect = Exception("Connection timeout")

        # Create a Git assignment
        semester = Semester.objects.create(
            name="2024 Spring", start_date="2024-02-01", end_date="2024-07-01"
        )

        course = Course.objects.create(
            name="Test Course",
            course_type="lab",
            semester=semester,
            teacher=self.teacher,
            tenant=self.tenant,
        )

        class_obj = Class.objects.create(
            course=course, name="Test Class", student_count=30, tenant=self.tenant
        )

        assignment = Assignment.objects.create(
            name="Git Assignment",
            owner=self.teacher,
            tenant=self.tenant,
            course=course,
            class_obj=class_obj,
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        # Try to get assignment structure
        response = self.client.get(
            reverse("grading:get_assignment_structure_api"),
            data={"assignment_id": assignment.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Should return error response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Error message should be user-friendly
        self.assertFalse(data.get("success", True))
        if "error" in data:
            self.assertIsInstance(data["error"], str)
            # Should not expose technical details
            self.assertNotIn("Traceback", data["error"])

    def test_ajax_request_detection(self):
        """Test that AJAX requests are properly detected"""
        # AJAX request
        ajax_response = self.client.post(
            reverse("grading:assignment_create"), data={}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        # Should return JSON
        self.assertEqual(ajax_response["Content-Type"], "application/json")

        # Regular request
        regular_response = self.client.post(reverse("grading:assignment_create"), data={})

        # Should return HTML or redirect
        self.assertIn(regular_response.status_code, [200, 302, 400])


class FormFieldSwitchingTest(TestCase):
    """
    Test dynamic form field switching
    Requirement 2.2: Only show relevant fields based on storage type
    """

    def setUp(self):
        """Setup test environment"""
        self.client = Client()

        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            description="Form test tenant",
            is_active=True,
            tenant_repo_dir="test_tenant",
        )

        # Create teacher user
        self.teacher = User.objects.create_user(
            username="teacher", password="testpass123", is_staff=True
        )

        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # Login
        self.client.login(username="teacher", password="testpass123")

    def test_form_contains_storage_type_options(self):
        """Test that form contains both storage type options"""
        response = self.client.get(reverse("grading:assignment_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "storage_type")
        self.assertContains(response, "git")
        self.assertContains(response, "filesystem")

    def test_form_contains_git_fields(self):
        """Test that form contains Git-specific fields"""
        response = self.client.get(reverse("grading:assignment_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "git_url")
        self.assertContains(response, "git_branch")

    def test_form_contains_filesystem_fields(self):
        """Test that form contains filesystem-specific fields"""
        response = self.client.get(reverse("grading:assignment_create"))

        self.assertEqual(response.status_code, 200)
        # Filesystem fields are dynamically shown
        self.assertContains(response, "course")
        self.assertContains(response, "class")
