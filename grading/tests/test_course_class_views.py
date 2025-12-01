"""
测试课程和班级管理视图

测试课程创建、列表、班级创建和列表视图的功能
"""

import logging
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from grading.models import Course, Class, Semester, Tenant
from grading.tests.base import BaseTestCase

# 配置日志
logger = logging.getLogger(__name__)


class CourseClassViewsTestCase(BaseTestCase):
    """课程和班级管理视图测试"""

    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.client = Client()

        # 创建测试用户
        self.teacher = User.objects.create_user(
            username="teacher1", password="testpass123", email="teacher1@test.com"
        )

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户", description="测试租户描述")

        # 为用户创建用户配置
        from grading.models import UserProfile

        self.user_profile = UserProfile.objects.create(
            user=self.teacher, tenant=self.tenant, repo_base_dir="~/test_repos"
        )

        # 创建测试学期
        from datetime import date

        self.semester = Semester.objects.create(
            name="2024-2025学年第一学期",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 1, 15),
            is_active=True,
        )

        # 登录
        self.client.login(username="teacher1", password="testpass123")

    def test_course_list_view(self):
        """测试课程列表视图"""
        # 创建测试课程
        course1 = Course.objects.create(
            teacher=self.teacher,
            name="数据结构",
            course_type="theory",
            description="数据结构课程",
            semester=self.semester,
            tenant=self.tenant,
        )

        course2 = Course.objects.create(
            teacher=self.teacher,
            name="操作系统实验",
            course_type="lab",
            description="操作系统实验课程",
            semester=self.semester,
            tenant=self.tenant,
        )

        # 访问课程列表页面
        response = self.client.get(reverse("grading:course_list"))

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "数据结构")
        self.assertContains(response, "操作系统实验")

    def test_course_create_view_get(self):
        """测试课程创建视图 - GET请求"""
        response = self.client.get(reverse("grading:course_create"))

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "创建课程")
        self.assertContains(response, "课程名称")
        self.assertContains(response, "课程类型")

    def test_course_create_view_post(self):
        """测试课程创建视图 - POST请求"""
        # 发送创建课程请求
        response = self.client.post(
            reverse("grading:course_create"),
            {
                "name": "计算机网络",
                "course_type": "theory",
                "description": "计算机网络课程",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("course_id", data)

        # 验证课程已创建
        course = Course.objects.get(id=data["course_id"])
        self.assertEqual(course.name, "计算机网络")
        self.assertEqual(course.course_type, "theory")
        self.assertEqual(course.teacher, self.teacher)

    def test_class_list_view(self):
        """测试班级列表视图"""
        # 创建测试课程
        course = Course.objects.create(
            teacher=self.teacher,
            name="数据结构",
            course_type="theory",
            semester=self.semester,
            tenant=self.tenant,
        )

        # 创建测试班级
        class1 = Class.objects.create(
            course=course, name="计算机科学1班", student_count=30, tenant=self.tenant
        )

        class2 = Class.objects.create(
            course=course, name="计算机科学2班", student_count=28, tenant=self.tenant
        )

        # 访问班级列表页面（指定课程）
        response = self.client.get(reverse("grading:class_list"), {"course_id": course.id})

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "计算机科学1班")
        self.assertContains(response, "计算机科学2班")

    def test_class_create_view_get(self):
        """测试班级创建视图 - GET请求"""
        # 创建测试课程
        course = Course.objects.create(
            teacher=self.teacher,
            name="数据结构",
            course_type="theory",
            semester=self.semester,
            tenant=self.tenant,
        )

        response = self.client.get(reverse("grading:class_create"))

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "创建班级")
        self.assertContains(response, "所属课程")
        self.assertContains(response, "数据结构")

    def test_class_create_view_post(self):
        """测试班级创建视图 - POST请求"""
        # 创建测试课程
        course = Course.objects.create(
            teacher=self.teacher,
            name="数据结构",
            course_type="theory",
            semester=self.semester,
            tenant=self.tenant,
        )

        # 发送创建班级请求
        response = self.client.post(
            reverse("grading:class_create"),
            {"course_id": course.id, "name": "软件工程1班", "student_count": "35"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("class_id", data)

        # 验证班级已创建
        class_obj = Class.objects.get(id=data["class_id"])
        self.assertEqual(class_obj.name, "软件工程1班")
        self.assertEqual(class_obj.student_count, 35)
        self.assertEqual(class_obj.course, course)

    def test_course_create_without_semester(self):
        """测试没有活跃学期时创建课程"""
        # 停用学期
        self.semester.is_active = False
        self.semester.save()

        # 尝试创建课程
        response = self.client.post(
            reverse("grading:course_create"),
            {
                "name": "计算机网络",
                "course_type": "theory",
                "description": "计算机网络课程",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("学期", data["message"])

    def test_class_create_invalid_course(self):
        """测试使用无效课程ID创建班级"""
        # 尝试使用不存在的课程ID创建班级
        response = self.client.post(
            reverse("grading:class_create"),
            {"course_id": "99999", "name": "测试班级", "student_count": "30"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("课程", data["message"])
