"""
Assignment 模型单元测试

测试 Assignment 模型的字段验证、模型方法和约束
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from grading.models import Assignment, Class, Course, Semester, Tenant


class AssignmentModelTest(TestCase):
    """Assignment 模型测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户", description="测试用租户")

        # 创建用户
        self.user = User.objects.create_user(username="testteacher", password="testpass123")

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date="2024-03-01", end_date="2024-07-15"
        )

        # 创建课程
        self.course = Course.objects.create(
            semester=self.semester, teacher=self.user, name="数据结构", tenant=self.tenant
        )

        # 创建班级
        self.class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
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
            base_path="/data/courses/数据结构/计算机1班/",
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
            git_username="testuser",
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
            git_url="https://github.com/test/repo.git",
        )

        fs_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="/data/test/",
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
            base_path="/data/test/",
        )

        git_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
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
            git_url="https://github.com/test/repo.git",
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
            base_path="/data/courses/数据结构/计算机1班/",
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
            git_password_encrypted="encrypted_password",
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
            base_path="/data/test/",
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
            storage_type="filesystem",
        )

        # 尝试创建重复的作业配置
        with self.assertRaises(Exception):
            Assignment.objects.create(
                owner=self.user,
                tenant=self.tenant,
                course=self.course,
                class_obj=self.class_obj,
                name="第一次作业",
                storage_type="filesystem",
            )

    def test_str_method(self):
        """测试 __str__ 方法"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
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
            storage_type="filesystem",
        )

        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.storage_type, "filesystem")
        self.assertEqual(assignment.git_branch, "main")
        self.assertIsNotNone(assignment.created_at)
        self.assertIsNotNone(assignment.updated_at)

    def test_validate_git_config_missing_url(self):
        """测试 Git 配置验证 - 缺少 URL"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_branch="main",
        )

        with self.assertRaises(ValueError) as context:
            assignment.validate_git_config()

        self.assertIn("Git存储方式必须提供仓库URL", str(context.exception))

    def test_validate_git_config_default_branch(self):
        """测试 Git 配置验证 - 默认分支"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="",
        )

        assignment.validate_git_config()
        self.assertEqual(assignment.git_branch, "main")

    def test_validate_git_config_success(self):
        """测试 Git 配置验证 - 成功"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="develop",
        )

        # 不应该抛出异常
        assignment.validate_git_config()
        self.assertEqual(assignment.git_branch, "develop")

    def test_validate_filesystem_config_auto_generate_path(self):
        """测试文件系统配置验证 - 自动生成路径"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="",
        )

        assignment.validate_filesystem_config()
        expected_path = f"{self.course.name}/{self.class_obj.name}/"
        self.assertEqual(assignment.base_path, expected_path)

    def test_validate_filesystem_config_keep_existing_path(self):
        """测试文件系统配置验证 - 保留现有路径"""
        custom_path = "/custom/path/to/assignments/"
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path=custom_path,
        )

        assignment.validate_filesystem_config()
        self.assertEqual(assignment.base_path, custom_path)

    def test_clean_method_git_validation(self):
        """测试 clean 方法 - Git 配置验证"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
        )

        with self.assertRaises(ValidationError) as context:
            assignment.clean()

        self.assertIn("Git存储方式必须提供仓库URL", str(context.exception))

    def test_clean_method_filesystem_validation(self):
        """测试 clean 方法 - 文件系统配置验证"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="",
        )

        # clean 应该自动生成路径，不抛出异常
        assignment.clean()
        expected_path = f"{self.course.name}/{self.class_obj.name}/"
        self.assertEqual(assignment.base_path, expected_path)

    def test_save_calls_full_clean(self):
        """测试 save 方法调用 full_clean"""
        assignment = Assignment(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
        )

        # save 应该调用 full_clean，从而触发验证
        with self.assertRaises(ValidationError):
            assignment.save()

    def test_course_class_relationship(self):
        """测试课程和班级关系 (Requirements 7.1, 7.2)"""
        # 创建另一个课程
        other_course = Course.objects.create(
            semester=self.semester, teacher=self.user, name="算法设计", tenant=self.tenant
        )

        # 创建属于不同课程的班级
        other_class = Class.objects.create(
            tenant=self.tenant, course=other_course, name="计算机2班", student_count=25
        )

        # 创建作业配置
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 验证关联正确
        self.assertEqual(assignment.course, self.course)
        self.assertEqual(assignment.class_obj, self.class_obj)
        self.assertEqual(assignment.class_obj.course, self.course)

    def test_multiple_assignments_same_course_different_classes(self):
        """测试同一课程的不同班级可以有独立的作业配置 (Requirement 7.3)"""
        # 创建第二个班级
        class2 = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机2班", student_count=28
        )

        # 为两个班级创建同名作业
        assignment1 = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        assignment2 = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=class2,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 两个作业应该是不同的对象
        self.assertNotEqual(assignment1.id, assignment2.id)
        self.assertEqual(assignment1.name, assignment2.name)
        self.assertNotEqual(assignment1.class_obj, assignment2.class_obj)

    def test_assignment_ordering(self):
        """测试作业配置的排序"""
        # 创建多个作业
        assignment1 = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        assignment2 = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第二次作业",
            storage_type="filesystem",
        )

        # 获取所有作业
        assignments = Assignment.objects.all()

        # 应该按创建时间倒序排列（最新的在前）
        self.assertEqual(assignments[0].id, assignment2.id)
        self.assertEqual(assignments[1].id, assignment1.id)

    def test_assignment_indexes(self):
        """测试数据库索引是否正确创建"""
        # 这个测试主要验证模型定义中的索引配置
        # 实际的索引创建由 Django 迁移处理
        from django.db import connection

        # 获取表的索引信息
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='grading_assignment'"
            )
            table_exists = cursor.fetchone()

            if table_exists:
                # 获取索引信息
                cursor.execute("PRAGMA index_list('grading_assignment')")
                indexes = cursor.fetchall()

                # 至少应该有一些索引
                self.assertGreater(len(indexes), 0)

    def test_is_active_filter(self):
        """测试 is_active 字段的过滤"""
        # 创建激活的作业
        active_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="激活作业",
            storage_type="filesystem",
            is_active=True,
        )

        # 创建未激活的作业
        inactive_assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="未激活作业",
            storage_type="filesystem",
            is_active=False,
        )

        # 过滤激活的作业
        active_assignments = Assignment.objects.filter(is_active=True)
        self.assertIn(active_assignment, active_assignments)
        self.assertNotIn(inactive_assignment, active_assignments)

    def test_tenant_isolation(self):
        """测试租户隔离 (Requirement 2.1)"""
        # 创建另一个租户
        other_tenant = Tenant.objects.create(name="其他租户", description="另一个测试租户")

        # 创建另一个用户
        other_user = User.objects.create_user(username="otherteacher", password="testpass123")

        # 创建另一个学期
        other_semester = Semester.objects.create(
            name="2024年秋季学期", start_date="2024-09-01", end_date="2025-01-15"
        )

        # 创建另一个课程
        other_course = Course.objects.create(
            semester=other_semester, teacher=other_user, name="数据结构", tenant=other_tenant
        )

        # 创建另一个班级
        other_class = Class.objects.create(
            tenant=other_tenant, course=other_course, name="计算机1班", student_count=30
        )

        # 为第一个租户创建作业
        assignment1 = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 为第二个租户创建作业
        assignment2 = Assignment.objects.create(
            owner=other_user,
            tenant=other_tenant,
            course=other_course,
            class_obj=other_class,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 按租户过滤
        tenant1_assignments = Assignment.objects.filter(tenant=self.tenant)
        tenant2_assignments = Assignment.objects.filter(tenant=other_tenant)

        self.assertIn(assignment1, tenant1_assignments)
        self.assertNotIn(assignment2, tenant1_assignments)
        self.assertIn(assignment2, tenant2_assignments)
        self.assertNotIn(assignment1, tenant2_assignments)

    def test_get_display_path_filesystem_empty(self):
        """测试文件系统类型的显示路径 - 空路径"""
        assignment = Assignment.objects.create(
            owner=self.user,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="文件作业",
            storage_type="filesystem",
            base_path="",
        )

        # 应该返回默认格式
        expected = f"{self.course.name}/{self.class_obj.name}/"
        self.assertEqual(assignment.get_display_path(), expected)
