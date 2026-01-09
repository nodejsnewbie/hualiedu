"""
作业管理服务单元测试

测试 AssignmentManagementService 的核心功能，补充属性测试。
这些测试专注于具体的业务场景和边界条件。
"""

from datetime import date
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from grading.assignment_utils import ValidationError
from grading.models import Assignment, Class, Course, Semester, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService


class AssignmentManagementServiceUnitTest(TestCase):
    """AssignmentManagementService 单元测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant = Tenant.objects.create(name="测试学校", is_active=True)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 7, 15),
            is_active=True,
        )

        # 创建教师用户
        self.teacher = User.objects.create_user(
            username="teacher1", password="testpass123", email="teacher1@test.com"
        )
        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant
        )

        # 创建课程
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="数据结构",
            tenant=self.tenant,
        )

        # 创建班级
        self.class_obj = Class.objects.create(
            course=self.course, name="计算机1班", tenant=self.tenant
        )

        # 创建服务实例
        self.service = AssignmentManagementService()

    def tearDown(self):
        """清理测试数据"""
        Assignment.objects.all().delete()
        Class.objects.all().delete()
        Course.objects.all().delete()
        Semester.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Tenant.objects.all().delete()


class CreateAssignmentTest(AssignmentManagementServiceUnitTest):
    """测试 create_assignment 方法"""

    def test_create_filesystem_assignment_success(self):
        """测试成功创建文件系统类型作业"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
            description="测试作业描述",
        )

        self.assertIsNotNone(assignment.id)
        self.assertEqual(assignment.owner, self.teacher)
        self.assertEqual(assignment.tenant, self.tenant)
        self.assertEqual(assignment.course, self.course)
        self.assertEqual(assignment.class_obj, self.class_obj)
        self.assertEqual(assignment.name, "第一次作业")
        self.assertEqual(assignment.storage_type, "filesystem")
        self.assertIsNotNone(assignment.base_path)
        self.assertTrue(assignment.is_active)

    def test_create_git_assignment_success(self):
        """测试成功创建Git类型作业"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            git_username="testuser",
            git_password="testpass",
        )

        self.assertIsNotNone(assignment.id)
        self.assertEqual(assignment.storage_type, "git")
        self.assertEqual(assignment.git_url, "https://github.com/test/repo.git")
        self.assertEqual(assignment.git_branch, "main")
        self.assertEqual(assignment.git_username, "testuser")
        self.assertIsNotNone(assignment.git_password_encrypted)

    def test_create_assignment_empty_name_fails(self):
        """测试空名称创建失败"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="",
                storage_type="filesystem",
            )
        self.assertIn("名称", str(context.exception.user_message))

    def test_create_assignment_whitespace_name_fails(self):
        """测试仅空格名称创建失败"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="   ",
                storage_type="filesystem",
            )
        self.assertIn("名称", str(context.exception.user_message))

    def test_create_assignment_invalid_storage_type_fails(self):
        """测试无效存储类型创建失败"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="测试作业",
                storage_type="invalid_type",
            )
        self.assertIn("存储类型", str(context.exception.user_message))

    def test_create_git_assignment_missing_url_fails(self):
        """测试Git类型缺少URL创建失败"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="Git作业",
                storage_type="git",
            )
        self.assertIn("URL", str(context.exception.user_message))

    def test_create_git_assignment_invalid_url_fails(self):
        """测试Git类型无效URL创建失败"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="Git作业",
                storage_type="git",
                git_url="ftp://invalid.com/repo.git",
            )
        self.assertIn("URL", str(context.exception.user_message))

    def test_create_assignment_mismatched_course_class_fails(self):
        """测试课程和班级不匹配创建失败"""
        # 创建另一个课程
        other_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="算法设计",
            tenant=self.tenant,
        )

        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=other_course,  # 不同的课程
                class_obj=self.class_obj,  # 但班级属于原课程
                name="测试作业",
                storage_type="filesystem",
            )
        self.assertIn("不属于", str(context.exception.user_message))

    def test_create_duplicate_assignment_fails(self):
        """测试创建重复作业配置失败"""
        # 创建第一个作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 尝试创建重复的作业
        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name="第一次作业",
                storage_type="filesystem",
            )
        self.assertIn("已存在", str(context.exception.user_message))

    def test_create_assignment_different_tenant_fails(self):
        """测试不同租户的课程/班级创建失败"""
        # 创建另一个租户
        other_tenant = Tenant.objects.create(name="其他学校", is_active=True)

        # 创建属于其他租户的课程
        other_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="其他课程",
            tenant=other_tenant,
        )

        with self.assertRaises(ValidationError) as context:
            self.service.create_assignment(
                teacher=self.teacher,
                course=other_course,
                class_obj=self.class_obj,
                name="测试作业",
                storage_type="filesystem",
            )
        self.assertIn("租户", str(context.exception.user_message))

    def test_create_assignment_generates_base_path(self):
        """测试文件系统类型自动生成基础路径"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="测试作业",
            storage_type="filesystem",
        )

        # 验证路径格式
        self.assertIsNotNone(assignment.base_path)
        self.assertIn(self.course.name, assignment.base_path)
        self.assertIn(self.class_obj.name, assignment.base_path)
        self.assertTrue(assignment.base_path.endswith("/"))


class ListAssignmentsTest(AssignmentManagementServiceUnitTest):
    """测试 list_assignments 方法"""

    def setUp(self):
        super().setUp()
        # 创建多个作业用于测试
        self.assignment1 = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        self.assignment2 = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="第二次作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
        )

    def test_list_all_assignments(self):
        """测试列出所有作业"""
        assignments = self.service.list_assignments(teacher=self.teacher)

        self.assertEqual(assignments.count(), 2)
        self.assertIn(self.assignment1, assignments)
        self.assertIn(self.assignment2, assignments)

    def test_list_assignments_by_course(self):
        """测试按课程筛选作业"""
        # 创建另一个课程和作业
        other_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="算法设计",
            tenant=self.tenant,
        )
        other_class = Class.objects.create(
            course=other_course, name="计算机2班", tenant=self.tenant
        )
        other_assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=other_course,
            class_obj=other_class,
            name="算法作业",
            storage_type="filesystem",
        )

        # 按原课程筛选
        assignments = self.service.list_assignments(
            teacher=self.teacher, course_id=self.course.id
        )

        self.assertEqual(assignments.count(), 2)
        self.assertIn(self.assignment1, assignments)
        self.assertIn(self.assignment2, assignments)
        self.assertNotIn(other_assignment, assignments)

    def test_list_assignments_by_class(self):
        """测试按班级筛选作业"""
        # 创建另一个班级和作业
        other_class = Class.objects.create(
            course=self.course, name="计算机2班", tenant=self.tenant
        )
        other_assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=other_class,
            name="其他班级作业",
            storage_type="filesystem",
        )

        # 按原班级筛选
        assignments = self.service.list_assignments(
            teacher=self.teacher, class_id=self.class_obj.id
        )

        self.assertEqual(assignments.count(), 2)
        self.assertIn(self.assignment1, assignments)
        self.assertIn(self.assignment2, assignments)
        self.assertNotIn(other_assignment, assignments)

    def test_list_assignments_by_storage_type(self):
        """测试按存储类型筛选作业"""
        # 筛选文件系统类型
        fs_assignments = self.service.list_assignments(
            teacher=self.teacher, storage_type="filesystem"
        )
        self.assertEqual(fs_assignments.count(), 1)
        self.assertIn(self.assignment1, fs_assignments)

        # 筛选Git类型
        git_assignments = self.service.list_assignments(teacher=self.teacher, storage_type="git")
        self.assertEqual(git_assignments.count(), 1)
        self.assertIn(self.assignment2, git_assignments)

    def test_list_assignments_teacher_isolation(self):
        """测试教师隔离：只能看到自己的作业"""
        # 创建另一个教师
        other_teacher = User.objects.create_user(
            username="teacher2", password="testpass123"
        )
        UserProfile.objects.create(user=other_teacher, tenant=self.tenant)

        # 另一个教师创建作业
        other_course = Course.objects.create(
            semester=self.semester,
            teacher=other_teacher,
            name="操作系统",
            tenant=self.tenant,
        )
        other_class = Class.objects.create(
            course=other_course, name="计算机3班", tenant=self.tenant
        )
        other_assignment = self.service.create_assignment(
            teacher=other_teacher,
            course=other_course,
            class_obj=other_class,
            name="其他教师作业",
            storage_type="filesystem",
        )

        # 原教师只能看到自己的作业
        assignments = self.service.list_assignments(teacher=self.teacher)
        self.assertEqual(assignments.count(), 2)
        self.assertNotIn(other_assignment, assignments)

    def test_list_assignments_excludes_inactive(self):
        """测试默认排除未激活的作业"""
        # 停用一个作业
        self.assignment1.is_active = False
        self.assignment1.save()

        # 默认只返回激活的作业
        assignments = self.service.list_assignments(teacher=self.teacher)
        self.assertEqual(assignments.count(), 1)
        self.assertNotIn(self.assignment1, assignments)
        self.assertIn(self.assignment2, assignments)

    def test_list_assignments_includes_inactive_when_specified(self):
        """测试可以包含未激活的作业"""
        # 停用一个作业
        self.assignment1.is_active = False
        self.assignment1.save()

        # 明确请求包含未激活的作业
        assignments = self.service.list_assignments(teacher=self.teacher, is_active=None)
        self.assertEqual(assignments.count(), 2)


class UpdateAssignmentTest(AssignmentManagementServiceUnitTest):
    """测试 update_assignment 方法"""

    def setUp(self):
        super().setUp()
        self.assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="原始作业",
            storage_type="filesystem",
            description="原始描述",
        )

    def test_update_assignment_name(self):
        """测试更新作业名称"""
        updated = self.service.update_assignment(
            assignment=self.assignment, teacher=self.teacher, name="更新后的作业"
        )

        self.assertEqual(updated.name, "更新后的作业")
        self.assertEqual(updated.id, self.assignment.id)

    def test_update_assignment_description(self):
        """测试更新作业描述"""
        updated = self.service.update_assignment(
            assignment=self.assignment, teacher=self.teacher, description="新描述"
        )

        self.assertEqual(updated.description, "新描述")

    def test_update_assignment_is_active(self):
        """测试更新激活状态"""
        updated = self.service.update_assignment(
            assignment=self.assignment, teacher=self.teacher, is_active=False
        )

        self.assertFalse(updated.is_active)

    def test_update_assignment_preserves_immutable_fields(self):
        """测试更新保留不可变字段"""
        original_owner = self.assignment.owner
        original_tenant = self.assignment.tenant
        original_course = self.assignment.course
        original_class = self.assignment.class_obj
        original_storage_type = self.assignment.storage_type
        original_created_at = self.assignment.created_at

        # 尝试更新（这些字段应该被忽略或保护）
        updated = self.service.update_assignment(
            assignment=self.assignment, teacher=self.teacher, name="新名称"
        )

        # 验证不可变字段未改变
        self.assertEqual(updated.owner, original_owner)
        self.assertEqual(updated.tenant, original_tenant)
        self.assertEqual(updated.course, original_course)
        self.assertEqual(updated.class_obj, original_class)
        self.assertEqual(updated.storage_type, original_storage_type)
        self.assertEqual(updated.created_at, original_created_at)

    def test_update_assignment_wrong_teacher_fails(self):
        """测试其他教师无法更新作业"""
        other_teacher = User.objects.create_user(username="teacher2", password="testpass123")
        UserProfile.objects.create(user=other_teacher, tenant=self.tenant)

        with self.assertRaises(PermissionError):
            self.service.update_assignment(
                assignment=self.assignment, teacher=other_teacher, name="尝试修改"
            )

    def test_update_assignment_empty_name_fails(self):
        """测试更新为空名称失败"""
        with self.assertRaises(ValidationError):
            self.service.update_assignment(
                assignment=self.assignment, teacher=self.teacher, name=""
            )

    def test_update_assignment_duplicate_name_fails(self):
        """测试更新为重复名称失败"""
        # 创建另一个作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="已存在的作业",
            storage_type="filesystem",
        )

        # 尝试更新为已存在的名称
        with self.assertRaises(ValidationError):
            self.service.update_assignment(
                assignment=self.assignment, teacher=self.teacher, name="已存在的作业"
            )

    def test_update_git_assignment_url(self):
        """测试更新Git作业的URL"""
        git_assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/old/repo.git",
        )

        updated = self.service.update_assignment(
            assignment=git_assignment,
            teacher=self.teacher,
            git_url="https://github.com/new/repo.git",
        )

        self.assertEqual(updated.git_url, "https://github.com/new/repo.git")

    def test_update_git_assignment_branch(self):
        """测试更新Git作业的分支"""
        git_assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
        )

        updated = self.service.update_assignment(
            assignment=git_assignment, teacher=self.teacher, git_branch="develop"
        )

        self.assertEqual(updated.git_branch, "develop")


class DeleteAssignmentTest(AssignmentManagementServiceUnitTest):
    """测试 delete_assignment 方法"""

    def setUp(self):
        super().setUp()
        self.assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="待删除作业",
            storage_type="filesystem",
        )

    def test_delete_assignment_without_confirm_returns_impact(self):
        """测试未确认删除返回影响信息"""
        result = self.service.delete_assignment(
            assignment=self.assignment, teacher=self.teacher, confirm=False
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["deleted"])
        self.assertIn("impact", result)
        self.assertIn("warning", result["impact"])

        # 作业应该还存在
        self.assertTrue(Assignment.objects.filter(id=self.assignment.id).exists())

    def test_delete_assignment_with_confirm_deletes(self):
        """测试确认删除成功删除作业"""
        result = self.service.delete_assignment(
            assignment=self.assignment, teacher=self.teacher, confirm=True
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["deleted"])

        # 作业应该已删除
        self.assertFalse(Assignment.objects.filter(id=self.assignment.id).exists())

    def test_delete_assignment_wrong_teacher_fails(self):
        """测试其他教师无法删除作业"""
        other_teacher = User.objects.create_user(username="teacher2", password="testpass123")
        UserProfile.objects.create(user=other_teacher, tenant=self.tenant)

        with self.assertRaises(PermissionError):
            self.service.delete_assignment(
                assignment=self.assignment, teacher=other_teacher, confirm=True
            )

        # 作业应该还存在
        self.assertTrue(Assignment.objects.filter(id=self.assignment.id).exists())


class GetAssignmentSummaryTest(AssignmentManagementServiceUnitTest):
    """测试 get_assignment_summary 方法"""

    def test_summary_empty(self):
        """测试空作业列表的统计"""
        summary = self.service.get_assignment_summary(teacher=self.teacher)

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["active"], 0)
        self.assertEqual(summary["git_count"], 0)
        self.assertEqual(summary["filesystem_count"], 0)

    def test_summary_with_assignments(self):
        """测试有作业时的统计"""
        # 创建多个作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业2",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
        )
        assignment3 = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业3",
            storage_type="filesystem",
        )
        # 停用一个作业
        assignment3.is_active = False
        assignment3.save()

        summary = self.service.get_assignment_summary(teacher=self.teacher)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["active"], 2)
        self.assertEqual(summary["git_count"], 1)
        self.assertEqual(summary["filesystem_count"], 2)
        self.assertEqual(summary["courses_count"], 1)
        self.assertEqual(summary["classes_count"], 1)


class GetTeacherCoursesTest(AssignmentManagementServiceUnitTest):
    """测试 get_teacher_courses 方法"""

    def test_get_courses_empty(self):
        """测试无作业时返回空列表"""
        courses = self.service.get_teacher_courses(teacher=self.teacher)
        self.assertEqual(courses.count(), 0)

    def test_get_courses_with_assignments(self):
        """测试有作业时返回课程列表"""
        # 创建作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )

        courses = self.service.get_teacher_courses(teacher=self.teacher)
        self.assertEqual(courses.count(), 1)
        self.assertIn(self.course, courses)

    def test_get_courses_deduplicates(self):
        """测试课程去重"""
        # 同一课程创建多个作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业2",
            storage_type="filesystem",
        )

        courses = self.service.get_teacher_courses(teacher=self.teacher)
        self.assertEqual(courses.count(), 1)


class GetTeacherClassesTest(AssignmentManagementServiceUnitTest):
    """测试 get_teacher_classes 方法"""

    def test_get_classes_empty(self):
        """测试无作业时返回空列表"""
        classes = self.service.get_teacher_classes(teacher=self.teacher)
        self.assertEqual(classes.count(), 0)

    def test_get_classes_with_assignments(self):
        """测试有作业时返回班级列表"""
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )

        classes = self.service.get_teacher_classes(teacher=self.teacher)
        self.assertEqual(classes.count(), 1)
        self.assertIn(self.class_obj, classes)

    def test_get_classes_filtered_by_course(self):
        """测试按课程筛选班级"""
        # 创建另一个课程和班级
        other_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="算法设计",
            tenant=self.tenant,
        )
        other_class = Class.objects.create(
            course=other_course, name="计算机2班", tenant=self.tenant
        )

        # 为两个课程创建作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )
        self.service.create_assignment(
            teacher=self.teacher,
            course=other_course,
            class_obj=other_class,
            name="作业2",
            storage_type="filesystem",
        )

        # 按课程筛选
        classes = self.service.get_teacher_classes(teacher=self.teacher, course_id=self.course.id)
        self.assertEqual(classes.count(), 1)
        self.assertIn(self.class_obj, classes)
        self.assertNotIn(other_class, classes)



class GetAssignmentStructureTest(AssignmentManagementServiceUnitTest):
    """测试 get_assignment_structure 方法"""

    def setUp(self):
        super().setUp()
        self.fs_assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="文件系统作业",
            storage_type="filesystem",
        )

    @patch("grading.services.assignment_management_service.FileSystemStorageAdapter")
    def test_get_structure_filesystem_success(self, mock_adapter_class):
        """测试获取文件系统作业结构成功"""
        # Mock适配器
        mock_adapter = Mock()
        mock_adapter.list_directory.return_value = [
            {"name": "第一次作业", "type": "dir", "size": 0},
            {"name": "第二次作业", "type": "dir", "size": 0},
        ]
        mock_adapter_class.return_value = mock_adapter

        result = self.service.get_assignment_structure(self.fs_assignment, "")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["entries"]), 2)
        self.assertEqual(result["entries"][0]["name"], "第一次作业")

    @patch("grading.services.assignment_management_service.FileSystemStorageAdapter")
    def test_get_structure_with_path(self, mock_adapter_class):
        """测试获取子目录结构"""
        mock_adapter = Mock()
        mock_adapter.list_directory.return_value = [
            {"name": "张三-作业1.docx", "type": "file", "size": 1024},
        ]
        mock_adapter_class.return_value = mock_adapter

        result = self.service.get_assignment_structure(self.fs_assignment, "第一次作业")

        self.assertTrue(result["success"])
        mock_adapter.list_directory.assert_called_once_with("第一次作业")

    @patch("grading.services.assignment_management_service.FileSystemStorageAdapter")
    def test_get_structure_error_handling(self, mock_adapter_class):
        """测试获取结构时的错误处理"""
        from grading.services.storage_adapter import FileSystemError

        mock_adapter = Mock()
        mock_adapter.list_directory.side_effect = FileSystemError(
            "Directory not found", user_message="目录不存在"
        )
        mock_adapter_class.return_value = mock_adapter

        result = self.service.get_assignment_structure(self.fs_assignment, "nonexistent")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "目录不存在")


class PathGenerationTest(AssignmentManagementServiceUnitTest):
    """测试路径生成相关功能"""

    def test_base_path_format(self):
        """测试基础路径格式"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="测试作业",
            storage_type="filesystem",
        )

        # 验证路径格式：<课程名>/<班级名>/
        self.assertIsNotNone(assignment.base_path)
        self.assertTrue(assignment.base_path.endswith("/"))

        parts = assignment.base_path.rstrip("/").split("/")
        self.assertEqual(len(parts), 2)

    def test_base_path_special_characters(self):
        """测试路径中特殊字符的处理"""
        # 创建包含特殊字符的课程和班级
        special_course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="数据结构/算法",  # 包含斜杠
            tenant=self.tenant,
        )
        special_class = Class.objects.create(
            course=special_course, name="计算机:1班", tenant=self.tenant  # 包含冒号
        )

        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=special_course,
            class_obj=special_class,
            name="测试作业",
            storage_type="filesystem",
        )

        # 验证特殊字符被清理
        self.assertNotIn("/", assignment.base_path.rstrip("/").replace("/", "", 1))
        self.assertNotIn(":", assignment.base_path)

    def test_base_path_chinese_characters(self):
        """测试路径支持中文字符"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="第一次作业",
            storage_type="filesystem",
        )

        # 验证路径包含中文
        self.assertIn("数据结构", assignment.base_path)
        self.assertIn("计算机", assignment.base_path)


class TenantIsolationTest(AssignmentManagementServiceUnitTest):
    """测试租户隔离"""

    def setUp(self):
        super().setUp()
        # 创建第二个租户
        self.tenant2 = Tenant.objects.create(name="其他学校", is_active=True)

        # 创建第二个租户的教师
        self.teacher2 = User.objects.create_user(
            username="teacher2", password="testpass123"
        )
        self.teacher2_profile = UserProfile.objects.create(
            user=self.teacher2, tenant=self.tenant2
        )

        # 创建第二个租户的课程和班级
        self.semester2 = Semester.objects.create(
            name="2024年秋季学期",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 1, 15),
            is_active=True,
        )
        self.course2 = Course.objects.create(
            semester=self.semester2,
            teacher=self.teacher2,
            name="数据结构",
            tenant=self.tenant2,
        )
        self.class2 = Class.objects.create(
            course=self.course2, name="计算机1班", tenant=self.tenant2
        )

    def test_create_assignment_validates_tenant(self):
        """测试创建作业时验证租户"""
        # 教师1尝试为教师2的课程创建作业
        with self.assertRaises(ValidationError):
            self.service.create_assignment(
                teacher=self.teacher,
                course=self.course2,  # 属于tenant2
                class_obj=self.class2,
                name="跨租户作业",
                storage_type="filesystem",
            )

    def test_list_assignments_tenant_isolation(self):
        """测试列表作业时的租户隔离"""
        # 两个租户各创建作业
        assignment1 = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="租户1作业",
            storage_type="filesystem",
        )
        assignment2 = self.service.create_assignment(
            teacher=self.teacher2,
            course=self.course2,
            class_obj=self.class2,
            name="租户2作业",
            storage_type="filesystem",
        )

        # 教师1只能看到自己租户的作业
        assignments1 = self.service.list_assignments(teacher=self.teacher)
        self.assertIn(assignment1, assignments1)
        self.assertNotIn(assignment2, assignments1)

        # 教师2只能看到自己租户的作业
        assignments2 = self.service.list_assignments(teacher=self.teacher2)
        self.assertIn(assignment2, assignments2)
        self.assertNotIn(assignment1, assignments2)

    def test_update_assignment_tenant_check(self):
        """测试更新作业时的租户检查"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="租户1作业",
            storage_type="filesystem",
        )

        # 教师2尝试更新教师1的作业
        with self.assertRaises(PermissionError):
            self.service.update_assignment(
                assignment=assignment, teacher=self.teacher2, name="尝试修改"
            )


class EdgeCasesTest(AssignmentManagementServiceUnitTest):
    """测试边界情况和特殊场景"""

    def test_create_assignment_with_very_long_name(self):
        """测试创建超长名称的作业"""
        long_name = "作业" * 100  # 200个字符

        # 应该成功创建（或根据验证规则失败）
        try:
            assignment = self.service.create_assignment(
                teacher=self.teacher,
                course=self.course,
                class_obj=self.class_obj,
                name=long_name,
                storage_type="filesystem",
            )
            # 如果成功，验证名称被正确存储
            self.assertIsNotNone(assignment.id)
        except ValidationError:
            # 如果有长度限制，应该抛出验证错误
            pass

    def test_create_assignment_with_unicode_name(self):
        """测试创建包含Unicode字符的作业"""
        unicode_name = "作业📝测试🎓"

        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name=unicode_name,
            storage_type="filesystem",
        )

        self.assertIsNotNone(assignment.id)

    def test_list_assignments_empty_result(self):
        """测试列表作业返回空结果"""
        assignments = self.service.list_assignments(teacher=self.teacher)
        self.assertEqual(assignments.count(), 0)

    def test_get_summary_with_multiple_courses_and_classes(self):
        """测试多课程多班级的统计"""
        # 创建多个课程和班级
        course2 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="算法设计",
            tenant=self.tenant,
        )
        class2 = Class.objects.create(course=self.course, name="计算机2班", tenant=self.tenant)
        class3 = Class.objects.create(course=course2, name="计算机3班", tenant=self.tenant)

        # 创建多个作业
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="作业1",
            storage_type="filesystem",
        )
        self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=class2,
            name="作业2",
            storage_type="filesystem",
        )
        self.service.create_assignment(
            teacher=self.teacher,
            course=course2,
            class_obj=class3,
            name="作业3",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
        )

        summary = self.service.get_assignment_summary(teacher=self.teacher)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["courses_count"], 2)
        self.assertEqual(summary["classes_count"], 3)

    def test_create_assignment_git_default_branch(self):
        """测试Git作业默认分支"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="Git作业",
            storage_type="git",
            git_url="https://github.com/test/repo.git",
            # 不指定分支
        )

        # 应该使用默认分支
        self.assertEqual(assignment.git_branch, "main")

    def test_update_assignment_no_changes(self):
        """测试更新作业但不提供任何更改"""
        assignment = self.service.create_assignment(
            teacher=self.teacher,
            course=self.course,
            class_obj=self.class_obj,
            name="测试作业",
            storage_type="filesystem",
        )

        # 不提供任何更新字段
        updated = self.service.update_assignment(assignment=assignment, teacher=self.teacher)

        # 应该返回原对象，没有错误
        self.assertEqual(updated.id, assignment.id)
