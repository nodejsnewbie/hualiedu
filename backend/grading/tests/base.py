"""
测试基类和通用工具
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase


class BaseTestCase(TestCase):
    """基础测试类，提供通用的测试设置"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 创建临时媒体目录
        cls.temp_media_root = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # 清理临时媒体目录
        if hasattr(cls, "temp_media_root") and os.path.exists(cls.temp_media_root):
            shutil.rmtree(cls.temp_media_root)

    def setUp(self):
        """每个测试方法执行前的设置"""
        self.client = Client()
        self.create_test_users()
        self.create_test_data()

    def create_test_users(self):
        """创建测试用户"""
        # 创建普通用户
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="测试",
            last_name="用户",
        )

        # 创建管理员用户
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            first_name="管理员",
            last_name="用户",
        )

        # 创建教师用户
        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="teacherpass123",
            first_name="教师",
            last_name="用户",
        )

    def create_test_data(self):
        """创建测试数据"""
        pass  # 子类可以重写此方法

    def login_user(self, user=None):
        """登录用户"""
        if user is None:
            user = self.user
        self.client.force_login(user)
        return user

    def logout_user(self):
        """登出用户"""
        self.client.logout()

    def create_test_file(self, filename="test.txt", content="测试内容"):
        """创建测试文件"""
        return SimpleUploadedFile(filename, content.encode("utf-8"), content_type="text/plain")

    def create_test_docx_file(self, filename="test.docx"):
        """创建测试Word文档"""
        # 简单的docx文件内容（实际应用中可能需要更复杂的文档）
        content = b"PK\x03\x04" + b"\x00" * 100  # 简化的docx文件头
        return SimpleUploadedFile(
            filename,
            content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def assertResponseOK(self, response):
        """断言响应成功"""
        self.assertEqual(response.status_code, 200)

    def assertResponseRedirect(self, response, expected_url=None):
        """断言响应重定向"""
        self.assertIn(response.status_code, [301, 302])
        if expected_url:
            self.assertRedirects(response, expected_url)

    def assertResponseForbidden(self, response):
        """断言响应被禁止"""
        self.assertEqual(response.status_code, 403)

    def assertResponseNotFound(self, response):
        """断言响应未找到"""
        self.assertEqual(response.status_code, 404)


class APITestCase(BaseTestCase):
    """API测试基类"""

    def setUp(self):
        super().setUp()
        self.api_client = Client()

    def api_get(self, url, data=None, **extra):
        """API GET请求"""
        return self.api_client.get(url, data, **extra)

    def api_post(self, url, data=None, **extra):
        """API POST请求"""
        return self.api_client.post(url, data, **extra)

    def api_put(self, url, data=None, **extra):
        """API PUT请求"""
        return self.api_client.put(url, data, **extra)

    def api_delete(self, url, **extra):
        """API DELETE请求"""
        return self.api_client.delete(url, **extra)

    def assertJSONResponse(self, response, expected_data=None):
        """断言JSON响应"""
        self.assertEqual(response["Content-Type"], "application/json")
        if expected_data:
            self.assertEqual(response.json(), expected_data)


class MockTestCase(BaseTestCase):
    """带Mock功能的测试基类"""

    def setUp(self):
        super().setUp()
        self.patches = []

    def tearDown(self):
        """清理所有的mock"""
        for patcher in self.patches:
            patcher.stop()
        super().tearDown()

    def mock_volcengine_api(self, return_value=None, side_effect=None):
        """Mock火山引擎API"""
        if return_value is None:
            return_value = (85, "评分：85分。内容充实，结构清晰。")

        patcher = patch("grading.views.volcengine_score_homework")
        mock_func = patcher.start()

        if side_effect:
            mock_func.side_effect = side_effect
        else:
            mock_func.return_value = return_value

        self.patches.append(patcher)
        return mock_func

    def mock_file_operations(self):
        """Mock文件操作"""
        patcher = patch("builtins.open")
        mock_open = patcher.start()
        self.patches.append(patcher)
        return mock_open


class DatabaseTestCase(TransactionTestCase):
    """数据库事务测试基类"""

    def setUp(self):
        super().setUp()
        self.client = Client()

    def create_test_user(self):
        """创建测试用户"""
        return User.objects.create_user(username="dbtest", password="testpass123")
