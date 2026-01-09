"""
课程管理服务测试模块

测试课程管理服务的创建、查询和管理功能
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from grading.models import Course, Semester, Tenant
from grading.services.course_service import CourseService


class CourseServiceTest(TestCase):
    """课程管理服务测试类"""

    def setUp(self):
        """设置测试数据"""
        self.service = CourseService()

        # 创建租户
        self.tenant1 = Tenant.objects.create(name="测试学校1", is_active=True)
        self.tenant2 = Tenant.objects.create(name="测试学校2", is_active=True)

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username="teacher1", password="testpass123", first_name="张", last_name="老师"
        )
        self.teacher2 = User.objects.create_user(
            username="teacher2", password="testpass123", first_name="李", last_name="老师"
        )

        # 创建用户配置文件
        from grading.models import UserProfile

        self.teacher1_profile = UserProfile.objects.create(user=self.teacher1, tenant=self.tenant1)
        self.teacher2_profile = UserProfile.objects.create(user=self.teacher2, tenant=self.tenant2)

        # 创建学期
        today = date.today()
        self.semester1 = Semester.objects.create(
            name="2024年春季学期",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            is_active=True,
        )
        self.semester2 = Semester.objects.create(
            name="2024年秋季学期",
            start_date=today + timedelta(days=90),
            end_date=today + timedelta(days=180),
            is_active=False,
        )

    def test_create_course_success(self):
        """测试成功创建课程"""
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            description="数据结构与算法课程",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 验证课程创建成功
        self.assertIsNotNone(course)
        self.assertEqual(course.name, "数据结构")
        self.assertEqual(course.course_type, "theory")
        self.assertEqual(course.description, "数据结构与算法课程")
        self.assertEqual(course.teacher, self.teacher1)
        self.assertEqual(course.semester, self.semester1)
        self.assertEqual(course.tenant, self.tenant1)

        # 验证数据库中存在该课程
        self.assertTrue(Course.objects.filter(id=course.id).exists())

    def test_create_course_auto_tenant(self):
        """测试自动从教师配置获取租户"""
        course = self.service.create_course(
            teacher=self.teacher1,
            name="操作系统",
            course_type="lab",
            semester=self.semester1,
        )

        # 验证租户自动设置
        self.assertEqual(course.tenant, self.tenant1)

    def test_create_course_invalid_type(self):
        """测试创建课程时使用无效类型"""
        with self.assertRaises(ValueError) as context:
            self.service.create_course(
                teacher=self.teacher1,
                name="测试课程",
                course_type="invalid_type",
                semester=self.semester1,
                tenant=self.tenant1,
            )

        self.assertIn("无效的课程类型", str(context.exception))

    def test_create_course_empty_name(self):
        """测试创建课程时名称为空"""
        with self.assertRaises(ValueError) as context:
            self.service.create_course(
                teacher=self.teacher1,
                name="   ",
                course_type="theory",
                semester=self.semester1,
                tenant=self.tenant1,
            )

        self.assertIn("课程名称不能为空", str(context.exception))

    def test_create_course_no_teacher(self):
        """测试创建课程时没有教师"""
        with self.assertRaises(ValueError) as context:
            self.service.create_course(
                teacher=None,
                name="测试课程",
                course_type="theory",
                semester=self.semester1,
                tenant=self.tenant1,
            )

        self.assertIn("必须指定授课教师", str(context.exception))

    def test_create_course_no_semester(self):
        """测试创建课程时没有学期"""
        with self.assertRaises(ValueError) as context:
            self.service.create_course(
                teacher=self.teacher1,
                name="测试课程",
                course_type="theory",
                semester=None,
                tenant=self.tenant1,
            )

        self.assertIn("必须指定所属学期", str(context.exception))

    def test_list_courses_teacher_isolation(self):
        """测试教师数据隔离 - Property 2"""
        # 为teacher1创建课程
        course1 = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        course2 = self.service.create_course(
            teacher=self.teacher1,
            name="算法设计",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 为teacher2创建课程
        course3 = self.service.create_course(
            teacher=self.teacher2,
            name="操作系统",
            course_type="lab",
            semester=self.semester1,
            tenant=self.tenant2,
        )

        # 查询teacher1的课程
        teacher1_courses = self.service.list_courses(self.teacher1)

        # 验证只返回teacher1的课程
        self.assertEqual(len(teacher1_courses), 2)
        course_ids = [c.id for c in teacher1_courses]
        self.assertIn(course1.id, course_ids)
        self.assertIn(course2.id, course_ids)
        self.assertNotIn(course3.id, course_ids)

        # 查询teacher2的课程
        teacher2_courses = self.service.list_courses(self.teacher2)

        # 验证只返回teacher2的课程
        self.assertEqual(len(teacher2_courses), 1)
        self.assertEqual(teacher2_courses[0].id, course3.id)

    def test_list_courses_with_semester_filter(self):
        """测试按学期过滤课程"""
        # 在不同学期创建课程
        course1 = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        course2 = self.service.create_course(
            teacher=self.teacher1,
            name="算法设计",
            course_type="theory",
            semester=self.semester2,
            tenant=self.tenant1,
        )

        # 查询semester1的课程
        semester1_courses = self.service.list_courses(self.teacher1, semester=self.semester1)
        self.assertEqual(len(semester1_courses), 1)
        self.assertEqual(semester1_courses[0].id, course1.id)

        # 查询semester2的课程
        semester2_courses = self.service.list_courses(self.teacher1, semester=self.semester2)
        self.assertEqual(len(semester2_courses), 1)
        self.assertEqual(semester2_courses[0].id, course2.id)

    def test_list_courses_with_tenant_filter(self):
        """测试按租户过滤课程"""
        # 创建课程
        course1 = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 查询时指定租户
        courses = self.service.list_courses(self.teacher1, tenant=self.tenant1)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].id, course1.id)

        # 查询不存在的租户
        courses = self.service.list_courses(self.teacher1, tenant=self.tenant2)
        self.assertEqual(len(courses), 0)

    def test_update_course_type_success(self):
        """测试成功更新课程类型"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 更新课程类型
        updated_course = self.service.update_course_type(course.id, "lab")

        # 验证更新成功
        self.assertEqual(updated_course.course_type, "lab")

        # 验证数据库中已更新
        course.refresh_from_db()
        self.assertEqual(course.course_type, "lab")

    def test_update_course_type_invalid(self):
        """测试更新课程类型时使用无效类型"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 尝试使用无效类型更新
        with self.assertRaises(ValueError) as context:
            self.service.update_course_type(course.id, "invalid_type")

        self.assertIn("无效的课程类型", str(context.exception))

    def test_update_course_type_not_found(self):
        """测试更新不存在的课程"""
        with self.assertRaises(Course.DoesNotExist):
            self.service.update_course_type(99999, "lab")

    def test_get_course_by_id_success(self):
        """测试根据ID获取课程"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 获取课程
        retrieved_course = self.service.get_course_by_id(course.id)

        # 验证获取成功
        self.assertEqual(retrieved_course.id, course.id)
        self.assertEqual(retrieved_course.name, "数据结构")

    def test_get_course_by_id_with_teacher_filter(self):
        """测试根据ID获取课程时验证教师权限"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # teacher1可以访问
        retrieved_course = self.service.get_course_by_id(course.id, teacher=self.teacher1)
        self.assertEqual(retrieved_course.id, course.id)

        # teacher2不能访问
        with self.assertRaises(Course.DoesNotExist):
            self.service.get_course_by_id(course.id, teacher=self.teacher2)

    def test_get_courses_by_semester(self):
        """测试获取指定学期的课程"""
        # 创建多个课程
        course1 = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        course2 = self.service.create_course(
            teacher=self.teacher1,
            name="算法设计",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        course3 = self.service.create_course(
            teacher=self.teacher1,
            name="操作系统",
            course_type="lab",
            semester=self.semester2,
            tenant=self.tenant1,
        )

        # 获取semester1的课程
        semester1_courses = self.service.get_courses_by_semester(self.semester1)
        self.assertEqual(len(semester1_courses), 2)

        # 获取semester2的课程
        semester2_courses = self.service.get_courses_by_semester(self.semester2)
        self.assertEqual(len(semester2_courses), 1)

    def test_delete_course_success(self):
        """测试删除课程"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        course_id = course.id

        # 删除课程
        self.service.delete_course(course_id)

        # 验证课程已删除
        self.assertFalse(Course.objects.filter(id=course_id).exists())

    def test_delete_course_with_teacher_permission(self):
        """测试删除课程时验证教师权限"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # teacher2不能删除teacher1的课程
        with self.assertRaises(Course.DoesNotExist):
            self.service.delete_course(course.id, teacher=self.teacher2)

        # 验证课程仍然存在
        self.assertTrue(Course.objects.filter(id=course.id).exists())

    def test_update_course_success(self):
        """测试更新课程信息"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            description="原始描述",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 更新课程
        updated_course = self.service.update_course(
            course_id=course.id,
            name="数据结构与算法",
            course_type="lab",
            description="更新后的描述",
        )

        # 验证更新成功
        self.assertEqual(updated_course.name, "数据结构与算法")
        self.assertEqual(updated_course.course_type, "lab")
        self.assertEqual(updated_course.description, "更新后的描述")

        # 验证数据库中已更新
        course.refresh_from_db()
        self.assertEqual(course.name, "数据结构与算法")
        self.assertEqual(course.course_type, "lab")
        self.assertEqual(course.description, "更新后的描述")

    def test_update_course_partial(self):
        """测试部分更新课程信息"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            description="原始描述",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 只更新名称
        updated_course = self.service.update_course(course_id=course.id, name="新名称")

        # 验证只有名称更新
        self.assertEqual(updated_course.name, "新名称")
        self.assertEqual(updated_course.course_type, "theory")  # 未改变
        self.assertEqual(updated_course.description, "原始描述")  # 未改变

    def test_update_course_empty_name(self):
        """测试更新课程时名称为空"""
        # 创建课程
        course = self.service.create_course(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 尝试设置空名称
        with self.assertRaises(ValueError) as context:
            self.service.update_course(course_id=course.id, name="   ")

        self.assertIn("课程名称不能为空", str(context.exception))

    def test_list_courses_ordering(self):
        """测试课程列表排序"""
        # 创建多个课程
        course1 = self.service.create_course(
            teacher=self.teacher1,
            name="B课程",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        course2 = self.service.create_course(
            teacher=self.teacher1,
            name="A课程",
            course_type="theory",
            semester=self.semester2,
            tenant=self.tenant1,
        )
        course3 = self.service.create_course(
            teacher=self.teacher1,
            name="C课程",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )

        # 获取课程列表
        courses = self.service.list_courses(self.teacher1)

        # 验证排序：先按学期倒序，再按名称
        self.assertEqual(len(courses), 3)
        # semester2的课程应该在前面（开始日期更晚）
        self.assertEqual(courses[0].id, course2.id)
        # semester1的课程按名称排序
        self.assertEqual(courses[1].name, "B课程")
        self.assertEqual(courses[2].name, "C课程")
