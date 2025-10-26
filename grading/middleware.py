"""
多租户中间件
负责处理租户隔离和用户权限
"""

import logging

from django.http import JsonResponse

from .models import Tenant, UserProfile

logger = logging.getLogger(__name__)


class MultiTenantMiddleware:
    """多租户中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 处理请求前的逻辑
        self.process_request(request)

        response = self.get_response(request)

        # 处理响应后的逻辑
        return self.process_response(request, response)

    def process_request(self, request):
        """处理请求"""
        if not request.user.is_authenticated:
            return

        # 获取或创建用户配置文件
        try:
            profile = UserProfile.objects.get(user=request.user)
            request.tenant = profile.tenant
            request.user_profile = profile
        except UserProfile.DoesNotExist:
            # 如果用户没有配置文件，创建默认租户和配置文件
            self.create_default_tenant_and_profile(request.user)
            profile = UserProfile.objects.get(user=request.user)
            request.tenant = profile.tenant
            request.user_profile = profile

    def process_response(self, request, response):
        """处理响应"""
        return response

    def create_default_tenant_and_profile(self, user):
        """为用户创建默认租户和配置文件"""
        try:
            # 创建默认租户
            tenant, created = Tenant.objects.get_or_create(
                name=f"default-{user.username}",
                defaults={"description": f"用户 {user.username} 的默认租户", "is_active": True},
            )

            # 创建用户配置文件
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "tenant": tenant,
                    "is_tenant_admin": True,
                },
            )

            logger.info(f"为用户 {user.username} 创建了默认租户和配置文件")

        except Exception as e:
            logger.error(f"创建默认租户和配置文件失败: {e}")


def require_tenant_admin(view_func):
    """要求租户管理员权限的装饰器"""

    def wrapper(request, *args, **kwargs):
        if not hasattr(request, "user_profile"):
            return JsonResponse({"status": "error", "message": "用户配置文件不存在"}, status=403)

        if not request.user_profile.is_tenant_admin:
            return JsonResponse({"status": "error", "message": "需要租户管理员权限"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper


def require_superuser(view_func):
    """要求超级用户权限的装饰器"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({"status": "error", "message": "需要超级用户权限"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper


def get_user_tenant(request):
    """获取用户的租户"""
    if hasattr(request, "tenant"):
        return request.tenant
    return None


def get_user_profile(request):
    """获取用户配置文件"""
    if hasattr(request, "user_profile"):
        return request.user_profile
    return None


def get_tenant_repo_base_dir(request):
    """获取租户的基础仓库目录"""
    profile = get_user_profile(request)
    if profile and profile.tenant:
        return profile.tenant.get_full_repo_path()
    return None
