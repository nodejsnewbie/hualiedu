"""
多租户管理视图
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .middleware import get_user_profile, get_user_tenant, require_superuser, require_tenant_admin
from .models import Tenant, TenantConfig, UserProfile

logger = logging.getLogger(__name__)


@login_required
@require_superuser
def super_admin_dashboard(request):
    """超级管理员仪表板"""
    try:
        tenants = Tenant.objects.all().order_by("-created_at")
        total_users = User.objects.count()
        active_tenants = tenants.filter(is_active=True).count()

        context = {
            "tenants": tenants,
            "total_users": total_users,
            "active_tenants": active_tenants,
        }

        return render(request, "super_admin_dashboard.html", context)

    except Exception as e:
        logger.error(f"超级管理员仪表板异常: {str(e)}")
        messages.error(request, "加载仪表板失败")
        return redirect("admin:index")


@login_required
@require_superuser
def tenant_management(request):
    """租户管理页面"""
    try:
        tenants = Tenant.objects.all().order_by("-created_at")

        context = {
            "tenants": tenants,
        }

        return render(request, "tenant_management.html", context)

    except Exception as e:
        logger.error(f"租户管理页面异常: {str(e)}")
        messages.error(request, "加载租户管理页面失败")
        return redirect("super_admin_dashboard")


@login_required
@require_superuser
@require_http_methods(["POST"])
def create_tenant(request):
    """创建租户"""
    try:
        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            return JsonResponse({"status": "error", "message": "租户名称不能为空"}, status=400)

        # 检查租户名称是否已存在
        if Tenant.objects.filter(name=name).exists():
            return JsonResponse({"status": "error", "message": "租户名称已存在"}, status=400)

        tenant = Tenant.objects.create(name=name, description=description, is_active=True)

        logger.info("超级管理员 %s 创建了租户: %s", request.user.username, tenant.name)

        return JsonResponse(
            {"status": "success", "message": f"租户 {tenant.name} 创建成功", "tenant_id": tenant.id}
        )

    except Exception as e:
        logger.error(f"创建租户异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "创建租户失败"}, status=500)


@login_required
@require_superuser
@require_http_methods(["POST"])
def update_tenant(request):
    """更新租户"""
    try:
        tenant_id = request.POST.get("tenant_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        is_active = request.POST.get("is_active", "true").lower() == "true"

        if not tenant_id or not name:
            return JsonResponse({"status": "error", "message": "缺少必要参数"}, status=400)

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return JsonResponse({"status": "error", "message": "租户不存在"}, status=404)

        # 检查名称是否与其他租户冲突
        if Tenant.objects.filter(name=name).exclude(id=tenant_id).exists():
            return JsonResponse({"status": "error", "message": "租户名称已存在"}, status=400)

        tenant.name = name
        tenant.description = description
        tenant.is_active = is_active
        tenant.save()

        logger.info(f"超级管理员 {request.user.username} 更新了租户: {tenant.name}")

        return JsonResponse({"status": "success", "message": f"租户 {tenant.name} 更新成功"})

    except Exception as e:
        logger.error(f"更新租户异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "更新租户失败"}, status=500)


@login_required
@require_tenant_admin
def tenant_admin_dashboard(request):
    """租户管理员仪表板"""
    try:
        tenant = get_user_tenant(request)
        profile = get_user_profile(request)

        # 获取租户统计信息
        user_count = UserProfile.objects.filter(tenant=tenant).count()
        repository_count = tenant.repositories.filter(is_active=True).count()

        context = {
            "tenant": tenant,
            "profile": profile,
            "user_count": user_count,
            "repository_count": repository_count,
        }

        return render(request, "tenant_admin_dashboard.html", context)

    except Exception as e:
        logger.error(f"租户管理员仪表板异常: {str(e)}")
        messages.error(request, "加载仪表板失败")
        return redirect("grading:index")


@login_required
@require_tenant_admin
def tenant_user_management(request):
    """租户用户管理"""
    try:
        tenant = get_user_tenant(request)
        users = (
            UserProfile.objects.filter(tenant=tenant).select_related("user").order_by("-created_at")
        )

        context = {
            "tenant": tenant,
            "users": users,
        }

        return render(request, "tenant_user_management.html", context)

    except Exception as e:
        logger.error(f"租户用户管理异常: {str(e)}")
        messages.error(request, "加载用户管理页面失败")
        return redirect("tenant_admin_dashboard")


@login_required
@require_tenant_admin
@require_http_methods(["POST"])
def add_user_to_tenant(request):
    """添加用户到租户"""
    try:
        tenant = get_user_tenant(request)
        username = request.POST.get("username")
        repo_base_dir = request.POST.get("repo_base_dir", "")
        is_tenant_admin = request.POST.get("is_tenant_admin", "false").lower() == "true"

        if not username:
            return JsonResponse({"status": "error", "message": "用户名不能为空"}, status=400)

        # 查找用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "用户不存在"}, status=404)

        # 检查用户是否已有配置文件
        if UserProfile.objects.filter(user=user).exists():
            return JsonResponse({"status": "error", "message": "用户已属于其他租户"}, status=400)

        # 创建用户配置文件
        profile = UserProfile.objects.create(
            user=user, tenant=tenant, repo_base_dir=repo_base_dir, is_tenant_admin=is_tenant_admin
        )

        logger.info(
            f"租户管理员 {request.user.username} 将用户 {username} 添加到租户 {tenant.name}"
        )

        return JsonResponse(
            {
                "status": "success",
                "message": f"用户 {username} 已添加到租户",
                "profile_id": profile.id,
            }
        )

    except Exception as e:
        logger.error(f"添加用户到租户异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "添加用户失败"}, status=500)


@login_required
@require_tenant_admin
@require_http_methods(["POST"])
def update_user_profile(request):
    """更新用户配置文件"""
    try:
        tenant = get_user_tenant(request)
        profile_id = request.POST.get("profile_id")
        repo_base_dir = request.POST.get("repo_base_dir", "")
        is_tenant_admin = request.POST.get("is_tenant_admin", "false").lower() == "true"

        if not profile_id:
            return JsonResponse({"status": "error", "message": "缺少必要参数"}, status=400)

        try:
            profile = UserProfile.objects.get(id=profile_id, tenant=tenant)
        except UserProfile.DoesNotExist:
            return JsonResponse({"status": "error", "message": "用户配置文件不存在"}, status=404)

        profile.repo_base_dir = repo_base_dir
        profile.is_tenant_admin = is_tenant_admin
        profile.save()

        logger.info(
            f"租户管理员 {request.user.username} 更新了用户 {profile.user.username} 的配置文件"
        )

        return JsonResponse({"status": "success", "message": "用户配置文件更新成功"})

    except Exception as e:
        logger.error(f"更新用户配置文件异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "更新用户配置文件失败"}, status=500)


@login_required
@require_tenant_admin
@require_http_methods(["POST"])
def remove_user_from_tenant(request):
    """从租户移除用户"""
    try:
        tenant = get_user_tenant(request)
        profile_id = request.POST.get("profile_id")

        if not profile_id:
            return JsonResponse({"status": "error", "message": "缺少必要参数"}, status=400)

        try:
            profile = UserProfile.objects.get(id=profile_id, tenant=tenant)
        except UserProfile.DoesNotExist:
            return JsonResponse({"status": "error", "message": "用户配置文件不存在"}, status=404)

        # 不能移除自己
        if profile.user == request.user:
            return JsonResponse({"status": "error", "message": "不能移除自己"}, status=400)

        username = profile.user.username
        profile.delete()

        logger.info(
            f"租户管理员 {request.user.username} 从租户 {tenant.name} 移除了用户 {username}"
        )

        return JsonResponse({"status": "success", "message": f"用户 {username} 已从租户移除"})

    except Exception as e:
        logger.error(f"从租户移除用户异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "移除用户失败"}, status=500)


@login_required
@require_tenant_admin
def tenant_config_management(request):
    """租户配置管理"""
    try:
        tenant = get_user_tenant(request)
        configs = TenantConfig.objects.filter(tenant=tenant).order_by("key")

        context = {
            "tenant": tenant,
            "configs": configs,
        }

        return render(request, "tenant_config_management.html", context)

    except Exception as e:
        logger.error(f"租户配置管理异常: {str(e)}")
        messages.error(request, "加载配置管理页面失败")
        return redirect("tenant_admin_dashboard")


@login_required
@require_tenant_admin
@require_http_methods(["POST"])
def update_tenant_config(request):
    """更新租户配置"""
    try:
        tenant = get_user_tenant(request)
        key = request.POST.get("key")
        value = request.POST.get("value", "")
        description = request.POST.get("description", "")

        if not key:
            return JsonResponse({"status": "error", "message": "配置键不能为空"}, status=400)

        TenantConfig.set_value(tenant, key, value, description)

        logger.info(f"租户管理员 {request.user.username} 更新了租户 {tenant.name} 的配置: {key}")

        return JsonResponse({"status": "success", "message": f"配置 {key} 更新成功"})

    except Exception as e:
        logger.error(f"更新租户配置异常: {str(e)}")
        return JsonResponse({"status": "error", "message": "更新配置失败"}, status=500)
