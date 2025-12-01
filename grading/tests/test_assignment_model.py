"""
Assignment 模型单元测试

测试 Assignment 模型的字段验证、模型方法和约束
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from grading.models import Assignment, Tenant, Course, Class, Semester


class AssignmentModelTest(TestCase):
    """Assignment 模型测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant = Tenant.objects.create(
            name="测试租户",
            description="测试用租户"
        )

        # 创建用户
        self.user = User.objects.create_user(
            username="testteacher",
            password="testpass123"
        )

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date="2024-03-01",
            end_date="2024-07-15"
        )

        # 创建课程
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.user,
            name="数据结构",
            tenant=self.tenant
        )

        # 创建班级
        self.class_obj = Class.objects.create(
            tenant=self.tenant,
            course=self.course,
            name="计算机1班",
            student_count=30
        )

    def test_create_filesystem_assignment(self):
        """测试创建文件系统类型的作业配置"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            description="数据结构第一次作业",
            storage_type="filesystem",
            base_path="/data/courses/数据结构/计算机1班/"
        )

        self.assertEqual(assignment.owner, self.user)
        self.assertEqual(assignment.tenant, self.tenant)
        self.assertEqual(assignment.course, self.course)
        self.assertEqual(assignment.class_obj, self.class_obj)
        self.assertEqual(assignment.name, "第一次作业")
        self.assertEqual(assignment.storage_type, "filesystem")
        self.assertTrue(assignment.is_active)

    def test_create_git_assignment(self):
        """测试创建Git类型的作业配置"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="算法作业",
            description="算法课程作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            git_username="testuser"
        )

        self.assertEqual(assignment.storage_type, "git")
        self.assertEqual(assignment.git_url, "https://github.com/test/repo.git")
        self.assertEqual(assignment.git_branch, "main")
        self.assertTrue(assignment.is_git_storage())

    def test_is_git_storage(self):
        """测试 is_git_storage 方法"""
        git_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git"
        )

        fs_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="/data/test/"
        )

        self.assertTrue(git_assignment.is_git_storage())
        self.assertFalse(fs_assignment.is_git_storage())

    def test_is_filesystem_storage(self):
        """测试 is_filesystem_storage 方法"""
        fs_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="/data/test/"
        )

        git_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git"
        )

        self.assertTrue(fs_assignment.is_filesystem_storage())
        self.assertFalse(git_assignment.is_filesystem_storage())

    def test_get_display_path_git(self):
        """测试 Git 类型的显示路径"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git"
        )

        self.assertEqual(assignment.get_display_path(), "https://github.com/test/repo.git")

    def test_get_display_path_filesystem(self):
        """测试文件系统类型的显示路径"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="/data/courses/数据结构/计算机1班/"
        )

        self.assertEqual(assignment.get_display_path(), "/data/courses/数据结构/计算机1班/")

    def test_get_storage_config_git(self):
        """测试获取 Git 存储配置"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="develop",
            git_username="testuser",
            git_password_encrypted="encrypted_password"
        )

        config = assignment.get_storage_config()
        self.assertEqual(config["type"], "git")
        self.assertEqual(config["url"], "https://github.com/test/repo.git")
        self.assertEqual(config["branch"], "develop")
        self.assertEqual(config["username"], "testuser")

    def test_get_storage_config_filesystem(self):
        """测试获取文件系统存储配置"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="/data/test/"
        )

        config = assignment.get_storage_config()
        self.assertEqual(config["type"], "filesystem")
        self.assertEqual(config["base_path"], "/data/test/")

    def test_unique_together_constraint(self):
        """测试唯一性约束"""
        Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem"
        )

        # 尝试创建重复的作业配置
        with self.assertRaises(Exception):
            Assignment.objects.create(
                owner=self.user,
                tenant=self.tenant,
                course=self.course,
                class_obj=self.class_obj,
                name="第一次作业",
                storage_type="filesystem"
            )

    def test_str_method(self):
        """测试 __str__ 方法"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem"
        )

        expected = f"{self.course.name} - {self.class_obj.name} - 第一次作业"
        self.assertEqual(str(assignment), expected)

    def test_default_values(self):
        """测试默认值"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="测试作业",
            storage_type="filesystem"
        )

        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.storage_type, "filesystem")
        self.assertEqual(assignment.git_branch, "main")
        self.assertIsNotNone(assignment.created_at)
        self.assertIsNotNone(assignment.updated_at)
