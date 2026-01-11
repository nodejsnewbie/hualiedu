"""
Unit tests for Assignment Admin

Tests:
- 列表显示
- 筛选器
- 表单验证

Requirements: 5.1, 5.2, 7.4
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from grading.admin import AssignmentAdmin, AssignmentForm
from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile


class MockRequest:
    """Mock request object for admin tests"""

    def __init__(self, user):
        self.user = user


class AssignmentAdminTest(TestCase):
    """Test Assignment Admin"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant", is_active=True)

        # Create users
        self.teacher1 = User.objects.create_user(username="teacher1", password="pass123")
        self.teacher2 = User.objects.create_user(username="teacher2", password="pass123")
        self.superuser = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )

        # Create user profiles
        self.teacher1_profile = UserProfile.objects.create(user=self.teacher1, tenant=self.tenant)
        self.teacher2_profile = UserProfile.objects.create(user=self.teacher2, tenant=self.tenant)

        # Create semester
        self.semester = Semester.objects.create(
            name="2024春季学期", start_date="2024-02-01", end_date="2024-06-30"
        )

        # Create courses
        self.course1 = Course.objects.create(
            name="数据结构", semester=self.semester, teacher=self.teacher1
        )
        self.course2 = Course.objects.create(
            name="算法设计", semester=self.semester, teacher=self.teacher2
        )

        # Create classes
        self.class1 = Class.objects.create(name="计算机1班", course=self.course1)
        self.class2 = Class.objects.create(name="计算机2班", course=self.course2)

        # Create assignments
        self.assignment1 = Assignment.objects.create(
            owner=self.teacher1,
            tenant=self.tenant,
            course=self.course1,
            class_obj=self.class1,
            name="第一次作业",
            storage_type="filesystem",
            base_path="数据结构/计算机1班/",
            is_active=True,
        )

        self.assignment2 = Assignment.objects.create(
            owner=self.teacher2,
            tenant=self.tenant,
            course=self.course2,
            class_obj=self.class2,
            name="第一次作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            is_active=True,
        )

        # Create admin site and admin instance
        self.site = AdminSite()
        self.admin = AssignmentAdmin(Assignment, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test list_display fields are correct"""
        expected_fields = (
            "name",
            "course",
            "class_obj",
            "storage_type",
            "owner",
            "is_active",
            "created_at",
        )
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter(self):
        """Test list_filter fields are correct"""
        expected_filters = (
            "storage_type",
            "is_active",
            "course",
            "class_obj",
            "created_at",
        )
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields are correct"""
        expected_fields = (
            "name",
            "description",
            "course__name",
            "class_obj__name",
            "owner__username",
        )
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_teacher_queryset_isolation(self):
        """Test that teachers only see their own assignments (Requirement 5.1)"""
        # Create mock request for teacher1
        request = MockRequest(self.teacher1)

        # Get queryset
        queryset = self.admin.get_queryset(request)

        # Should only see assignment1
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.assignment1)

    def test_superuser_sees_all_assignments(self):
        """Test that superuser sees all assignments"""
        # Create mock request for superuser
        request = MockRequest(self.superuser)

        # Get queryset
        queryset = self.admin.get_queryset(request)

        # Should see all assignments
        self.assertEqual(queryset.count(), 2)

    def test_course_filter(self):
        """Test filtering by course (Requirement 7.4)"""
        # Create mock request
        request = MockRequest(self.superuser)

        # Get all assignments
        queryset = self.admin.get_queryset(request)

        # Filter by course1
        filtered = queryset.filter(course=self.course1)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.assignment1)

    def test_class_filter(self):
        """Test filtering by class (Requirement 7.4)"""
        # Create mock request
        request = MockRequest(self.superuser)

        # Get all assignments
        queryset = self.admin.get_queryset(request)

        # Filter by class1
        filtered = queryset.filter(class_obj=self.class1)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.assignment1)

    def test_storage_type_filter(self):
        """Test filtering by storage_type (Requirement 5.2)"""
        # Create mock request
        request = MockRequest(self.superuser)

        # Get all assignments
        queryset = self.admin.get_queryset(request)

        # Filter by filesystem
        filtered = queryset.filter(storage_type="filesystem")
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.assignment1)

        # Filter by git
        filtered = queryset.filter(storage_type="git")
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.assignment2)

    def test_has_change_permission_owner(self):
        """Test that owner can change their assignment"""
        request = MockRequest(self.teacher1)
        self.assertTrue(self.admin.has_change_permission(request, self.assignment1))

    def test_has_change_permission_non_owner(self):
        """Test that non-owner cannot change assignment"""
        request = MockRequest(self.teacher2)
        self.assertFalse(self.admin.has_change_permission(request, self.assignment1))

    def test_has_change_permission_superuser(self):
        """Test that superuser can change any assignment"""
        request = MockRequest(self.superuser)
        self.assertTrue(self.admin.has_change_permission(request, self.assignment1))

    def test_has_delete_permission_owner(self):
        """Test that owner can delete their assignment"""
        request = MockRequest(self.teacher1)
        self.assertTrue(self.admin.has_delete_permission(request, self.assignment1))

    def test_has_delete_permission_non_owner(self):
        """Test that non-owner cannot delete assignment"""
        request = MockRequest(self.teacher2)
        self.assertFalse(self.admin.has_delete_permission(request, self.assignment1))

    def test_save_model_sets_owner_and_tenant(self):
        """Test that save_model sets owner and tenant for new assignments"""
        # Create a new assignment without owner/tenant
        new_assignment = Assignment(
            course=self.course1,
            class_obj=self.class1,
            name="新作业",
            storage_type="filesystem",
        )

        # Create mock request
        request = MockRequest(self.teacher1)
        request.user.profile = self.teacher1_profile

        # Save through admin
        self.admin.save_model(request, new_assignment, None, change=False)

        # Check owner and tenant are set
        self.assertEqual(new_assignment.owner, self.teacher1)
        self.assertEqual(new_assignment.tenant, self.tenant)


class AssignmentFormTest(TestCase):
    """Test Assignment Form"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant", is_active=True)

        # Create user
        self.teacher = User.objects.create_user(username="teacher", password="pass123")
        self.teacher_profile = UserProfile.objects.create(user=self.teacher, tenant=self.tenant)

        # Create semester
        self.semester = Semester.objects.create(
            name="2024春季学期", start_date="2024-02-01", end_date="2024-06-30"
        )

        # Create course
        self.course = Course.objects.create(
            name="数据结构", semester=self.semester, teacher=self.teacher
        )

        # Create class
        self.class_obj = Class.objects.create(name="计算机1班", course=self.course)

    def test_form_git_storage_requires_url(self):
        """Test that Git storage type requires git_url"""
        form_data = {
            "name": "测试作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_branch": "main",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertFalse(form.is_valid())
        self.assertIn("Git仓库方式必须提供仓库URL", str(form.errors))

    def test_form_class_must_belong_to_course(self):
        """Test that class must belong to the selected course"""
        # Create another course
        other_course = Course.objects.create(
            name="算法设计", semester=self.semester, teacher=self.teacher
        )

        form_data = {
            "name": "测试作业",
            "course": other_course.id,
            "class_obj": self.class_obj.id,  # This class belongs to self.course
            "storage_type": "filesystem",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertFalse(form.is_valid())
        self.assertIn("不属于课程", str(form.errors))

    def test_form_duplicate_assignment_validation(self):
        """Test that duplicate assignments are rejected"""
        # Create an existing assignment
        existing = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
            is_active=True,
        )

        # Try to create another with the same name
        form_data = {
            "name": "第一次作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "filesystem",
            "is_active": True,
        }

        # Create a new instance with owner set
        new_instance = Assignment(owner=self.teacher, tenant=self.tenant)
        form = AssignmentForm(data=form_data, instance=new_instance)

        self.assertFalse(form.is_valid())
        self.assertIn("已存在", str(form.errors))

    def test_form_filesystem_generates_base_path(self):
        """Test that filesystem storage generates base_path automatically"""
        form_data = {
            "name": "测试作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "filesystem",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertTrue(form.is_valid())
        assignment = form.save()

        # Check base_path is generated
        self.assertIsNotNone(assignment.base_path)
        self.assertIn(self.course.name, assignment.base_path)
        self.assertIn(self.class_obj.name, assignment.base_path)

    def test_form_valid_git_assignment(self):
        """Test creating a valid Git assignment"""
        form_data = {
            "name": "Git作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_url": "https://github.com/test/repo.git",
            "git_branch": "main",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertTrue(form.is_valid())
        assignment = form.save()

        self.assertEqual(assignment.storage_type, "git")
        self.assertEqual(assignment.git_url, "https://github.com/test/repo.git")
        self.assertEqual(assignment.git_branch, "main")

    def test_form_valid_filesystem_assignment(self):
        """Test creating a valid filesystem assignment"""
        form_data = {
            "name": "文件作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "filesystem",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertTrue(form.is_valid())
        assignment = form.save()

        self.assertEqual(assignment.storage_type, "filesystem")
        self.assertIsNotNone(assignment.base_path)

    def test_form_password_encryption(self):
        """Test that Git password is encrypted when saved (Requirement 10.7)"""
        from grading.assignment_utils import CredentialEncryption

        form_data = {
            "name": "Git作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_url": "https://github.com/test/repo.git",
            "git_branch": "main",
            "git_username": "testuser",
            "git_password": "mypassword123",
            "is_active": True,
        }

        form = AssignmentForm(data=form_data)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertTrue(form.is_valid())
        assignment = form.save()

        # Check that password is encrypted
        self.assertIsNotNone(assignment.git_password_encrypted)
        self.assertNotEqual(assignment.git_password_encrypted, "mypassword123")

        # Check that we can decrypt it back
        decrypted = CredentialEncryption.decrypt(assignment.git_password_encrypted)
        self.assertEqual(decrypted, "mypassword123")

    def test_form_password_not_changed_when_empty(self):
        """Test that password is not changed when field is left empty"""
        from grading.assignment_utils import CredentialEncryption

        # Create an assignment with encrypted password
        original_password = "original_password"
        encrypted_password = CredentialEncryption.encrypt(original_password)

        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            git_password_encrypted=encrypted_password,
            is_active=True,
        )

        # Update the assignment without providing a new password
        form_data = {
            "name": "Git作业（更新）",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_url": "https://github.com/test/repo.git",
            "git_branch": "main",
            "git_password": "",  # Empty password
            "is_active": True,
        }

        form = AssignmentForm(data=form_data, instance=assignment)
        self.assertTrue(form.is_valid())
        updated_assignment = form.save()

        # Password should remain unchanged
        self.assertEqual(updated_assignment.git_password_encrypted, encrypted_password)

        # Verify we can still decrypt the original password
        decrypted = CredentialEncryption.decrypt(updated_assignment.git_password_encrypted)
        self.assertEqual(decrypted, original_password)

    def test_form_password_updated_when_provided(self):
        """Test that password is updated when a new one is provided"""
        from grading.assignment_utils import CredentialEncryption

        # Create an assignment with encrypted password
        original_password = "original_password"
        encrypted_password = CredentialEncryption.encrypt(original_password)

        assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            git_password_encrypted=encrypted_password,
            is_active=True,
        )

        # Update with a new password
        new_password = "new_password_123"
        form_data = {
            "name": "Git作业（更新）",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_url": "https://github.com/test/repo.git",
            "git_branch": "main",
            "git_password": new_password,
            "is_active": True,
        }

        form = AssignmentForm(data=form_data, instance=assignment)
        self.assertTrue(form.is_valid())
        updated_assignment = form.save()

        # Password should be changed
        self.assertNotEqual(updated_assignment.git_password_encrypted, encrypted_password)

        # Verify we can decrypt the new password
        decrypted = CredentialEncryption.decrypt(updated_assignment.git_password_encrypted)
        self.assertEqual(decrypted, new_password)

    def test_form_dynamic_field_requirements(self):
        """Test that required fields change based on storage_type (Requirement 2.2)"""
        # Test Git storage type
        form_data_git = {
            "name": "Git作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "git",
            "git_branch": "main",
            "is_active": True,
            # Missing git_url - should fail
        }

        form = AssignmentForm(data=form_data_git)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertFalse(form.is_valid())

        # Test filesystem storage type - should not require git_url
        form_data_fs = {
            "name": "文件作业",
            "course": self.course.id,
            "class_obj": self.class_obj.id,
            "storage_type": "filesystem",
            "is_active": True,
            # No git_url - should pass
        }

        form = AssignmentForm(data=form_data_fs)
        form.instance.owner = self.teacher
        form.instance.tenant = self.tenant

        self.assertTrue(form.is_valid())
