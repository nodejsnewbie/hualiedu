"""
测试学生作业上传视图
"""

import io
import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from grading.models import Class, Course, Homework, Repository, Semester, Submission, Tenant


class HomeworkUploadViewsTest(TestCase):
    """测试学生作业上传视图"""

    def setUp(self):
        """设置测试环境"""
        # 创建租户
        self.tenant = Tenant.objects.create(name="测试学校", is_active=True)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=120)).date(),
            is_active=True,
        )

        # 创建教师用户
        self.teacher = User.objects.create_user(
            username="teacher1", password="password123", first_name="张", last_name="老师"
        )

        # 创建学生用户
        self.student = User.objects.create_user(
            username="student1", password="password123", first_name="李", last_name="同学"
        )

        # 创建课程
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="数据结构",
            course_type="theory",
            tenant=self.tenant,
        )

        # 创建班级
        self.class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        # 创建文件系统仓库
        self.repository = Repository.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            class_obj=self.class_obj,
            name="数据结构作业仓库",
            repo_type="filesystem",
            filesystem_path="teacher1_datastruct",
            allocated_space_mb=1024,
            is_active=True,
        )

        # 创建作业
        self.homework = Homework.objects.create(
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            title="第一次作业",
            homework_type="normal",
            folder_name="homework1",
            due_date=timezone.now() + timedelta(days=7),
        )

        # 创建客户端
        self.client = Client()

    def test_homework_upload_page_requires_login(self):
        """测试上传页面需要登录"""
        response = self.client.get(reverse("grading:homework_upload_page"))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_homework_upload_page_authenticated(self):
        """测试登录后可以访问上传页面"""
        self.client.login(username="student1", password="password123")
        response = self.client.get(reverse("grading:homework_upload_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "homework_upload.html")

    def test_get_student_homework_list(self):
        """测试获取学生作业列表"""
        self.client.login(username="student1", password="password123")
        response = self.client.get(reverse("grading:get_student_homework_list"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("homeworks", data)
        self.assertEqual(len(data["homeworks"]), 1)

        homework_data = data["homeworks"][0]
        self.assertEqual(homework_data["title"], "第一次作业")
        self.assertEqual(homework_data["homework_type"], "normal")
        self.assertEqual(homework_data["course_name"], "数据结构")
        self.assertEqual(homework_data["class_name"], "计算机1班")

    def test_upload_homework_success(self):
        """测试上传作业成功"""
        self.client.login(username="student1", password="password123")

        # 创建测试文件
        file_content = b"This is a test homework file"
        test_file = SimpleUploadedFile("homework1.docx", file_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        response = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": self.homework.id, "file": test_file},
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("submission", data)

        # 验证提交记录已创建
        submission = Submission.objects.filter(
            homework=self.homework, student=self.student
        ).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.version, 1)
        self.assertEqual(submission.file_name, "homework1.docx")

    def test_upload_homework_version_increment(self):
        """测试重复上传时版本号递增"""
        self.client.login(username="student1", password="password123")

        # 第一次上传
        file1 = SimpleUploadedFile("homework1_v1.docx", b"Version 1", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response1 = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": self.homework.id, "file": file1},
        )
        self.assertEqual(response1.status_code, 200)

        # 第二次上传
        file2 = SimpleUploadedFile("homework1_v2.docx", b"Version 2", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response2 = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": self.homework.id, "file": file2},
        )
        self.assertEqual(response2.status_code, 200)

        # 验证版本号
        submissions = Submission.objects.filter(
            homework=self.homework, student=self.student
        ).order_by("version")
        self.assertEqual(submissions.count(), 2)
        self.assertEqual(submissions[0].version, 1)
        self.assertEqual(submissions[1].version, 2)

    def test_upload_homework_missing_file(self):
        """测试上传时缺少文件"""
        self.client.login(username="student1", password="password123")

        response = self.client.post(
            reverse("grading:upload_homework"), {"homework_id": self.homework.id}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("未选择文件", data["message"])

    def test_upload_homework_invalid_format(self):
        """测试上传不支持的文件格式"""
        self.client.login(username="student1", password="password123")

        # 创建不支持的文件格式
        test_file = SimpleUploadedFile("homework.exe", b"Invalid file", content_type="application/x-msdownload")

        response = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": self.homework.id, "file": test_file},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("不支持的文件格式", data["message"])

    def test_upload_homework_overdue(self):
        """测试上传过期作业"""
        # 创建过期作业
        overdue_homework = Homework.objects.create(
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            title="过期作业",
            homework_type="normal",
            folder_name="homework_overdue",
            due_date=timezone.now() - timedelta(days=1),  # 昨天截止
        )

        self.client.login(username="student1", password="password123")

        test_file = SimpleUploadedFile("homework.docx", b"Test content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        response = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": overdue_homework.id, "file": test_file},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("已过期", data["message"])

    def test_get_submission_history(self):
        """测试获取提交历史"""
        self.client.login(username="student1", password="password123")

        # 创建几个提交记录
        for i in range(3):
            Submission.objects.create(
                tenant=self.tenant,
                homework=self.homework,
                student=self.student,
                repository=self.repository,
                file_path=f"/path/to/file_v{i+1}.docx",
                file_name=f"homework_v{i+1}.docx",
                file_size=1024 * (i + 1),
                version=i + 1,
            )

        response = self.client.get(
            reverse("grading:get_submission_history"),
            {"homework_id": self.homework.id},
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["submissions"]), 3)

        # 验证按版本号降序排列
        versions = [sub["version"] for sub in data["submissions"]]
        self.assertEqual(versions, [3, 2, 1])

    def test_upload_homework_git_repository(self):
        """测试Git仓库不支持上传"""
        # 创建Git仓库
        git_repo = Repository.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            class_obj=self.class_obj,
            name="Git仓库",
            repo_type="git",
            git_url="https://github.com/test/repo.git",
            is_active=True,
        )

        # 创建关联到Git仓库的作业
        git_homework = Homework.objects.create(
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            title="Git作业",
            homework_type="normal",
            folder_name="git_homework",
        )

        # 删除文件系统仓库，只保留Git仓库
        self.repository.delete()

        self.client.login(username="student1", password="password123")

        test_file = SimpleUploadedFile("homework.docx", b"Test content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        response = self.client.post(
            reverse("grading:upload_homework"),
            {"homework_id": git_homework.id, "file": test_file},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("没有配置文件系统仓库", data["message"])

    def tearDown(self):
        """清理测试环境"""
        # 清理创建的文件
        import shutil

        repo_path = self.repository.get_full_path()
        if repo_path and repo_path.startswith("/Users/") or repo_path.startswith("/tmp/"):
            try:
                import os

                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
            except Exception:
                pass
