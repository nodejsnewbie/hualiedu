"""
作业管理服务的属性测试

使用 Hypothesis 进行基于属性的测试，验证通用规则。
"""

import hypothesis
from django.contrib.auth.models import User
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase

from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService

# 配置最小迭代次数
hypothesis.settings.register_profile("ci", max_examples=100)
hypothesis.settings.load_profile("ci")


class TestAssignmentManagementServiceProperties(TestCase):
    """AssignmentManagementService 属性测试"""

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
        UserProfile.objects.get_or_create(user=self.teacher1, defaults={'tenant': self.tenant1})
        UserProfile.objects.get_or_create(user=self.teacher2, defaults={'tenant': self.tenant1})
        UserProfile.objects.get_or_create(user=self.teacher3, defaults={'tenant': self.tenant2})

        # 清除 Django 的 related object cache (related_name is 'profile')
        if hasattr(self.teacher1, '_profile_cache'):
            del self.teacher1._profile_cache
        if hasattr(self.teacher2, '_profile_cache'):
            del self.teacher2._profile_cache
        if hasattr(self.teacher3, '_profile_cache'):
            del self.teacher3._profile_cache
        
        # Also add userprofile as an alias to profile for compatibility
        # This is needed because the service uses teacher.userprofile
        for teacher in [self.teacher1, self.teacher2, self.teacher3]:
            if hasattr(teacher, 'profile') and not hasattr(teacher, 'userprofile'):
                teacher.userprofile = teacher.profile

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
            lambda x: x.strip() and not any(c in x for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|'])
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
        UserProfile.objects.get_or_create(user=self.teacher1, defaults={'tenant': self.tenant1})
        
        # 清除 Django 的 related object cache
        if hasattr(self.teacher1, '_profile_cache'):
            del self.teacher1._profile_cache
        if hasattr(self.teacher1, 'profile') and not hasattr(self.teacher1, 'userprofile'):
            self.teacher1.userprofile = self.teacher1.profile

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
            updated_assignment.id,
            original_id,
            "Assignment ID should not change during update"
        )
        self.assertEqual(
            updated_assignment.owner,
            original_owner,
            "Assignment owner should not change during update"
        )
        self.assertEqual(
            updated_assignment.tenant,
            original_tenant,
            "Assignment tenant should not change during update"
        )
        self.assertEqual(
            updated_assignment.course,
            original_course,
            "Assignment course should not change during update"
        )
        self.assertEqual(
            updated_assignment.class_obj,
            original_class_obj,
            "Assignment class should not change during update"
        )
        self.assertEqual(
            updated_assignment.storage_type,
            original_storage_type,
            "Assignment storage_type should not change during update"
        )
        self.assertEqual(
            updated_assignment.created_at,
            original_created_at,
            "Assignment created_at should not change during update"
        )

        # 验证可更新的字段确实被更新了
        self.assertNotEqual(
            updated_assignment.name,
            "原始作业名称",
            "Assignment name should be updated"
        )
        self.assertEqual(
            updated_assignment.description,
            description_update,
            "Assignment description should be updated"
        )
        self.assertEqual(
            updated_assignment.is_active,
            is_active_update,
            "Assignment is_active should be updated"
        )
        self.assertEqual(
            updated_assignment.git_branch,
            git_branch_update,
            "Assignment git_branch should be updated"
        )

        # 验证其他Git配置字段保持不变（因为我们没有更新它们）
        self.assertEqual(
            updated_assignment.git_url,
            "https://github.com/original/repo.git",
            "Git URL should remain unchanged when not updated"
        )
        self.assertEqual(
            updated_assignment.git_username,
            "original_user",
            "Git username should remain unchanged when not updated"
        )
        self.assertEqual(
            updated_assignment.git_password_encrypted,
            "encrypted_password",
            "Git password should remain unchanged when not updated"
        )

        # 验证updated_at字段被更新了
        self.assertGreater(
            updated_assignment.updated_at,
            original_created_at,
            "Assignment updated_at should be greater than created_at after update"
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
            "Base path should remain unchanged when not explicitly updated"
        )
