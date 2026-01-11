"""
测试 delete_assignment 方法

验证作业删除功能的正确性，包括：
- 权限检查
- 删除确认流程
- 级联删除处理
- 影响信息提供
"""

from django.contrib.auth.models import User
from django.test import TestCase

from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService


class DeleteAssignmentTestCase(TestCase):
    """测试 delete_assignment 方法"""

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant = Tenant.objects.create(name="测试学校", description="测试租户")

        # 创建教师用户
        self.teacher = User.objects.create_user(username="teacher1", password="password123")
        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # 创建另一个教师用户（用于测试权限）
        self.other_teacher = User.objects.create_user(username="teacher2", password="password123")
        self.other_teacher_profile = UserProfile.objects.create(
            user=self.other_teacher, tenant=self.tenant, is_tenant_admin=False
        )

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024春季", start_date="2024-02-01", end_date="2024-06-30"
        )

        # 创建课程
        self.course = Course.objects.create(
            name="数据结构", semester=self.semester, teacher=self.teacher
        )

        # 创建班级
        self.class_obj = Class.objects.create(name="计算机1班", course=self.course)

        # 创建作业配置
        self.assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            description="测试作业",
            storage_type="filesystem",
            base_path="/tmp/test",
        )

        self.service = AssignmentManagementService()

    def test_delete_without_confirm_returns_impact_info(self):
        """测试未确认删除时返回影响信息"""
        result = self.service.delete_assignment(self.assignment, self.teacher, confirm=False)

        self.assertTrue(result["success"])
        self.assertFalse(result["deleted"])
        self.assertEqual(result["message"], "请确认删除操作")

        # 验证影响信息
        impact = result["impact"]
        self.assertEqual(impact["assignment_name"], "第一次作业")
        self.assertEqual(impact["course_name"], "数据结构")
        self.assertEqual(impact["class_name"], "计算机1班")
        self.assertEqual(impact["storage_type"], "文件上传")
        self.assertFalse(impact["has_submissions"])
        self.assertIn("您即将删除作业配置", impact["warning"])
        self.assertIn("此操作不可撤销", impact["warning"])

    def test_delete_with_confirm_deletes_assignment(self):
        """测试确认删除时成功删除作业"""
        assignment_id = self.assignment.id

        result = self.service.delete_assignment(self.assignment, self.teacher, confirm=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["deleted"])
        self.assertIn("已成功删除", result["message"])

        # 验证作业已被删除
        self.assertFalse(Assignment.objects.filter(id=assignment_id).exists())

    def test_delete_by_non_owner_raises_permission_error(self):
        """测试非所有者删除作业时抛出权限错误"""
        with self.assertRaises(PermissionError) as context:
            self.service.delete_assignment(self.assignment, self.other_teacher, confirm=True)

        self.assertIn("没有权限删除", str(context.exception))

        # 验证作业未被删除
        self.assertTrue(Assignment.objects.filter(id=self.assignment.id).exists())

    def test_delete_git_assignment_shows_git_warning(self):
        """测试删除Git类型作业时显示Git相关警告"""
        git_assignment = Assignment.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        result = self.service.delete_assignment(git_assignment, self.teacher, confirm=False)

        impact = result["impact"]
        self.assertEqual(impact["storage_type"], "Git仓库")
        self.assertIn("不会影响远程Git仓库", impact["warning"])

    def test_delete_filesystem_assignment_shows_filesystem_warning(self):
        """测试删除文件系统类型作业时显示文件系统相关警告"""
        result = self.service.delete_assignment(self.assignment, self.teacher, confirm=False)

        impact = result["impact"]
        self.assertEqual(impact["storage_type"], "文件上传")
        self.assertIn("不会删除文件系统中已上传的作业文件", impact["warning"])

    def test_delete_workflow(self):
        """测试完整的删除工作流程"""
        # 第一步：获取影响信息
        result1 = self.service.delete_assignment(self.assignment, self.teacher, confirm=False)

        self.assertFalse(result1["deleted"])
        self.assertIn("impact", result1)

        # 验证作业仍然存在
        self.assertTrue(Assignment.objects.filter(id=self.assignment.id).exists())

        # 第二步：确认删除
        result2 = self.service.delete_assignment(self.assignment, self.teacher, confirm=True)

        self.assertTrue(result2["deleted"])

        # 验证作业已被删除
        self.assertFalse(Assignment.objects.filter(id=self.assignment.id).exists())
