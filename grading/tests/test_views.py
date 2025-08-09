"""
Django view tests for the grading app.
"""

import json
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from grading.models import GlobalConfig


class GradingViewsTest(TestCase):
    """Test cases for grading views."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )

        # Create test client
        self.client = Client()

        # Create GlobalConfig
        self.config = GlobalConfig.objects.create(repo_base_dir="~/test_jobs")

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_document.docx")

        # Create a simple test file
        with open(self.test_file_path, "w") as f:
            f.write("Test document content")

    def tearDown(self):
        """Clean up test data."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_index_view(self):
        """Test index view."""
        response = self.client.get(reverse("grading:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_grading_page_view_authenticated(self):
        """Test grading page view for authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("grading:grading"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grading.html")

    def test_grading_page_view_unauthenticated(self):
        """Test grading page view for unauthenticated user."""
        response = self.client.get(reverse("grading:grading"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_grading_page_view_non_staff(self):
        """Test grading page view for non-staff user."""
        # Create non-staff user
        non_staff_user = User.objects.create_user(
            username="nonstaff", password="testpass123", is_staff=False
        )
        self.client.login(username="nonstaff", password="testpass123")
        response = self.client.get(reverse("grading:grading"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_grading_simple_view(self):
        """Test grading simple view."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("grading:grading_simple"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grading_simple.html")

    def test_get_directory_tree_view(self):
        """Test get directory tree view."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("grading:get_directory_tree"))
        self.assertEqual(response.status_code, 200)
        # Response should be JSON
        self.assertEqual(response["Content-Type"], "application/json")

    def test_get_file_content_view(self):
        """Test get file content view."""
        self.client.login(username="testuser", password="testpass123")

        # Test with valid file path
        data = {"path": "test_document.docx"}
        response = self.client.post(reverse("grading:get_file_content"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_add_grade_to_file_view(self):
        """Test add grade to file view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_document.docx", "grade": "A"}
        response = self.client.post(reverse("grading:add_grade_to_file"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_save_grade_view(self):
        """Test save grade view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_document.docx", "grade": "B"}
        response = self.client.post(reverse("grading:save_grade"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_remove_grade_view(self):
        """Test remove grade view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_document.docx"}
        response = self.client.post(reverse("grading:remove_grade"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_save_teacher_comment_view(self):
        """Test save teacher comment view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"file_path": "test_document.docx", "comment": "Excellent work!"}
        response = self.client.post(reverse("grading:save_teacher_comment"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_get_teacher_comment_view(self):
        """Test get teacher comment view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"file_path": "test_document.docx"}
        response = self.client.get(reverse("grading:get_teacher_comment"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_ai_score_view(self):
        """Test AI score view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_document.docx"}
        response = self.client.post(reverse("grading:ai_score"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_batch_ai_score_view(self):
        """Test batch AI score view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_directory"}
        response = self.client.post(reverse("grading:batch_ai_score"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_batch_grade_page_view(self):
        """Test batch grade page view."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("grading:batch_grade_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "batch_grade.html")

    def test_get_template_list_view(self):
        """Test get template list view."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("grading:get_template_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_get_dir_file_count_view(self):
        """Test get directory file count view."""
        self.client.login(username="testuser", password="testpass123")

        data = {"path": "test_directory"}
        response = self.client.post(reverse("grading:get_dir_file_count"), data)
        self.assertEqual(response.status_code, 200)


class GradingViewsAuthenticationTest(TestCase):
    """Test authentication requirements for grading views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )

    def test_views_require_authentication(self):
        """Test that views require authentication."""
        views_to_test = [
            "grading:grading",
            "grading:grading_simple",
            "grading:get_directory_tree",
            "grading:add_grade_to_file",
            "grading:save_grade",
            "grading:remove_grade",
            "grading:save_teacher_comment",
            "grading:get_teacher_comment",
            "grading:ai_score",
            "grading:batch_ai_score",
            "grading:batch_grade_page",
            "grading:get_template_list",
        ]

        for view_name in views_to_test:
            if "get" in view_name:
                response = self.client.get(reverse(view_name))
            else:
                response = self.client.post(reverse(view_name), {})

            # Should redirect to login (302) or return forbidden (403)
            self.assertIn(response.status_code, [302, 403])

    def test_views_require_staff_permission(self):
        """Test that views require staff permission."""
        # Create non-staff user
        non_staff_user = User.objects.create_user(
            username="nonstaff", password="testpass123", is_staff=False
        )
        self.client.login(username="nonstaff", password="testpass123")

        views_to_test = [
            "grading:grading",
            "grading:grading_simple",
            "grading:get_directory_tree",
            "grading:add_grade_to_file",
            "grading:save_grade",
            "grading:remove_grade",
            "grading:save_teacher_comment",
            "grading:get_teacher_comment",
            "grading:ai_score",
            "grading:batch_ai_score",
            "grading:batch_grade_page",
            "grading:get_template_list",
        ]

        for view_name in views_to_test:
            if "get" in view_name:
                response = self.client.get(reverse(view_name))
            else:
                response = self.client.post(reverse(view_name), {})

            # Should return forbidden (403)
            self.assertEqual(response.status_code, 403)


class GradingViewsErrorHandlingTest(TestCase):
    """Test error handling in grading views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )
        self.client.login(username="testuser", password="testpass123")

    def test_get_file_content_invalid_path(self):
        """Test get file content with invalid path."""
        data = {"path": "nonexistent_file.docx"}
        response = self.client.post(reverse("grading:get_file_content"), data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "error")

    def test_add_grade_to_file_missing_data(self):
        """Test add grade to file with missing data."""
        data = {}  # Missing required fields
        response = self.client.post(reverse("grading:add_grade_to_file"), data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "error")

    def test_save_grade_missing_data(self):
        """Test save grade with missing data."""
        data = {}  # Missing required fields
        response = self.client.post(reverse("grading:save_grade"), data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "error")

    def test_ai_score_missing_data(self):
        """Test AI score with missing data."""
        data = {}  # Missing required fields
        response = self.client.post(reverse("grading:ai_score"), data)
        self.assertEqual(response.status_code, 400)
