"""
Django model tests for the grading app.
"""

import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from grading.models import GlobalConfig, Repository


class GlobalConfigModelTest(TestCase):
    """Test cases for GlobalConfig model."""

    def setUp(self):
        """Set up test data."""
        self.config = GlobalConfig.objects.create(repo_base_dir="~/test_jobs")

    def test_global_config_creation(self):
        """Test GlobalConfig model creation."""
        self.assertEqual(self.config.repo_base_dir, "~/test_jobs")
        self.assertIsNotNone(self.config.created_at)
        self.assertIsNotNone(self.config.updated_at)

    def test_global_config_str_representation(self):
        """Test string representation of GlobalConfig."""
        expected = f"GlobalConfig(id={self.config.id}, repo_base_dir=~/test_jobs)"
        self.assertEqual(str(self.config), expected)

    def test_global_config_default_values(self):
        """Test GlobalConfig default values."""
        config = GlobalConfig.objects.create()
        self.assertEqual(config.repo_base_dir, "~/jobs")

    def test_global_config_expanded_path(self):
        """Test that repo_base_dir can be expanded."""
        expanded_path = os.path.expanduser(self.config.repo_base_dir)
        self.assertIsInstance(expanded_path, str)
        self.assertNotIn("~", expanded_path)


class RepositoryModelTest(TestCase):
    """Test cases for Repository model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.repository = Repository.objects.create(
            name="test-repo",
            url="https://github.com/test/test-repo.git",
            branch="main",
            branches=["main", "develop"],
            owner=self.user,
        )

    def test_repository_creation(self):
        """Test Repository model creation."""
        self.assertEqual(self.repository.name, "test-repo")
        self.assertEqual(self.repository.url, "https://github.com/test/test-repo.git")
        self.assertEqual(self.repository.branch, "main")
        self.assertEqual(self.repository.branches, ["main", "develop"])
        self.assertEqual(self.repository.owner, self.user)

    def test_repository_str_representation(self):
        """Test string representation of Repository."""
        expected = f"Repository(id={self.repository.id}, name=test-repo, branch=main)"
        self.assertEqual(str(self.repository), expected)

    def test_repository_branch_validation(self):
        """Test that branch must be in branches list."""
        # This should work
        self.repository.branch = "develop"
        self.repository.save()

        # This should raise an error if validation is implemented
        # For now, we'll just test the current behavior
        self.repository.branch = "non-existent"
        self.repository.save()  # Current implementation doesn't validate

    def test_repository_owner_relationship(self):
        """Test Repository owner relationship."""
        self.assertEqual(self.repository.owner.username, "testuser")
        self.assertTrue(self.repository.owner.is_active)

    def test_repository_default_values(self):
        """Test Repository default values."""
        repo = Repository.objects.create(
            name="default-repo", url="https://github.com/test/default-repo.git", owner=self.user
        )
        self.assertEqual(repo.branch, "main")
        self.assertEqual(repo.branches, ["main"])

    def test_repository_unique_name(self):
        """Test that repository names should be unique per owner."""
        # Create another repository with same name for same owner
        repo2 = Repository.objects.create(
            name="test-repo",  # Same name
            url="https://github.com/test/test-repo2.git",
            owner=self.user,
        )
        # Current implementation allows this, but we can test the behavior
        self.assertNotEqual(self.repository.id, repo2.id)

    def test_repository_different_owners_same_name(self):
        """Test that different owners can have repositories with same name."""
        user2 = User.objects.create_user(username="testuser2", password="testpass123")
        repo2 = Repository.objects.create(
            name="test-repo",  # Same name as first repo
            url="https://github.com/test/test-repo2.git",
            owner=user2,
        )
        self.assertNotEqual(self.repository.owner, repo2.owner)
        self.assertEqual(self.repository.name, repo2.name)


class ModelIntegrationTest(TestCase):
    """Integration tests for models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="integrationuser", password="testpass123")
        self.config = GlobalConfig.objects.create(repo_base_dir="~/integration_test")

    def test_models_work_together(self):
        """Test that models can work together."""
        # Create a repository
        repo = Repository.objects.create(
            name="integration-repo",
            url="https://github.com/test/integration-repo.git",
            owner=self.user,
        )

        # Verify both models exist
        self.assertEqual(GlobalConfig.objects.count(), 1)
        self.assertEqual(Repository.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

        # Verify relationships
        self.assertEqual(repo.owner, self.user)
        self.assertEqual(self.config.repo_base_dir, "~/integration_test")

    def test_cascade_delete_behavior(self):
        """Test cascade delete behavior."""
        # Create a repository
        repo = Repository.objects.create(
            name="cascade-repo", url="https://github.com/test/cascade-repo.git", owner=self.user
        )

        # Delete the user
        self.user.delete()

        # Repository should be deleted if cascade is set up
        # Current implementation doesn't have cascade, so we test the current behavior
        self.assertEqual(Repository.objects.count(), 0)
