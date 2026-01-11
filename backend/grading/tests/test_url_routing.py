"""
Tests for URL routing configuration.

This test file verifies that:
1. Assignment management URLs are properly configured
2. Deprecated repository URLs are maintained for backward compatibility
3. Sync-related URLs have been removed (Requirement 6.1)
"""

from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class AssignmentURLTests(TestCase):
    """Test assignment management URL routing."""

    def test_assignment_list_url(self):
        """Test assignment list URL resolves correctly."""
        url = reverse("grading:assignment_list")
        self.assertEqual(url, "/grading/assignments/")

    def test_assignment_create_url(self):
        """Test assignment create URL resolves correctly."""
        url = reverse("grading:assignment_create")
        self.assertEqual(url, "/grading/assignments/create/")

    def test_assignment_edit_url(self):
        """Test assignment edit URL resolves correctly."""
        url = reverse("grading:assignment_edit", args=[1])
        self.assertEqual(url, "/grading/assignments/1/edit/")

    def test_assignment_delete_url(self):
        """Test assignment delete URL resolves correctly."""
        url = reverse("grading:assignment_delete", args=[1])
        self.assertEqual(url, "/grading/assignments/1/delete/")

    def test_assignment_structure_api_url(self):
        """Test assignment structure API URL resolves correctly."""
        url = reverse("grading:get_assignment_structure_api")
        self.assertEqual(url, "/grading/api/assignments/structure/")

    def test_assignment_file_api_url(self):
        """Test assignment file API URL resolves correctly."""
        url = reverse("grading:get_assignment_file_api")
        self.assertEqual(url, "/grading/api/assignments/file/")

    def test_assignment_directories_api_url(self):
        """Test assignment directories API URL resolves correctly."""
        url = reverse("grading:get_assignment_directories_api")
        self.assertEqual(url, "/grading/api/assignments/directories/")


class StudentSubmissionURLTests(TestCase):
    """Test student submission URL routing."""

    def test_student_submission_url(self):
        """Test student submission page URL resolves correctly."""
        url = reverse("grading:student_submission")
        self.assertEqual(url, "/grading/student/submission/")

    def test_upload_assignment_file_api_url(self):
        """Test upload assignment file API URL resolves correctly."""
        url = reverse("grading:upload_assignment_file_api")
        self.assertEqual(url, "/grading/api/student/upload/")

    def test_create_assignment_directory_api_url(self):
        """Test create assignment directory API URL resolves correctly."""
        url = reverse("grading:create_assignment_directory_api")
        self.assertEqual(url, "/grading/api/student/create-directory/")


class DeprecatedRepositoryURLTests(TestCase):
    """Test deprecated repository URLs for backward compatibility."""

    def test_repository_management_url_exists(self):
        """Test repository management URL still exists for backward compatibility."""
        url = reverse("grading:repository_management")
        self.assertEqual(url, "/grading/repository-management/")

    def test_add_repository_url_exists(self):
        """Test add repository URL still exists for backward compatibility."""
        url = reverse("grading:add_repository")
        self.assertEqual(url, "/grading/add-repository/")

    def test_update_repository_url_exists(self):
        """Test update repository URL still exists for backward compatibility."""
        url = reverse("grading:update_repository")
        self.assertEqual(url, "/grading/update-repository/")

    def test_delete_repository_url_exists(self):
        """Test delete repository URL still exists for backward compatibility."""
        url = reverse("grading:delete_repository")
        self.assertEqual(url, "/grading/delete-repository/")


class RemovedSyncURLTests(TestCase):
    """Test that sync-related URLs have been removed (Requirement 6.1)."""

    def test_sync_repository_url_removed(self):
        """
        Test that sync_repository URL has been removed.

        Validates: Requirements 6.1
        The sync functionality is no longer needed with the remote-first architecture.
        """
        with self.assertRaises(NoReverseMatch):
            reverse("grading:sync_repository")
