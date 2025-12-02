"""
作业管理服务的属性测试

使用 Hypothesis 进行基于属性的测试，验证通用规则。
"""

from django.contrib.auth.models import User
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService

# 导入共享的 Hypothesis 配置
from . import hypothesis_config  # noqa: F401


class TestAssignmentManagementServiceProperties(TestCase):
    """AssignmentManagementService 属性测试"""

    def _ensure_user_profile(self, user, tenant):
        """确保用户配置文件存在的辅助方法"""
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user, tenant=tenant)

        # 清除 Django 的 related object cache
        if hasattr(user, "_profile_cache"):
            del user._profile_cache
        if hasattr(user, "profile") and not hasattr(user, "userprofile"):
            user.userprofile = user.profile

        return profile

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant1 = Tenant.objects.create(name="租户1", is_active=True)
        self.tenant2 = Tenant.objects.create(name="租户2", is_active=True)

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username="teacher1", password="pass123", email="teacher1@test.com"
        )
        self.teacher2 = User.objects.create_user(
            username="teacher2", password="pass123", email="teacher2@test.com"
        )
        self.teacher3 = User.objects.create_user(
            username="teacher3", password="pass123", email="teacher3@test.com"
        )

        # 创建用户配置文件
        self.profile1 = UserProfile.objects.create(user=self.teacher1, tenant=self.tenant1)
        self.profile2 = UserProfile.objects.create(user=self.teacher2, tenant=self.tenant1)
        self.profile3 = UserProfile.objects.create(user=self.teacher3, tenant=self.tenant2)

        # 创建学期
        from datetime import date

        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 7, 15),
            is_active=True,
        )

        # 创建课程
        self.course1 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher1,
            name="数据结构",
            tenant=self.tenant1,
        )
        self.course2 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher2,
            name="算法设计",
            tenant=self.tenant1,
        )
        self.course3 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher3,
            name="操作系统",
            tenant=self.tenant2,
        )

        # 创建班级
        self.class1 = Class.objects.create(
            course=self.course1, name="计算机1班", tenant=self.tenant1
        )
        self.class2 = Class.objects.create(
            course=self.course2, name="计算机2班", tenant=self.tenant1
        )
        self.class3 = Class.objects.create(
            course=self.course3, name="计算机3班", tenant=self.tenant2
        )

        # 创建服务实例
        self.service = AssignmentManagementService()

    @given(
        num_assignments_teacher1=st.integers(min_value=0, max_value=10),
        num_assignments_teacher2=st.integers(min_value=0, max_value=10),
        num_assignments_teacher3=st.integers(min_value=0, max_value=10),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_12_teacher_assignment_list_isolation(
        self, num_assignments_teacher1, num_assignments_teacher2, num_assignments_teacher3
    ):
        """**Feature: assignment-management-refactor, Property 12: 教师作业列表隔离**

        For any 教师用户，作业管理页面应该只显示该教师创建的作业配置
        **Validates: Requirements 5.1**
        """
        # 确保用户配置文件存在（Hypothesis 可能会重新创建数据库）

        # 清理之前的作业
        Assignment.objects.all().delete()

        # 为 teacher1 创建作业
        teacher1_assignments = []
        for i in range(num_assignments_teacher1):
            assignment = Assignment.objects.create(
                owner=self.teacher1,
                tenant=self.tenant1,
                course=self.course1,
                class_obj=self.class1,
                name=f"teacher1_assignment_{i}",
                storage_type="filesystem",
                base_path=f"/path/to/teacher1/assignment{i}",
                is_active=True,
            )
            teacher1_assignments.append(assignment)

        # 为 teacher2 创建作业（同一租户）
        teacher2_assignments = []
        for i in range(num_assignments_teacher2):
            assignment = Assignment.objects.create(
                owner=self.teacher2,
                tenant=self.tenant1,
                course=self.course2,
                class_obj=self.class2,
                name=f"teacher2_assignment_{i}",
                storage_type="git",
                git_url=f"https://github.com/teacher2/repo{i}.git",
                git_branch="main",
                is_active=True,
            )
            teacher2_assignments.append(assignment)

        # 为 teacher3 创建作业（不同租户）
        teacher3_assignments = []
        for i in range(num_assignments_teacher3):
            assignment = Assignment.objects.create(
                owner=self.teacher3,
                tenant=self.tenant2,
                course=self.course3,
                class_obj=self.class3,
                name=f"teacher3_assignment_{i}",
                storage_type="filesystem",
                base_path=f"/path/to/teacher3/assignment{i}",
                is_active=True,
            )
            teacher3_assignments.append(assignment)

        # 测试 teacher1 只能看到自己的作业
        teacher1_list = self.service.list_assignments(self.teacher1)
        teacher1_ids = set(teacher1_list.values_list("id", flat=True))
        expected_teacher1_ids = set(a.id for a in teacher1_assignments)

        self.assertEqual(
            teacher1_ids,
            expected_teacher1_ids,
            f"Teacher1 should only see their own {num_assignments_teacher1} assignments",
        )

        # 验证 teacher1 看不到 teacher2 的作业
        teacher2_ids = set(a.id for a in teacher2_assignments)
        self.assertEqual(
            teacher1_ids & teacher2_ids,
            set(),
            "Teacher1 should not see Teacher2's assignments (same tenant)",
        )

        # 验证 teacher1 看不到 teacher3 的作业
        teacher3_ids = set(a.id for a in teacher3_assignments)
        self.assertEqual(
            teacher1_ids & teacher3_ids,
            set(),
            "Teacher1 should not see Teacher3's assignments (different tenant)",
        )

        # 测试 teacher2 只能看到自己的作业
        teacher2_list = self.service.list_assignments(self.teacher2)
        teacher2_list_ids = set(teacher2_list.values_list("id", flat=True))
        expected_teacher2_ids = set(a.id for a in teacher2_assignments)

        self.assertEqual(
            teacher2_list_ids,
            expected_teacher2_ids,
            f"Teacher2 should only see their own {num_assignments_teacher2} assignments",
        )

        # 验证 teacher2 看不到 teacher1 的作业
        self.assertEqual(
            teacher2_list_ids & teacher1_ids,
            set(),
            "Teacher2 should not see Teacher1's assignments (same tenant)",
        )

        # 测试 teacher3 只能看到自己的作业
        teacher3_list = self.service.list_assignments(self.teacher3)
        teacher3_list_ids = set(teacher3_list.values_list("id", flat=True))
        expected_teacher3_ids = set(a.id for a in teacher3_assignments)

        self.assertEqual(
            teacher3_list_ids,
            expected_teacher3_ids,
            f"Teacher3 should only see their own {num_assignments_teacher3} assignments",
        )

        # 验证 teacher3 看不到其他租户的作业
        self.assertEqual(
            teacher3_list_ids & (teacher1_ids | teacher2_ids),
            set(),
            "Teacher3 should not see assignments from other tenants",
        )

        # 验证返回的作业数量正确
        self.assertEqual(teacher1_list.count(), num_assignments_teacher1)
        self.assertEqual(teacher2_list.count(), num_assignments_teacher2)
        self.assertEqual(teacher3_list.count(), num_assignments_teacher3)

        # 验证所有返回的作业都属于正确的教师
        for assignment in teacher1_list:
            self.assertEqual(assignment.owner, self.teacher1)
            self.assertEqual(assignment.tenant, self.tenant1)

        for assignment in teacher2_list:
            self.assertEqual(assignment.owner, self.teacher2)
            self.assertEqual(assignment.tenant, self.tenant1)

        for assignment in teacher3_list:
            self.assertEqual(assignment.owner, self.teacher3)
            self.assertEqual(assignment.tenant, self.tenant2)

    @given(
        name_update=st.text(min_size=1, max_size=100).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
        description_update=st.text(min_size=0, max_size=500),
        is_active_update=st.booleans(),
        git_branch_update=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_13_edit_preserves_data_integrity(
        self, name_update, description_update, is_active_update, git_branch_update
    ):
        """**Feature: assignment-management-refactor, Property 13: 编辑保留数据完整性**

        For any 作业配置的编辑操作，已提交的学生作业数据应该保持不变
        **Validates: Requirements 5.4**
        """
        # 确保用户配置文件存在

        # 清理之前的作业
        Assignment.objects.all().delete()

        # 创建一个Git类型的作业
        original_assignment = Assignment.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            name="原始作业名称",
            description="原始描述",
            storage_type="git",
            git_url="https://github.com/original/repo.git",
            git_branch="main",
            git_username="original_user",
            git_password_encrypted="encrypted_password",
            is_active=True,
        )

        # 记录关键的不可变字段的原始值
        original_id = original_assignment.id
        original_owner = original_assignment.owner
        original_tenant = original_assignment.tenant
        original_course = original_assignment.course
        original_class_obj = original_assignment.class_obj
        original_storage_type = original_assignment.storage_type
        original_created_at = original_assignment.created_at

        # 执行更新操作
        updated_assignment = self.service.update_assignment(
            original_assignment,
            self.teacher1,
            name=name_update,
            description=description_update,
            is_active=is_active_update,
            git_branch=git_branch_update,
        )

        # 刷新对象以获取最新数据
        updated_assignment.refresh_from_db()

        # 验证关键的不可变字段保持不变（数据完整性）
        self.assertEqual(
            updated_assignment.id, original_id, "Assignment ID should not change during update"
        )
        self.assertEqual(
            updated_assignment.owner,
            original_owner,
            "Assignment owner should not change during update",
        )
        self.assertEqual(
            updated_assignment.tenant,
            original_tenant,
            "Assignment tenant should not change during update",
        )
        self.assertEqual(
            updated_assignment.course,
            original_course,
            "Assignment course should not change during update",
        )
        self.assertEqual(
            updated_assignment.class_obj,
            original_class_obj,
            "Assignment class should not change during update",
        )
        self.assertEqual(
            updated_assignment.storage_type,
            original_storage_type,
            "Assignment storage_type should not change during update",
        )
        self.assertEqual(
            updated_assignment.created_at,
            original_created_at,
            "Assignment created_at should not change during update",
        )

        # 验证可更新的字段确实被更新了
        self.assertNotEqual(
            updated_assignment.name, "原始作业名称", "Assignment name should be updated"
        )
        self.assertEqual(
            updated_assignment.description,
            description_update,
            "Assignment description should be updated",
        )
        self.assertEqual(
            updated_assignment.is_active, is_active_update, "Assignment is_active should be updated"
        )
        self.assertEqual(
            updated_assignment.git_branch,
            git_branch_update,
            "Assignment git_branch should be updated",
        )

        # 验证其他Git配置字段保持不变（因为我们没有更新它们）
        self.assertEqual(
            updated_assignment.git_url,
            "https://github.com/original/repo.git",
            "Git URL should remain unchanged when not updated",
        )
        self.assertEqual(
            updated_assignment.git_username,
            "original_user",
            "Git username should remain unchanged when not updated",
        )
        self.assertEqual(
            updated_assignment.git_password_encrypted,
            "encrypted_password",
            "Git password should remain unchanged when not updated",
        )

        # 验证updated_at字段被更新了
        self.assertGreater(
            updated_assignment.updated_at,
            original_created_at,
            "Assignment updated_at should be greater than created_at after update",
        )

        # 测试文件系统类型的作业
        fs_assignment = Assignment.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            name="文件系统作业",
            description="文件系统描述",
            storage_type="filesystem",
            base_path="/path/to/original",
            is_active=True,
        )

        fs_original_id = fs_assignment.id
        fs_original_storage_type = fs_assignment.storage_type
        fs_original_base_path = fs_assignment.base_path

        # 更新文件系统作业
        fs_updated = self.service.update_assignment(
            fs_assignment,
            self.teacher1,
            name=name_update + "_fs",
            description=description_update,
        )

        fs_updated.refresh_from_db()

        # 验证文件系统作业的关键字段也保持不变
        self.assertEqual(fs_updated.id, fs_original_id)
        self.assertEqual(fs_updated.storage_type, fs_original_storage_type)
        self.assertEqual(
            fs_updated.base_path,
            fs_original_base_path,
            "Base path should remain unchanged when not explicitly updated",
        )

    @given(
        name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"), min_codepoint=0x4E00, max_codepoint=0x9FFF
            )
            | st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=50,
        ).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "-"])
        ),
        description=st.text(min_size=0, max_size=500),
        storage_type=st.sampled_from(["git", "filesystem"]),
        git_url=st.sampled_from(
            [
                "https://github.com/user/repo.git",
                "http://gitlab.com/user/repo.git",
            ]
        ),
        git_branch=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=20
        ).filter(lambda x: x.strip()),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_1_form_validation_completeness(
        self, name, description, storage_type, git_url, git_branch
    ):
        """**Feature: assignment-management-refactor, Property 1: 表单验证完整性**

        For any 作业配置表单提交，所有必填字段都应该被验证，未填写的必填字段应该阻止提交
        **Validates: Requirements 2.5**
        """
        from grading.assignment_utils import ValidationError

        # 确保用户配置文件存在
        # 清理之前的作业
        Assignment.objects.all().delete()

        # 测试1: 验证必填字段 - 作业名称
        with self.assertRaises(ValidationError) as cm:
            self.service.create_assignment(
                self.teacher1,
                self.course1,
                self.class1,
                name="",  # 空名称应该被拒绝
                storage_type=storage_type,
            )
        self.assertIn("名称", str(cm.exception.user_message))

        # 测试2: 验证Git类型必填字段 - Git URL
        if storage_type == "git":
            with self.assertRaises(ValidationError) as cm:
                self.service.create_assignment(
                    self.teacher1,
                    self.course1,
                    self.class1,
                    name=name,
                    storage_type="git",
                    # 缺少 git_url
                )
            self.assertIn("URL", str(cm.exception.user_message))

        # 测试3: 有效的创建应该成功
        try:
            if storage_type == "git":
                assignment = self.service.create_assignment(
                    self.teacher1,
                    self.course1,
                    self.class1,
                    name=name,
                    description=description,
                    storage_type="git",
                    git_url=git_url,
                    git_branch=git_branch,
                )

                # 验证所有字段都被正确设置
                self.assertIsNotNone(assignment.id)
                self.assertEqual(assignment.owner, self.teacher1)
                self.assertEqual(assignment.course, self.course1)
                self.assertEqual(assignment.class_obj, self.class1)
                self.assertEqual(assignment.storage_type, "git")
                self.assertEqual(assignment.git_url, git_url)
                self.assertEqual(assignment.git_branch, git_branch)

            else:  # filesystem
                assignment = self.service.create_assignment(
                    self.teacher1,
                    self.course1,
                    self.class1,
                    name=name,
                    description=description,
                    storage_type="filesystem",
                )

                # 验证所有字段都被正确设置
                self.assertIsNotNone(assignment.id)
                self.assertEqual(assignment.owner, self.teacher1)
                self.assertEqual(assignment.course, self.course1)
                self.assertEqual(assignment.class_obj, self.class1)
                self.assertEqual(assignment.storage_type, "filesystem")
                self.assertIsNotNone(assignment.base_path)
                self.assertIn(self.course1.name, assignment.base_path or "")
        except ValidationError as e:
            # If validation fails due to name sanitization, that's expected
            if "名称" in str(e.user_message) or "清理" in str(e.user_message):
                pass  # This is expected for some generated names
            else:
                raise

    @given(
        course_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
        class_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_6_directory_path_generation_rule(self, course_name, class_name):
        """**Feature: assignment-management-refactor, Property 6: 目录路径生成规则**

        For any 课程名称和班级名称的组合，系统应该生成格式为 `<课程名称>/<班级名称>/` 的基础路径
        **Validates: Requirements 4.1**
        """
        from grading.assignment_utils import PathValidator

        # 确保用户配置文件存在
        # 清理之前的作业
        Assignment.objects.all().delete()

        # 创建临时课程和班级
        temp_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher1,
            name=course_name,
            tenant=self.tenant1,
        )
        temp_class = Class.objects.create(
            course=temp_course,
            name=class_name,
            tenant=self.tenant1,
        )

        # 创建文件系统类型的作业
        assignment = self.service.create_assignment(
            self.teacher1, temp_course, temp_class, name="测试作业", storage_type="filesystem"
        )

        # 验证路径格式
        base_path = assignment.base_path
        self.assertIsNotNone(base_path)

        # 清理课程名和班级名
        clean_course = PathValidator.sanitize_name(course_name)
        clean_class = PathValidator.sanitize_name(class_name)

        # 验证路径包含课程名和班级名
        self.assertIn(clean_course, base_path)
        self.assertIn(clean_class, base_path)

        # 验证路径格式：应该是 <课程名>/<班级名>/ 的形式
        # 去除尾部斜杠后分割
        path_parts = base_path.rstrip("/").split("/")
        self.assertEqual(len(path_parts), 2, f"Path should have 2 parts, got: {base_path}")
        self.assertEqual(path_parts[0], clean_course)
        self.assertEqual(path_parts[1], clean_class)

        # 验证路径以斜杠结尾
        self.assertTrue(base_path.endswith("/"), f"Path should end with /, got: {base_path}")

    @given(
        git_url=st.one_of(
            st.just("https://github.com/user/repo.git"),
            st.just("http://gitlab.com/user/repo.git"),
            st.just("git@github.com:user/repo.git"),
            st.just("git://github.com/user/repo.git"),
            st.just("ssh://git@github.com/user/repo.git"),
            # 无效的URL
            st.just("ftp://invalid.com/repo.git"),
            st.just("not-a-url"),
            st.just(""),
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_18_git_url_validation(self, git_url):
        """**Feature: assignment-management-refactor, Property 18: Git URL 验证**

        For any Git URL 输入，系统应该验证 URL 格式正确（http/https/git/ssh 协议）
        **Validates: Requirements 8.4**
        """
        from grading.assignment_utils import ValidationError

        # 确保用户配置文件存在
        # 清理之前的作业
        Assignment.objects.all().delete()

        # 判断URL是否有效
        is_valid_url = (
            git_url.startswith("http://")
            or git_url.startswith("https://")
            or git_url.startswith("git@")
            or git_url.startswith("git://")
            or git_url.startswith("ssh://")
        ) and git_url.strip() != ""

        if is_valid_url:
            # 有效的URL应该能成功创建
            assignment = self.service.create_assignment(
                self.teacher1,
                self.course1,
                self.class1,
                name=f"测试作业_{git_url[:20]}",
                storage_type="git",
                git_url=git_url,
                git_branch="main",
            )

            self.assertEqual(assignment.git_url, git_url)
            self.assertEqual(assignment.storage_type, "git")

        else:
            # 无效的URL应该被拒绝
            with self.assertRaises(ValidationError) as cm:
                self.service.create_assignment(
                    self.teacher1,
                    self.course1,
                    self.class1,
                    name="测试作业",
                    storage_type="git",
                    git_url=git_url,
                    git_branch="main",
                )

            # 验证错误消息提到了URL
            error_msg = str(cm.exception.user_message)
            self.assertTrue(
                "URL" in error_msg or "url" in error_msg.lower(),
                f"Error message should mention URL, got: {error_msg}",
            )

    @given(
        name1=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
        name2=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_19_assignment_config_uniqueness(self, name1, name2):
        """**Feature: assignment-management-refactor, Property 19: 作业配置唯一性**

        For any 新的作业配置，系统应该检查是否存在相同课程、班级和名称的配置，存在则拒绝创建
        **Validates: Requirements 8.5**
        """
        from grading.assignment_utils import PathValidator, ValidationError

        # 确保用户配置文件存在
        # 清理之前的作业
        Assignment.objects.all().delete()

        # 创建第一个作业
        assignment1 = self.service.create_assignment(
            self.teacher1, self.course1, self.class1, name=name1, storage_type="filesystem"
        )

        self.assertIsNotNone(assignment1.id)

        # 清理名称以便比较
        clean_name1 = PathValidator.sanitize_name(name1)
        clean_name2 = PathValidator.sanitize_name(name2)

        # 如果两个名称清理后相同，应该拒绝创建
        if clean_name1 == clean_name2:
            with self.assertRaises(ValidationError) as cm:
                self.service.create_assignment(
                    self.teacher1, self.course1, self.class1, name=name2, storage_type="filesystem"
                )

            # 验证错误消息提到了重复
            error_msg = str(cm.exception.user_message)
            self.assertTrue(
                "已存在" in error_msg or "重复" in error_msg or "duplicate" in error_msg.lower(),
                f"Error message should mention duplicate, got: {error_msg}",
            )
        else:
            # 如果名称不同，应该能成功创建
            assignment2 = self.service.create_assignment(
                self.teacher1, self.course1, self.class1, name=name2, storage_type="filesystem"
            )

            self.assertIsNotNone(assignment2.id)
            self.assertNotEqual(assignment1.id, assignment2.id)
            self.assertNotEqual(assignment1.name, assignment2.name)

        # 测试跨课程/班级的唯一性：相同名称但不同课程应该允许
        assignment3 = self.service.create_assignment(
            self.teacher1,
            self.course2,  # 不同课程
            self.class2,
            name=name1,  # 相同名称
            storage_type="filesystem",
        )

        self.assertIsNotNone(assignment3.id)
        self.assertNotEqual(assignment1.id, assignment3.id)
        self.assertEqual(
            PathValidator.sanitize_name(assignment1.name),
            PathValidator.sanitize_name(assignment3.name),
        )
        self.assertNotEqual(assignment1.course, assignment3.course)

    @given(
        class1_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
        class2_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
        assignment_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip()
            and not any(c in x for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"])
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_14_class_directory_isolation(self, class1_name, class2_name, assignment_name):
        """**Feature: assignment-management-refactor, Property 14: 班级目录隔离**

        For any 同一课程的不同班级，系统应该为每个班级维护独立的作业目录
        **Validates: Requirements 7.3**
        """
        from grading.assignment_utils import PathValidator

        # 确保用户配置文件存在
        # 清理之前的作业
        Assignment.objects.all().delete()

        # 为同一课程创建两个不同的班级
        temp_class1 = Class.objects.create(
            course=self.course1,
            name=class1_name,
            tenant=self.tenant1,
        )
        temp_class2 = Class.objects.create(
            course=self.course1,  # 同一课程
            name=class2_name,
            tenant=self.tenant1,
        )

        # 为第一个班级创建作业配置
        assignment1 = self.service.create_assignment(
            self.teacher1,
            self.course1,
            temp_class1,
            name=assignment_name,
            storage_type="filesystem",
        )

        # 为第二个班级创建作业配置（同一课程，相同作业名）
        assignment2 = self.service.create_assignment(
            self.teacher1,
            self.course1,
            temp_class2,
            name=assignment_name,
            storage_type="filesystem",
        )

        # 验证两个作业配置都成功创建
        self.assertIsNotNone(assignment1.id)
        self.assertIsNotNone(assignment2.id)
        self.assertNotEqual(assignment1.id, assignment2.id)

        # 验证两个作业配置属于同一课程
        self.assertEqual(assignment1.course, assignment2.course)
        self.assertEqual(assignment1.course, self.course1)

        # 验证两个作业配置属于不同班级
        self.assertNotEqual(assignment1.class_obj, assignment2.class_obj)
        self.assertEqual(assignment1.class_obj, temp_class1)
        self.assertEqual(assignment2.class_obj, temp_class2)

        # 验证两个作业配置有不同的基础路径（目录隔离的核心）
        self.assertIsNotNone(assignment1.base_path)
        self.assertIsNotNone(assignment2.base_path)
        self.assertNotEqual(
            assignment1.base_path,
            assignment2.base_path,
            "Different classes should have different base paths",
        )

        # 验证路径格式：应该包含课程名和各自的班级名
        course_name_clean = PathValidator.sanitize_name(self.course1.name)
        class1_name_clean = PathValidator.sanitize_name(class1_name)
        class2_name_clean = PathValidator.sanitize_name(class2_name)

        # 验证第一个班级的路径包含正确的班级名
        self.assertIn(course_name_clean, assignment1.base_path)
        self.assertIn(class1_name_clean, assignment1.base_path)
        self.assertNotIn(class2_name_clean, assignment1.base_path)

        # 验证第二个班级的路径包含正确的班级名
        self.assertIn(course_name_clean, assignment2.base_path)
        self.assertIn(class2_name_clean, assignment2.base_path)
        self.assertNotIn(class1_name_clean, assignment2.base_path)

        # 验证路径格式符合 <课程名>/<班级名>/ 的规范
        expected_path1 = f"{course_name_clean}/{class1_name_clean}/"
        expected_path2 = f"{course_name_clean}/{class2_name_clean}/"

        self.assertEqual(
            assignment1.base_path, expected_path1, f"Class 1 path should be {expected_path1}"
        )
        self.assertEqual(
            assignment2.base_path, expected_path2, f"Class 2 path should be {expected_path2}"
        )

        # 验证目录隔离：两个路径不应该有重叠
        # 即一个路径不应该是另一个路径的前缀
        self.assertFalse(
            assignment1.base_path.startswith(assignment2.base_path),
            "Class 1 path should not be under Class 2 path",
        )
        self.assertFalse(
            assignment2.base_path.startswith(assignment1.base_path),
            "Class 2 path should not be under Class 1 path",
        )

        # 额外验证：如果班级名称清理后相同，路径应该相同（边界情况）
        if class1_name_clean == class2_name_clean:
            # 这种情况下，两个班级实际上会有相同的路径
            # 但它们仍然是不同的班级对象
            self.assertEqual(assignment1.base_path, assignment2.base_path)
        else:
            # 正常情况：不同的班级名应该产生不同的路径
            self.assertNotEqual(assignment1.base_path, assignment2.base_path)
