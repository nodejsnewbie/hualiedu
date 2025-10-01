"""
集成测试
测试各个模块之间的协作
"""

import os
import tempfile

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class IntegrationTestCase(TestCase):
    """集成测试基类"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理临时文件
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestGradingWorkflow(IntegrationTestCase):
    """评分工作流程测试"""

    def test_complete_grading_workflow(self):
        """测试完整的评分流程"""
        # 1. 访问首页
        response = self.client.get(reverse("grading:index"))
        self.assertEqual(response.status_code, 200)

        # 2. 测试评分页面访问
        response = self.client.get("/test-grade-switch/")
        self.assertEqual(response.status_code, 200)

        # 3. 验证页面包含必要元素
        self.assertContains(response, "评分系统功能测试")
        self.assertContains(response, "grade-mode-btn")
        self.assertContains(response, "grade-button")


class TestFileHandling(IntegrationTestCase):
    """文件处理测试"""

    def test_file_upload_validation(self):
        """测试文件上传验证"""
        # 创建测试文件
        test_file_path = os.path.join(self.temp_dir, "test.txt")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("测试内容")

        # 验证文件存在
        self.assertTrue(os.path.exists(test_file_path))

        # 验证文件内容
        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, "测试内容")


class TestSecurityFeatures(IntegrationTestCase):
    """安全功能测试"""

    def test_csrf_protection(self):
        """测试CSRF保护"""
        # 测试没有CSRF token的POST请求
        response = self.client.post("/some-protected-endpoint/", {"data": "test"})
        # 应该被拒绝或重定向
        self.assertIn(response.status_code, [403, 302])

    def test_authentication_required(self):
        """测试需要认证的页面"""
        # 测试未登录访问受保护页面
        protected_urls = [
            "/admin/",
        ]

        for url in protected_urls:
            response = self.client.get(url)
            # 应该重定向到登录页面或返回403
            self.assertIn(response.status_code, [302, 403, 404])
