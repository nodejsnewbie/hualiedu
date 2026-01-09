"""
中间件测试
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser, User
from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from grading.middleware import (
    MultiTenantMiddleware,
    get_tenant_repo_base_dir,
    get_user_profile,
    get_user_tenant,
    require_superuser,
    require_tenant_admin,
)
from grading.models import Tenant, UserProfile

from .base import BaseTestCase


class MultiTenantMiddlewareTest(BaseTestCase):
    """多租户中间件测试"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.middleware = MultiTenantMiddleware(lambda request: None)

        # 创建测试租户
        self.tenant = Tenant.objects.create(name="测试租户", description="测试用租户")

        # 创建用户配置文件
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/repo", is_tenant_admin=True
        )

    def test_process_request_authenticated_user_with_profile(self):
        """测试已认证用户且有配置文件的请求处理"""
        request = self.factory.get("/")
        request.user = self.user

        self.middleware.process_request(request)

        self.assertEqual(request.tenant, self.tenant)
        self.assertEqual(request.user_profile, self.user_profile)

    def test_process_request_authenticated_user_without_profile(self):
        """测试已认证用户但无配置文件的请求处理"""
        # 删除现有配置文件
        UserProfile.objects.filter(user=self.user).delete()

        request = self.factory.get("/")
        request.user = self.user

        self.middleware.process_request(request)

        # 应该自动创建配置文件
        self.assertTrue(hasattr(request, "tenant"))
        self.assertTrue(hasattr(request, "user_profile"))

        # 验证创建的配置文件
        profile = UserProfile.objects.get(user=self.user)
        self.assertTrue(profile.is_tenant_admin)
        self.assertIn(self.user.username, profile.tenant.name)

    def test_process_request_anonymous_user(self):
        """测试匿名用户的请求处理"""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        result = self.middleware.process_request(request)

        # 匿名用户不应该设置租户信息
        self.assertFalse(hasattr(request, "tenant"))
        self.assertFalse(hasattr(request, "user_profile"))
        self.assertIsNone(result)

    def test_process_response(self):
        """测试响应处理"""
        request = self.factory.get("/")
        response = MagicMock()

        result = self.middleware.process_response(request, response)

        self.assertEqual(result, response)

    @patch("grading.middleware.logger")
    def test_create_default_tenant_and_profile_success(self, mock_logger):
        """测试成功创建默认租户和配置文件"""
        # 确保用户没有配置文件
        UserProfile.objects.filter(user=self.user).delete()

        self.middleware.create_default_tenant_and_profile(self.user)

        # 验证创建的租户
        tenant = Tenant.objects.get(name=f"default-{self.user.username}")
        self.assertTrue(tenant.is_active)
        self.assertIn(self.user.username, tenant.description)

        # 验证创建的配置文件
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.tenant, tenant)
        self.assertTrue(profile.is_tenant_admin)
        self.assertIn(self.user.username, profile.repo_base_dir)

        # 验证日志记录
        mock_logger.info.assert_called_once()

    @patch("grading.middleware.logger")
    def test_create_default_tenant_and_profile_exception(self, mock_logger):
        """测试创建默认租户和配置文件时发生异常"""
        with patch(
            "grading.models.Tenant.objects.get_or_create", side_effect=Exception("Database error")
        ):
            self.middleware.create_default_tenant_and_profile(self.user)

            # 验证错误日志记录
            mock_logger.error.assert_called_once()

    def test_middleware_call(self):
        """测试中间件调用"""
        request = self.factory.get("/")
        request.user = self.user

        # 模拟get_response函数
        def mock_get_response(req):
            return MagicMock()

        middleware = MultiTenantMiddleware(mock_get_response)
        response = middleware(request)

        # 验证请求被正确处理
        self.assertTrue(hasattr(request, "tenant"))
        self.assertTrue(hasattr(request, "user_profile"))
        self.assertIsNotNone(response)


class DecoratorTest(BaseTestCase):
    """装饰器测试"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建普通用户配置文件
        self.normal_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, is_tenant_admin=False
        )

        # 创建管理员用户配置文件
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, tenant=self.tenant, is_tenant_admin=True
        )

    def test_require_tenant_admin_with_admin_user(self):
        """测试租户管理员装饰器（管理员用户）"""

        @require_tenant_admin
        def test_view(request):
            return JsonResponse({"status": "success"})

        request = self.factory.get("/")
        request.user = self.admin_user
        request.user_profile = self.admin_profile

        response = test_view(request)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_require_tenant_admin_with_normal_user(self):
        """测试租户管理员装饰器（普通用户）"""

        @require_tenant_admin
        def test_view(request):
            return JsonResponse({"status": "success"})

        request = self.factory.get("/")
        request.user = self.user
        request.user_profile = self.normal_profile

        response = test_view(request)

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("租户管理员权限", data["message"])

    def test_require_tenant_admin_without_profile(self):
        """测试租户管理员装饰器（无配置文件）"""

        @require_tenant_admin
        def test_view(request):
            return JsonResponse({"status": "success"})

        request = self.factory.get("/")
        request.user = self.user
        # 不设置user_profile

        response = test_view(request)

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("用户配置文件不存在", data["message"])

    def test_require_superuser_with_superuser(self):
        """测试超级用户装饰器（超级用户）"""

        @require_superuser
        def test_view(request):
            return JsonResponse({"status": "success"})

        request = self.factory.get("/")
        request.user = self.admin_user  # admin_user是超级用户

        response = test_view(request)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_require_superuser_with_normal_user(self):
        """测试超级用户装饰器（普通用户）"""

        @require_superuser
        def test_view(request):
            return JsonResponse({"status": "success"})

        request = self.factory.get("/")
        request.user = self.user  # 普通用户

        response = test_view(request)

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("超级用户权限", data["message"])


class HelperFunctionTest(BaseTestCase):
    """辅助函数测试"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/repo"
        )

    def test_get_user_tenant_with_tenant(self):
        """测试获取用户租户（有租户）"""
        request = self.factory.get("/")
        request.tenant = self.tenant

        result = get_user_tenant(request)

        self.assertEqual(result, self.tenant)

    def test_get_user_tenant_without_tenant(self):
        """测试获取用户租户（无租户）"""
        request = self.factory.get("/")
        # 不设置tenant属性

        result = get_user_tenant(request)

        self.assertIsNone(result)

    def test_get_user_profile_with_profile(self):
        """测试获取用户配置文件（有配置文件）"""
        request = self.factory.get("/")
        request.user_profile = self.user_profile

        result = get_user_profile(request)

        self.assertEqual(result, self.user_profile)

    def test_get_user_profile_without_profile(self):
        """测试获取用户配置文件（无配置文件）"""
        request = self.factory.get("/")
        # 不设置user_profile属性

        result = get_user_profile(request)

        self.assertIsNone(result)

    def test_get_tenant_repo_base_dir_with_profile(self):
        """测试获取租户仓库基础目录（有配置文件）"""
        request = self.factory.get("/")
        request.user_profile = self.user_profile

        result = get_tenant_repo_base_dir(request)

        self.assertEqual(result, "/test/repo")

    def test_get_tenant_repo_base_dir_without_profile(self):
        """测试获取租户仓库基础目录（无配置文件）"""
        request = self.factory.get("/")
        # 不设置user_profile属性

        result = get_tenant_repo_base_dir(request)

        self.assertIsNone(result)

    def test_get_tenant_repo_base_dir_with_custom_method(self):
        """测试获取租户仓库基础目录（自定义方法）"""
        # 模拟用户配置文件有自定义的get_repo_base_dir方法
        mock_profile = MagicMock()
        mock_profile.get_repo_base_dir.return_value = "/custom/repo/path"

        request = self.factory.get("/")
        request.user_profile = mock_profile

        result = get_tenant_repo_base_dir(request)

        self.assertEqual(result, "/custom/repo/path")
        mock_profile.get_repo_base_dir.assert_called_once()


class MiddlewareIntegrationTest(BaseTestCase):
    """中间件集成测试"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_full_middleware_workflow(self):
        """测试完整的中间件工作流程"""
        # 创建一个新用户（没有配置文件）
        new_user = User.objects.create_user(username="newuser", password="testpass123")

        # 创建中间件
        def mock_get_response(request):
            # 验证中间件设置的属性
            self.assertTrue(hasattr(request, "tenant"))
            self.assertTrue(hasattr(request, "user_profile"))
            return MagicMock()

        middleware = MultiTenantMiddleware(mock_get_response)

        # 创建请求
        request = self.factory.get("/")
        request.user = new_user

        # 处理请求
        response = middleware(request)

        # 验证自动创建的租户和配置文件
        tenant = Tenant.objects.get(name=f"default-{new_user.username}")
        profile = UserProfile.objects.get(user=new_user)

        self.assertEqual(profile.tenant, tenant)
        self.assertTrue(profile.is_tenant_admin)
        self.assertIsNotNone(response)

    def test_middleware_with_existing_profile(self):
        """测试中间件处理已有配置文件的用户"""
        # 创建租户和配置文件
        tenant = Tenant.objects.create(name="现有租户")
        profile = UserProfile.objects.create(
            user=self.user, tenant=tenant, repo_base_dir="/existing/repo"
        )

        def mock_get_response(request):
            self.assertEqual(request.tenant, tenant)
            self.assertEqual(request.user_profile, profile)
            return MagicMock()

        middleware = MultiTenantMiddleware(mock_get_response)

        request = self.factory.get("/")
        request.user = self.user

        response = middleware(request)

        self.assertIsNotNone(response)
