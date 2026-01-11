"""
班级管理服务测试模块

测试班级管理服务的创建、查询和管理功能
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from grading.models import Class, Course, Semester, Submission, Tenant
from grading.services.class_service import ClassService


class ClassServiceTest(TestCase):
    """班级管理服务测试类"""

    def setUp(self):
        """设置测试数据"""
        self.service = ClassService()

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

        # 创建课程
        self.course1 = Course.objects.create(
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            semester=self.semester1,
            tenant=self.tenant1,
        )
        self.course2 = Course.objects.create(
            teacher=self.teacher2,
            name="操作系统",
            course_type="lab",
            semester=self.semester1,
            tenant=self.tenant2,
        )

    def test_create_class_success(self):
        """测试成功创建班级"""
        class_obj = self.service.create_class(
            course=self.course1, name="计算机科学1班", student_count=30, tenant=self.tenant1
        )

        # 验证班级创建成功
        self.assertIsNotNone(class_obj)
        self.assertEqual(class_obj.name, "计算机科学1班")
        self.assertEqual(class_obj.student_count, 30)
        self.assertEqual(class_obj.course, self.course1)
        self.assertEqual(class_obj.tenant, self.tenant1)

        # 验证数据库中存在该班级
        self.assertTrue(Class.objects.filter(id=class_obj.id).exists())

    def test_create_class_auto_tenant(self):
        """测试自动从课程获取租户"""
        class_obj = self.service.create_class(course=self.course1, name="计算机科学2班")

        # 验证租户自动设置
        self.assertEqual(class_obj.tenant, self.tenant1)

    def test_create_class_default_student_count(self):
        """测试默认学生人数为0"""
        class_obj = self.service.create_class(course=self.course1, name="计算机科学3班")

        # 验证默认学生人数
        self.assertEqual(class_obj.student_count, 0)

    def test_create_class_no_course(self):
        """测试创建班级时没有课程"""
        with self.assertRaises(ValueError) as context:
            self.service.create_class(course=None, name="测试班级", tenant=self.tenant1)

        self.assertIn("必须指定所属课程", str(context.exception))

    def test_create_class_empty_name(self):
        """测试创建班级时名称为空"""
        with self.assertRaises(ValueError) as context:
            self.service.create_class(course=self.course1, name="   ", tenant=self.tenant1)

        self.assertIn("班级名称不能为空", str(context.exception))

    def test_create_class_negative_student_count(self):
        """测试创建班级时学生人数为负数"""
        with self.assertRaises(ValueError) as context:
            self.service.create_class(
                course=self.course1, name="测试班级", student_count=-5, tenant=self.tenant1
            )

        self.assertIn("学生人数不能为负数", str(context.exception))

    def test_create_class_tenant_mismatch(self):
        """测试课程和班级租户不一致"""
        with self.assertRaises(ValueError) as context:
            self.service.create_class(
                course=self.course1, name="测试班级", tenant=self.tenant2  # course1属于tenant1
            )

        self.assertIn("课程和班级必须属于同一租户", str(context.exception))

    def test_list_classes_all(self):
        """测试列出所有班级"""
        # 创建多个班级
        class1 = self.service.create_class(course=self.course1, name="计算机科学1班")
        class2 = self.service.create_class(course=self.course1, name="计算机科学2班")
        class3 = self.service.create_class(course=self.course2, name="软件工程1班")

        # 列出所有班级
        all_classes = self.service.list_classes()

        # 验证返回所有班级
        self.assertEqual(len(all_classes), 3)
        class_ids = [c.id for c in all_classes]
        self.assertIn(class1.id, class_ids)
        self.assertIn(class2.id, class_ids)
        self.assertIn(class3.id, class_ids)

    def test_list_classes_by_course(self):
        """测试按课程过滤班级"""
        # 创建多个班级
        class1 = self.service.create_class(course=self.course1, name="计算机科学1班")
        class2 = self.service.create_class(course=self.course1, name="计算机科学2班")
        class3 = self.service.create_class(course=self.course2, name="软件工程1班")

        # 列出course1的班级
        course1_classes = self.service.list_classes(course=self.course1)

        # 验证只返回course1的班级
        self.assertEqual(len(course1_classes), 2)
        class_ids = [c.id for c in course1_classes]
        self.assertIn(class1.id, class_ids)
        self.assertIn(class2.id, class_ids)
        self.assertNotIn(class3.id, class_ids)

    def test_list_classes_by_tenant(self):
        """测试按租户过滤班级"""
        # 创建多个班级
        class1 = self.service.create_class(course=self.course1, name="计算机科学1班")
        class2 = self.service.create_class(course=self.course2, name="软件工程1班")

        # 列出tenant1的班级
        tenant1_classes = self.service.list_classes(tenant=self.tenant1)

        # 验证只返回tenant1的班级
        self.assertEqual(len(tenant1_classes), 1)
        self.assertEqual(tenant1_classes[0].id, class1.id)

        # 列出tenant2的班级
        tenant2_classes = self.service.list_classes(tenant=self.tenant2)

        # 验证只返回tenant2的班级
        self.assertEqual(len(tenant2_classes), 1)
        self.assertEqual(tenant2_classes[0].id, class2.id)

    def test_list_classes_ordering(self):
        """测试班级列表排序"""
        # 创建多个班级
        class1 = self.service.create_class(course=self.course1, name="B班")
        class2 = self.service.create_class(course=self.course1, name="A班")
        class3 = self.service.create_class(course=self.course1, name="C班")

        # 获取班级列表
        classes = self.service.list_classes(course=self.course1)

        # 验证排序：按课程名称和班级名称
        self.assertEqual(len(classes), 3)
        self.assertEqual(classes[0].name, "A班")
        self.assertEqual(classes[1].name, "B班")
        self.assertEqual(classes[2].name, "C班")

    def test_get_class_students_empty(self):
        """测试获取班级学生列表（无学生）"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 获取学生列表
        students = self.service.get_class_students(class_obj.id)

        # 验证返回空列表
        self.assertEqual(len(students), 0)

    def test_get_class_students_with_submissions(self):
        """测试获取班级学生列表（有提交记录）"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 创建作业
        from grading.models import Homework

        homework = Homework.objects.create(
            course=self.course1,
            class_obj=class_obj,
            title="第一次作业",
            folder_name="homework1",
            tenant=self.tenant1,
        )

        # 创建学生用户
        student1 = User.objects.create_user(username="student1", password="testpass123")
        student2 = User.objects.create_user(username="student2", password="testpass123")
        student3 = User.objects.create_user(username="student3", password="testpass123")

        # 创建提交记录
        Submission.objects.create(
            homework=homework,
            student=student1,
            file_path="/path/to/file1",
            file_name="file1.docx",
            tenant=self.tenant1,
        )
        Submission.objects.create(
            homework=homework,
            student=student2,
            file_path="/path/to/file2",
            file_name="file2.docx",
            tenant=self.tenant1,
        )
        # student3提交两次
        Submission.objects.create(
            homework=homework,
            student=student3,
            file_path="/path/to/file3",
            file_name="file3.docx",
            tenant=self.tenant1,
        )
        Submission.objects.create(
            homework=homework,
            student=student3,
            file_path="/path/to/file3_v2",
            file_name="file3_v2.docx",
            tenant=self.tenant1,
        )

        # 获取学生列表
        students = self.service.get_class_students(class_obj.id)

        # 验证返回3个学生（去重）
        self.assertEqual(len(students), 3)
        student_ids = [s.id for s in students]
        self.assertIn(student1.id, student_ids)
        self.assertIn(student2.id, student_ids)
        self.assertIn(student3.id, student_ids)

    def test_get_class_by_id_success(self):
        """测试根据ID获取班级"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 获取班级
        retrieved_class = self.service.get_class_by_id(class_obj.id)

        # 验证获取成功
        self.assertEqual(retrieved_class.id, class_obj.id)
        self.assertEqual(retrieved_class.name, "计算机科学1班")

    def test_get_class_by_id_not_found(self):
        """测试获取不存在的班级"""
        with self.assertRaises(Class.DoesNotExist):
            self.service.get_class_by_id(99999)

    def test_get_classes_by_course(self):
        """测试获取指定课程的所有班级"""
        # 创建多个班级
        class1 = self.service.create_class(course=self.course1, name="计算机科学1班")
        class2 = self.service.create_class(course=self.course1, name="计算机科学2班")
        class3 = self.service.create_class(course=self.course2, name="软件工程1班")

        # 获取course1的班级
        course1_classes = self.service.get_classes_by_course(self.course1)

        # 验证返回course1的班级
        self.assertEqual(len(course1_classes), 2)
        class_ids = [c.id for c in course1_classes]
        self.assertIn(class1.id, class_ids)
        self.assertIn(class2.id, class_ids)
        self.assertNotIn(class3.id, class_ids)

    def test_update_class_name(self):
        """测试更新班级名称"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 更新名称
        updated_class = self.service.update_class(class_obj.id, name="计算机科学A班")

        # 验证更新成功
        self.assertEqual(updated_class.name, "计算机科学A班")

        # 验证数据库中已更新
        class_obj.refresh_from_db()
        self.assertEqual(class_obj.name, "计算机科学A班")

    def test_update_class_student_count(self):
        """测试更新班级学生人数"""
        # 创建班级
        class_obj = self.service.create_class(
            course=self.course1, name="计算机科学1班", student_count=30
        )

        # 更新学生人数
        updated_class = self.service.update_class(class_obj.id, student_count=35)

        # 验证更新成功
        self.assertEqual(updated_class.student_count, 35)

        # 验证数据库中已更新
        class_obj.refresh_from_db()
        self.assertEqual(class_obj.student_count, 35)

    def test_update_class_multiple_fields(self):
        """测试同时更新多个字段"""
        # 创建班级
        class_obj = self.service.create_class(
            course=self.course1, name="计算机科学1班", student_count=30
        )

        # 同时更新名称和学生人数
        updated_class = self.service.update_class(
            class_obj.id, name="计算机科学A班", student_count=35
        )

        # 验证更新成功
        self.assertEqual(updated_class.name, "计算机科学A班")
        self.assertEqual(updated_class.student_count, 35)

    def test_update_class_empty_name(self):
        """测试更新班级时名称为空"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 尝试设置空名称
        with self.assertRaises(ValueError) as context:
            self.service.update_class(class_obj.id, name="   ")

        self.assertIn("班级名称不能为空", str(context.exception))

    def test_update_class_negative_student_count(self):
        """测试更新班级时学生人数为负数"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        # 尝试设置负数学生人数
        with self.assertRaises(ValueError) as context:
            self.service.update_class(class_obj.id, student_count=-5)

        self.assertIn("学生人数不能为负数", str(context.exception))

    def test_delete_class_success(self):
        """测试删除班级"""
        # 创建班级
        class_obj = self.service.create_class(course=self.course1, name="计算机科学1班")

        class_id = class_obj.id

        # 删除班级
        self.service.delete_class(class_id)

        # 验证班级已删除
        self.assertFalse(Class.objects.filter(id=class_id).exists())

    def test_delete_class_not_found(self):
        """测试删除不存在的班级"""
        with self.assertRaises(Class.DoesNotExist):
            self.service.delete_class(99999)
