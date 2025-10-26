import logging
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse, urlunparse

import git
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Assignment,
    Course,
    GlobalConfig,
    GradeTypeConfig,
    Repository,
    Semester,
    Student,
    Submission,
    Tenant,
    TenantConfig,
    UserProfile,
)

# 获取日志记录器
logger = logging.getLogger(__name__)


# 定义所有 Admin 类
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_id", "name", "class_name"]
    search_fields = ["student_id", "name", "class_name"]
    list_filter = ["class_name"]


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "due_date", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["due_date", "created_at"]
    date_hierarchy = "due_date"


class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "repository",
        "submitted_at",
        "grade",
        "graded_at",
        "teacher_comment_action",
    ]
    search_fields = ["file_name", "repository__name"]
    list_filter = ["submitted_at", "graded_at", "repository"]
    date_hierarchy = "submitted_at"
    raw_id_fields = ["repository"]

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "teacher_comment/<int:submission_id>/",
                admin.site.admin_view(self.teacher_comment_view),
                name="grading_submission_teacher_comment",
            ),
        ]
        return custom_urls + urls

    def teacher_comment_action(self, obj):
        return format_html(
            '<a class="button" href="{}">教师评价</a>',
            reverse("admin:grading_submission_teacher_comment", args=[obj.pk]),
        )

    teacher_comment_action.short_description = "教师评价"
    teacher_comment_action.allow_tags = True

    def teacher_comment_view(self, request, submission_id):
        from django import forms
        from django.shortcuts import get_object_or_404, redirect

        submission = get_object_or_404(Submission, pk=submission_id)

        class TeacherCommentForm(forms.Form):
            comment = forms.CharField(
                label="教师评价",
                widget=forms.Textarea(attrs={"rows": 5, "style": "width: 90%;"}),
                required=True,
            )

        if request.method == "POST":
            form = TeacherCommentForm(request.POST)
            if form.is_valid():
                new_comment = form.cleaned_data["comment"]
                # 追加到原有内容末尾
                if submission.teacher_comments:
                    submission.teacher_comments += "\n" + new_comment
                else:
                    submission.teacher_comments = new_comment
                submission.save()
                self.message_user(request, "教师评价已保存！")
                return redirect("admin:grading_submission_changelist")
        else:
            form = TeacherCommentForm(initial={"comment": ""})

        context = dict(
            admin.site.each_context(request),
            title="教师评价",
            submission=submission,
            form=form,
        )
        return render(request, "admin/grading/submission/teacher_comment.html", context)


class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # 添加评分系统链接
        app_list.append(
            {
                "name": "评分系统",
                "app_label": "grading_system",
                "url": "/grading/",
                "has_module_perms": True,
                "models": [],
            }
        )
        return app_list


# 创建自定义 AdminSite 实例
admin_site = CustomAdminSite(name="admin")


class SSHKeyFileInput(forms.ClearableFileInput):
    template_name = "django/forms/widgets/clearable_file_input.html"

    class Media:
        css = {"all": ("grading/admin/css/grading_ssh_key_input.css",)}
        js = ("grading/admin/js/grading_ssh_key_input.js",)

    def __init__(self, attrs=None):
        default_attrs = {"accept": "*", "class": "ssh-key-file-input", "type": "file"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        return format_html(
            '<div class="ssh-key-file-input-wrapper">'
            '<button type="button" class="button select-ssh-key">上传 SSH 私钥文件</button>'
            '<span class="ssh-key-file-name"></span>'
            "{}</div>",
            html,
        )


class SSHKeyFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = SSHKeyFileInput()

    def clean(self, value, initial):
        if value:
            # 读取上传的文件内容
            content = value.read().decode("utf-8")
            # 验证 SSH 密钥格式
            if not (
                content.strip().startswith("-----BEGIN")
                and content.strip().endswith("PRIVATE KEY-----")
            ):
                raise forms.ValidationError(
                    "无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件"
                )
            # 将文件内容保存到 ssh_key 字段
            if hasattr(self, "parent") and hasattr(self.parent, "instance"):
                self.parent.instance.ssh_key = content
        return value


class GlobalConfigForm(forms.ModelForm):
    """全局配置表单"""

    class Meta:
        model = GlobalConfig
        fields = ("key", "value", "description")
        widgets = {
            "key": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "配置键，如：default_repo_base_dir",
                }
            ),
            "value": forms.Textarea(
                attrs={
                    "rows": 5,
                    "cols": 80,
                    "class": "vLargeTextField",
                    "style": "width: 100%;",
                    "placeholder": "配置值",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "配置描述",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置默认值
        if not self.instance.pk:
            self.initial["key"] = "default_repo_base_dir"
            self.initial["value"] = "~/jobs"
            self.initial["description"] = "默认仓库基础目录"


@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    """全局配置管理界面"""

    form = GlobalConfigForm
    list_display = ("key", "value", "description", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "配置信息",
            {
                "fields": ("key", "value", "description"),
                "description": "配置全局系统参数。",
            },
        ),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    search_fields = ("key", "value", "description")
    list_filter = ("updated_at",)
    ordering = ("-updated_at",)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """租户管理界面"""

    list_display = ("name", "description", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户配置文件管理界面"""

    list_display = ("user", "tenant", "is_tenant_admin", "created_at")
    list_filter = ("tenant", "is_tenant_admin", "created_at")
    search_fields = ("user__username", "user__email", "tenant__name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    """租户配置管理界面"""

    list_display = ("tenant", "key", "get_value_display", "description", "updated_at")
    list_filter = ("tenant", "key", "created_at")
    search_fields = ("tenant__name", "key", "description")
    ordering = ("tenant", "key")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'key', 'value', 'description')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_value_display(self, obj):
        """显示配置值，隐藏敏感信息"""
        sensitive_keys = ['password', 'key', 'token', 'passphrase']
        if any(keyword in obj.key.lower() for keyword in sensitive_keys):
            return "***" if obj.value else "(未设置)"
        return obj.value[:50] + "..." if len(obj.value) > 50 else obj.value
    
    get_value_display.short_description = "配置值"
    
    def get_form(self, request, obj=None, **kwargs):
        """自定义表单"""
        form = super().get_form(request, obj, **kwargs)
        
        # 为敏感字段使用密码输入框
        if obj and any(keyword in obj.key.lower() for keyword in ['password', 'token', 'passphrase']):
            form.base_fields['value'].widget = forms.PasswordInput(render_value=True)
        elif obj and 'private_key' in obj.key.lower():
            # SSH密钥使用文本区域
            form.base_fields['value'].widget = forms.Textarea(attrs={'rows': 10, 'cols': 80})
        
        return form
    
    def get_queryset(self, request):
        """根据用户权限过滤查询集"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # 非超级用户只能看到自己租户的配置
            if hasattr(request, 'user_profile') and request.user_profile:
                return qs.filter(tenant=request.user_profile.tenant)
            return qs.none()
        return qs
    
    def get_urls(self):
        """添加自定义URL"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "auth-config/",
                admin.site.admin_view(self.auth_config_view),
                name="grading_tenant_auth_config",
            ),
        ]
        return custom_urls + urls
    
    def auth_config_view(self, request):
        """租户认证配置视图"""
        if not hasattr(request, 'user_profile') or not request.user_profile:
            messages.error(request, "用户配置文件不存在")
            return HttpResponseRedirect(reverse("admin:grading_tenantconfig_changelist"))
        
        tenant = request.user_profile.tenant
        
        if request.method == "POST":
            try:
                # 处理SSH私钥文件上传
                if 'ssh_private_key_file' in request.FILES:
                    ssh_key_file = request.FILES['ssh_private_key_file']
                    
                    # 验证文件大小（限制为100KB）
                    if ssh_key_file.size > 100 * 1024:
                        messages.error(request, "SSH私钥文件过大，请确认选择了正确的私钥文件")
                        return HttpResponseRedirect(request.path)
                    
                    # 读取文件内容
                    try:
                        ssh_key_content = ssh_key_file.read().decode('utf-8')
                        
                        # 验证SSH私钥格式
                        if not (ssh_key_content.strip().startswith('-----BEGIN') and 'PRIVATE KEY-----' in ssh_key_content):
                            messages.error(request, "无效的SSH私钥格式，请确认选择了正确的私钥文件")
                            return HttpResponseRedirect(request.path)
                        
                        # 保存SSH私钥
                        TenantConfig.set_value(
                            tenant=tenant,
                            key='ssh_private_key',
                            value=ssh_key_content,
                            description="用户上传的SSH私钥"
                        )
                        
                        messages.success(request, "SSH私钥文件上传成功")
                        
                    except UnicodeDecodeError:
                        messages.error(request, "SSH私钥文件编码错误，请确认文件是UTF-8编码的文本文件")
                        return HttpResponseRedirect(request.path)
                    except Exception as e:
                        messages.error(request, f"读取SSH私钥文件失败：{str(e)}")
                        return HttpResponseRedirect(request.path)
                
                # 处理清除SSH私钥
                if request.POST.get('clear_ssh_key'):
                    TenantConfig.objects.filter(tenant=tenant, key='ssh_private_key').delete()
                    messages.success(request, "SSH私钥已清除")
                
                # 处理其他配置项
                for key in request.POST:
                    if key.startswith('config_'):
                        config_key = key.replace('config_', '')
                        value = request.POST.get(key, '')
                        
                        # 更新或创建配置
                        TenantConfig.set_value(
                            tenant=tenant,
                            key=config_key,
                            value=value,
                            description=f"用户设置的{config_key}配置"
                        )
                
                if not request.FILES.get('ssh_private_key_file') and not request.POST.get('clear_ssh_key'):
                    messages.success(request, "认证配置已保存")
                
                return HttpResponseRedirect(request.path)
                
            except Exception as e:
                messages.error(request, f"保存配置失败：{str(e)}")
                return HttpResponseRedirect(request.path)
        
        # 获取当前配置
        auth_configs = {
            'ssh_private_key': TenantConfig.get_value(tenant, 'ssh_private_key', ''),
            'ssh_key_passphrase': TenantConfig.get_value(tenant, 'ssh_key_passphrase', ''),
            'https_username': TenantConfig.get_value(tenant, 'https_username', ''),
            'https_password': TenantConfig.get_value(tenant, 'https_password', ''),
            'https_token': TenantConfig.get_value(tenant, 'https_token', ''),
            'git_user_name': TenantConfig.get_value(tenant, 'git_user_name', tenant.name),
            'git_user_email': TenantConfig.get_value(tenant, 'git_user_email', f'{tenant.name}@example.com'),
            'default_auth_method': TenantConfig.get_value(tenant, 'default_auth_method', 'https'),
        }
        
        context = {
            'title': 'Git认证配置',
            'tenant': tenant,
            'auth_configs': auth_configs,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'has_permission': True,
        }
        
        return render(request, 'admin/grading/tenant_auth_config.html', context)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制租户选择"""
        if db_field.name == "tenant":
            if not request.user.is_superuser:
                # 非超级用户只能选择自己的租户
                if hasattr(request, 'user_profile') and request.user_profile:
                    kwargs["queryset"] = Tenant.objects.filter(id=request.user_profile.tenant.id)
                else:
                    kwargs["queryset"] = Tenant.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def changelist_view(self, request, extra_context=None):
        """自定义列表视图，添加认证配置链接"""
        extra_context = extra_context or {}
        
        # 添加认证配置链接
        if hasattr(request, 'user_profile') and request.user_profile:
            extra_context['show_auth_config_link'] = True
            extra_context['auth_config_url'] = reverse('admin:grading_tenant_auth_config')
        
        return super().changelist_view(request, extra_context)


@admin.register(GradeTypeConfig)
class GradeTypeConfigAdmin(admin.ModelAdmin):
    """评分类型配置管理界面"""

    list_display = ("tenant", "class_identifier", "grade_type", "is_locked", "created_at")
    list_filter = ("tenant", "grade_type", "is_locked", "created_at")
    search_fields = ("tenant__name", "class_identifier")
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at")


class RepositoryForm(forms.ModelForm):
    """仓库表单"""

    class Meta:
        model = Repository
        fields = ["name", "url", "branch", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "输入仓库名称",
                }
            ),
            "url": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "仓库URL，如：https://github.com/user/repo.git",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "vLargeTextField",
                    "style": "width: 100%;",
                    "placeholder": "仓库描述",
                }
            ),
        }

    def clean(self):
        """验证表单数据"""
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        url = cleaned_data.get("url")

        if name and url:
            # 验证名称唯一性（在同一租户内）
            request = getattr(self, '_request', None)
            if request and hasattr(request, 'user_profile') and request.user_profile:
                tenant = request.user_profile.tenant
                existing = Repository.objects.filter(name=name, tenant=tenant)
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise ValidationError("该仓库名称在您的租户内已存在")
            else:
                # 如果无法获取租户信息，使用全局唯一性检查
                existing = Repository.objects.filter(name=name)
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise ValidationError("该仓库名称已存在")
            
            # 验证认证配置
            self._validate_auth_config(url)

        return cleaned_data
    
    def _validate_auth_config(self, url):
        """验证用户是否配置了必要的认证信息"""
        # 获取当前用户的租户
        request = getattr(self, '_request', None)
        if not request or not hasattr(request, 'user_profile') or not request.user_profile:
            return  # 无法获取租户信息，跳过验证
        
        tenant = request.user_profile.tenant
        
        # 判断仓库协议类型
        is_ssh = url.startswith('git@') or url.startswith('ssh://')
        is_https = url.startswith('https://')
        
        if is_ssh:
            # SSH协议需要私钥
            ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
            if not ssh_key:
                auth_config_url = reverse('admin:grading_tenant_auth_config')
                raise ValidationError(
                    format_html(
                        'SSH协议的仓库需要配置SSH私钥。'
                        '<a href="{}" target="_blank">点击这里配置SSH认证</a>',
                        auth_config_url
                    )
                )
        
        elif is_https:
            # HTTPS协议需要用户名密码或令牌
            username = TenantConfig.get_value(tenant, 'https_username')
            password = TenantConfig.get_value(tenant, 'https_password')
            token = TenantConfig.get_value(tenant, 'https_token')
            
            if not (username and (password or token)):
                auth_config_url = reverse('admin:grading_tenant_auth_config')
                raise ValidationError(
                    format_html(
                        'HTTPS协议的仓库需要配置用户名和密码（或个人访问令牌）。'
                        '<a href="{}" target="_blank">点击这里配置HTTPS认证</a>',
                        auth_config_url
                    )
                )
        
        else:
            # 未知协议
            raise ValidationError(
                '不支持的仓库URL格式。请使用SSH（git@...）或HTTPS（https://...）格式的URL。'
            )

    class Media:
        js = ("admin/js/repository_form.js",)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    form = RepositoryForm
    
    def get_form(self, request, obj=None, **kwargs):
        """获取表单，传递request对象"""
        form = super().get_form(request, obj, **kwargs)
        form._request = request  # 将request传递给表单
        return form
    
    def save_model(self, request, obj, form, change):
        """保存仓库时自动设置所有者和租户"""
        if not change:  # 新创建的仓库
            # 设置所有者
            obj.owner = request.user
            
            # 设置租户
            if hasattr(request, 'user_profile') and request.user_profile:
                obj.tenant = request.user_profile.tenant
            else:
                # 如果没有user_profile，尝试获取或创建
                try:
                    profile = request.user.profile
                    obj.tenant = profile.tenant
                except:
                    # 如果还是没有，记录日志但继续保存
                    logger.warning(f"用户 {request.user.username} 没有profile，仓库 {obj.name} 将没有租户")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """根据用户权限过滤查询集，用户只能看到自己租户的仓库"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            # 超级用户可以看到所有仓库
            return qs
        
        # 尝试获取用户的租户
        user_tenant = None
        
        if hasattr(request, 'user_profile') and request.user_profile:
            user_tenant = request.user_profile.tenant
        elif hasattr(request.user, 'profile'):
            user_tenant = request.user.profile.tenant
        
        if user_tenant:
            # 普通用户只能看到自己租户的仓库
            return qs.filter(tenant=user_tenant)
        
        # 如果无法获取租户信息，返回空查询集
        logger.warning(f"用户 {request.user.username} 没有租户信息，返回空仓库列表")
        return qs.none()
    
    list_display = (
        "name",
        "url",
        "get_branch",
        "get_sync_status",
        "is_active",
        "get_action_buttons",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "url", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def get_site_header(self):
        """自定义站点标题"""
        return "评分系统管理"

    def get_site_title(self):
        """自定义浏览器标签页标题"""
        return "评分系统管理"

    def get_index_title(self):
        """自定义首页标题"""
        return "评分系统管理"

    def get_urls(self):
        """添加自定义 URL"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "grading/",
                admin.site.admin_view(self.grading_view),
                name="grading_system",
            ),
            path(
                "<int:repo_id>/clone/",
                admin.site.admin_view(self.clone_repository),
                name="grading_repository_clone",
            ),
            path(
                "<int:repo_id>/sync/",
                admin.site.admin_view(self.sync_repository),
                name="grading_repository_sync",
            ),
            path(
                "<int:repo_id>/push/",
                admin.site.admin_view(self.push_repository),
                name="grading_repository_push",
            ),
            path(
                "<int:repo_id>/clear/",
                admin.site.admin_view(self.clear_repository),
                name="grading_repository_clear",
            ),
            path(
                "<int:repo_id>/change_branch/",
                admin.site.admin_view(self.change_branch),
                name="grading_repository_change_branch",
            ),
        ]
        return custom_urls + urls

    def grading_view(self, request):
        """评分系统视图"""
        return HttpResponseRedirect("/grading/")

    def get_app_list(self, request):
        """自定义应用列表"""
        app_list = super().get_app_list(request)
        # 添加评分系统链接
        app_list.append(
            {
                "name": "评分系统",
                "app_label": "grading_system",
                "url": "/grading/",
                "has_module_perms": True,
                "models": [],
            }
        )
        return app_list

    def add_view(self, request, form_url="", extra_context=None):
        """重定向到列表页面"""
        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def changelist_view(self, request, extra_context=None):
        """自定义列表视图"""
        extra_context = extra_context or {}

        # 处理表单提交
        if request.method == "POST":
            form = self.get_form(request)(request.POST)
            if form.is_valid():
                form.save()
                self.message_user(request, "仓库添加成功")
                return HttpResponseRedirect(".")
            else:
                extra_context["add_form"] = form
        else:
            extra_context["add_form"] = self.get_form(request)()

        return super().changelist_view(request, extra_context)

    def get_fieldsets(self, request, obj=None):
        """根据是否是添加页面返回不同的字段集"""
        if not obj:  # 添加页面
            return (
                (
                    None,
                    {
                        "fields": ("name", "url", "description"),
                        "description": "输入仓库信息，包括名称、URL和描述。",
                    },
                ),
            )
        # 编辑页面显示所有字段
        return (
            (
                "基本信息",
                {
                    "fields": ("name", "url", "branch", "description", "is_active"),
                },
            ),
            (
                "系统信息",
                {
                    "fields": ("last_sync_time", "created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

    def get_last_sync_time(self, obj):
        return obj.last_sync_time if hasattr(obj, "last_sync_time") else None

    get_last_sync_time.short_description = "最后同步时间"

    def get_sync_status(self, obj):
        """获取同步状态"""
        if not obj.is_cloned():
            return format_html('<span style="color: #999;">未克隆</span>')
        elif not hasattr(obj, "last_sync_time") or not obj.last_sync_time:
            return format_html('<span style="color: #999;">未同步</span>')
        return format_html('<span style="color: green;">已同步</span>')

    get_sync_status.short_description = "同步状态"

    def get_branch(self, obj):
        """显示分支和修改按钮"""
        if obj.is_cloned():
            # 获取实际的当前分支
            current_branch = obj.get_current_branch()
            branches = obj.get_actual_branches()
            branch_count = len(branches)
            
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="font-weight: bold; color: #28a745;">{}</span>'
                '<span style="color: #666; font-size: 11px;">({} 个分支)</span>'
                '<a href="{}" class="button" style="font-size: 11px; padding: 4px 8px;">切换</a>'
                '</div>',
                current_branch,
                branch_count,
                reverse("admin:grading_repository_change_branch", args=[obj.pk]),
            )
        else:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #999;">{}</span>'
                '<span style="color: #999; font-size: 11px;">(未克隆)</span>'
                '</div>',
                obj.branch
            )

    get_branch.short_description = "分支"

    def get_action_buttons(self, obj):
        """获取操作按钮"""
        if not obj.is_cloned():
            # 如果仓库未克隆，只显示克隆按钮
            return format_html(
                '<div class="action-buttons">' '<a class="button" href="{}">克隆</a>' "</div>",
                reverse("admin:grading_repository_clone", args=[obj.pk]),
            )

        # 如果仓库已克隆，显示更新、推送和删除按钮
        return format_html(
            '<div class="action-buttons">'
            '<a class="button" href="{}">更新</a> '
            '<a class="button" href="{}">推送</a> '
            '<a class="button delete-button" href="{}" onclick="return confirm(\'确定要移除仓库 {} 吗？\n\n注意：\n1. 这将删除本地仓库文件\n2. 这将从数据库中移除仓库记录\n3. 此操作不可恢复\')">移除</a>'
            "</div>",
            reverse("admin:grading_repository_sync", args=[obj.pk]),
            reverse("admin:grading_repository_push", args=[obj.pk]),
            reverse("admin:grading_repository_clear", args=[obj.pk]),
            obj.name,
        )

    get_action_buttons.short_description = "操作"

    def clone_repository(self, request, repo_id):
        """克隆仓库"""
        try:
            repo = Repository.objects.get(pk=repo_id)
            
            # 获取当前用户的租户
            if not hasattr(request, 'user_profile') or not request.user_profile:
                error_msg = "用户配置文件不存在，无法获取租户信息"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
            
            tenant = request.user_profile.tenant
            
            # 确保仓库关联到正确的租户
            if not repo.tenant:
                repo.tenant = tenant
                repo.save()
                logger.info(f"为仓库 {repo.name} 设置租户: {tenant.name}")

            # 获取本地路径
            local_path = repo.get_local_path()
            if not local_path:
                error_msg = "无法获取本地路径，请检查全局配置中的仓库基础目录设置"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 如果目录已存在，先删除
            if os.path.exists(local_path):
                shutil.rmtree(local_path)

            # 确保父目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 验证认证配置
            auth_validation_result = self._validate_repo_auth_config(repo, tenant, "克隆")
            if not auth_validation_result['valid']:
                error_msg = auth_validation_result['message']
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": False, 
                        "message": error_msg,
                        "auth_config_url": auth_validation_result.get('auth_config_url')
                    })
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 设置认证环境
            auth_setup = self._setup_git_auth_env(repo, tenant)
            env = auth_setup['env']
            ssh_key_path = auth_setup['ssh_key_path']
            clone_url = auth_setup['auth_url'] or repo.get_clone_url()

            try:
                # 执行克隆命令
                logger.info(f"开始克隆仓库: {repo.name}, URL: {repo.url}, 本地路径: {local_path}")
                
                # 构建git命令
                git_cmd = ["git", "clone"]
                
                # 先尝试克隆指定分支
                if repo.branch and repo.branch.strip():
                    git_cmd.extend(["-b", repo.branch])
                
                # 添加URL和本地路径
                git_cmd.extend([clone_url, local_path])
                
                logger.info(f"执行命令: {' '.join(git_cmd)}")
                
                result = subprocess.run(
                    git_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分钟超时
                    cwd=os.path.dirname(local_path)  # 在父目录中执行命令
                )
                
                # 如果指定分支克隆失败，尝试克隆默认分支
                if result.returncode != 0 and repo.branch and repo.branch.strip() and 'not found in upstream' in result.stderr:
                    logger.info(f"分支 {repo.branch} 不存在，尝试克隆默认分支")
                    
                    # 删除可能创建的目录
                    if os.path.exists(local_path):
                        shutil.rmtree(local_path)
                    
                    # 重新构建不指定分支的命令
                    git_cmd = ["git", "clone", clone_url, local_path]
                    logger.info(f"执行命令: {' '.join(git_cmd)}")
                    
                    result = subprocess.run(
                        git_cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=os.path.dirname(local_path)
                    )
                    
                    if result.returncode == 0:
                        # 克隆成功后，获取默认分支名称并更新仓库配置
                        try:
                            git_repo = git.Repo(local_path)
                            default_branch = git_repo.active_branch.name
                            logger.info(f"检测到默认分支: {default_branch}")
                            
                            # 更新仓库的分支设置
                            repo.branch = default_branch
                            repo.save()
                            logger.info(f"已将仓库分支更新为: {default_branch}")
                        except Exception as e:
                            logger.warning(f"无法检测默认分支: {e}")
                            # 使用常见的默认分支名
                            for common_branch in ['master', 'main', 'develop']:
                                try:
                                    git_repo = git.Repo(local_path)
                                    git_repo.git.checkout(common_branch)
                                    repo.branch = common_branch
                                    repo.save()
                                    logger.info(f"已切换到分支: {common_branch}")
                                    break
                                except:
                                    continue

                if result.returncode == 0:
                    # 更新最后同步时间
                    repo.last_sync_time = timezone.now()
                    
                    # 获取并更新分支列表
                    try:
                        branches = repo.get_actual_branches()
                        current_branch = repo.get_current_branch()
                        logger.info(f"克隆后更新分支信息: 当前分支={current_branch}, 可用分支={branches}")
                    except Exception as e:
                        logger.warning(f"更新分支信息失败: {e}")
                    
                    repo.save()
                    success_msg = f"仓库 {repo.name} 克隆成功"
                    logger.info(f"克隆成功: {success_msg}")
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": success_msg})
                    messages.success(request, success_msg)
                else:
                    # 分析错误并提供解决建议
                    error_analysis = self._analyze_git_error(result.stderr, repo, tenant, "克隆")
                    logger.error(f"克隆失败: {result.stderr}")
                    
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({
                            "success": False, 
                            "message": error_analysis['message'],
                            "auth_config_url": error_analysis.get('auth_config_url')
                        })
                    messages.error(request, format_html(error_analysis['message']))
                    
            finally:
                # 清理认证资源
                self._cleanup_auth_resources(ssh_key_path)

        except subprocess.TimeoutExpired:
            error_msg = "克隆超时，请检查网络连接和仓库地址"
            logger.error(error_msg)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"克隆失败：{str(e)}"
            logger.error(f"克隆异常: {error_msg}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "未知错误"})
        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
    
    def _validate_clone_auth_config(self, repo, tenant):
        """验证克隆时的认证配置"""
        auth_config_url = reverse('admin:grading_tenant_auth_config')
        
        # 判断仓库协议类型
        is_ssh = repo.url.startswith('git@') or repo.url.startswith('ssh://')
        is_https = repo.url.startswith('https://')
        
        if is_ssh:
            # SSH协议需要私钥
            ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
            if not ssh_key:
                return {
                    'valid': False,
                    'message': format_html(
                        'SSH协议的仓库需要配置SSH私钥才能克隆。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置SSH认证</a>'
                        '<span style="color: #666;">配置完成后请重新尝试克隆</span>',
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
            
            # 验证SSH密钥格式
            if not (ssh_key.strip().startswith('-----BEGIN') and 'PRIVATE KEY-----' in ssh_key):
                return {
                    'valid': False,
                    'message': format_html(
                        'SSH私钥格式不正确，请检查配置。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查SSH配置</a>'
                        '<span style="color: #666;">请确保上传了有效的SSH私钥文件</span>',
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
        
        elif is_https:
            # HTTPS协议需要用户名密码或令牌
            username = TenantConfig.get_value(tenant, 'https_username')
            password = TenantConfig.get_value(tenant, 'https_password')
            token = TenantConfig.get_value(tenant, 'https_token')
            
            if not username:
                return {
                    'valid': False,
                    'message': format_html(
                        'HTTPS协议的仓库需要配置用户名才能克隆。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置HTTPS认证</a>'
                        '<span style="color: #666;">请配置Git服务器的用户名</span>',
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
            
            if not (password or token):
                return {
                    'valid': False,
                    'message': format_html(
                        'HTTPS协议的仓库需要配置密码或个人访问令牌才能克隆。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置HTTPS认证</a>'
                        '<span style="color: #666;">请配置密码或个人访问令牌（推荐使用令牌）</span>',
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
        
        else:
            # 未知协议
            return {
                'valid': False,
                'message': format_html(
                    '不支持的仓库URL格式：{}'
                    '<br><br>'
                    '<span style="color: #666;">请使用SSH（git@...）或HTTPS（https://...）格式的URL</span>'
                    '<br>'
                    '<a href="{}" target="_blank" class="button" style="margin-top: 10px;">查看认证配置</a>',
                    repo.url,
                    auth_config_url
                ),
                'auth_config_url': auth_config_url
            }
        
        return {'valid': True}
    
    def _validate_repo_auth_config(self, repo, tenant, operation="操作"):
        """验证仓库操作时的认证配置（通用方法）"""
        auth_config_url = reverse('admin:grading_tenant_auth_config')
        
        # 判断仓库协议类型
        is_ssh = repo.url.startswith('git@') or repo.url.startswith('ssh://')
        is_https = repo.url.startswith('https://')
        
        if is_ssh:
            # SSH协议需要私钥
            ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
            if not ssh_key:
                return {
                    'valid': False,
                    'message': format_html(
                        'SSH协议的仓库需要配置SSH私钥才能进行{}。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置SSH认证</a>'
                        '<span style="color: #666;">配置完成后请重新尝试{}</span>',
                        operation,
                        auth_config_url,
                        operation
                    ),
                    'auth_config_url': auth_config_url
                }
            
            # 验证SSH密钥格式
            if not (ssh_key.strip().startswith('-----BEGIN') and 'PRIVATE KEY-----' in ssh_key):
                return {
                    'valid': False,
                    'message': format_html(
                        'SSH私钥格式不正确，无法进行{}。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查SSH配置</a>'
                        '<span style="color: #666;">请确保上传了有效的SSH私钥文件</span>',
                        operation,
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
        
        elif is_https:
            # HTTPS协议需要用户名密码或令牌
            username = TenantConfig.get_value(tenant, 'https_username')
            password = TenantConfig.get_value(tenant, 'https_password')
            token = TenantConfig.get_value(tenant, 'https_token')
            
            if not username:
                return {
                    'valid': False,
                    'message': format_html(
                        'HTTPS协议的仓库需要配置用户名才能进行{}。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置HTTPS认证</a>'
                        '<span style="color: #666;">请配置Git服务器的用户名</span>',
                        operation,
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
            
            if not (password or token):
                return {
                    'valid': False,
                    'message': format_html(
                        'HTTPS协议的仓库需要配置密码或个人访问令牌才能进行{}。'
                        '<br><br>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">配置HTTPS认证</a>'
                        '<span style="color: #666;">请配置密码或个人访问令牌（推荐使用令牌）</span>',
                        operation,
                        auth_config_url
                    ),
                    'auth_config_url': auth_config_url
                }
        
        else:
            # 未知协议
            return {
                'valid': False,
                'message': format_html(
                    '不支持的仓库URL格式：{}'
                    '<br><br>'
                    '<span style="color: #666;">请使用SSH（git@...）或HTTPS（https://...）格式的URL</span>'
                    '<br>'
                    '<a href="{}" target="_blank" class="button" style="margin-top: 10px;">查看认证配置</a>',
                    repo.url,
                    auth_config_url
                ),
                'auth_config_url': auth_config_url
            }
        
        return {'valid': True}
    
    def _setup_git_auth_env(self, repo, tenant):
        """设置Git认证环境（通用方法）"""
        env = os.environ.copy()
        ssh_key_path = None
        auth_url = None
        
        if repo.url.startswith('git@') or repo.url.startswith('ssh://'):
            # SSH协议
            ssh_key = TenantConfig.get_value(tenant, 'ssh_private_key')
            if ssh_key:
                # 创建临时 SSH 密钥文件
                ssh_key_path = os.path.join(tempfile.gettempdir(), f"ssh_key_{repo.id}_{timezone.now().timestamp()}")
                with open(ssh_key_path, "w") as f:
                    f.write(ssh_key)
                os.chmod(ssh_key_path, 0o600)
                
                # 配置 Git SSH 命令
                env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
                
        elif repo.url.startswith('https://'):
            # HTTPS协议
            username = TenantConfig.get_value(tenant, 'https_username')
            password = TenantConfig.get_value(tenant, 'https_password')
            token = TenantConfig.get_value(tenant, 'https_token')
            
            if username and (password or token):
                # 构建带认证的URL
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(repo.url)
                auth_token = token if token else password
                netloc = f"{username}:{auth_token}@{parsed.netloc}"
                auth_url = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        
        return {
            'env': env,
            'ssh_key_path': ssh_key_path,
            'auth_url': auth_url
        }
    
    def _cleanup_auth_resources(self, ssh_key_path):
        """清理认证资源（通用方法）"""
        if ssh_key_path and os.path.exists(ssh_key_path):
            try:
                os.remove(ssh_key_path)
                logger.info(f"临时SSH密钥文件已清理: {ssh_key_path}")
            except Exception as e:
                logger.warning(f"清理临时SSH密钥文件失败: {e}")
    
    def _analyze_git_error(self, error_output, repo, tenant, operation="操作"):
        """分析Git操作错误并提供解决建议（通用方法）"""
        auth_config_url = reverse('admin:grading_tenant_auth_config')
        error_lower = error_output.lower()
        
        # 认证相关错误
        if any(keyword in error_lower for keyword in ['authentication failed', 'permission denied', 'access denied', 'unauthorized']):
            if repo.url.startswith('git@') or repo.url.startswith('ssh://'):
                return {
                    'message': format_html(
                        '{}失败：SSH认证失败'
                        '<br><br>'
                        '<strong>可能的原因：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>SSH私钥不正确或已过期</li>'
                        '<li>SSH私钥没有访问该仓库的权限</li>'
                        '<li>仓库地址不正确</li>'
                        '</ul>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查SSH配置</a>'
                        '<span style="color: #666;">请确认SSH私钥配置正确</span>'
                        '<br><br>'
                        '<details style="margin-top: 10px;">'
                        '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                        '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                        '</details>',
                        operation,
                        auth_config_url,
                        error_output
                    ),
                    'auth_config_url': auth_config_url
                }
            else:
                return {
                    'message': format_html(
                        '{}失败：HTTPS认证失败'
                        '<br><br>'
                        '<strong>可能的原因：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>用户名或密码/令牌不正确</li>'
                        '<li>个人访问令牌已过期或权限不足</li>'
                        '<li>仓库是私有的，需要正确的访问权限</li>'
                        '</ul>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查HTTPS配置</a>'
                        '<span style="color: #666;">请确认用户名和令牌配置正确</span>'
                        '<br><br>'
                        '<details style="margin-top: 10px;">'
                        '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                        '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                        '</details>',
                        operation,
                        auth_config_url,
                        error_output
                    ),
                    'auth_config_url': auth_config_url
                }
        
        # 网络相关错误
        elif any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'recv failure', 'could not resolve']):
            return {
                'message': format_html(
                    '{}失败：网络连接问题'
                    '<br><br>'
                    '<strong>可能的原因：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>网络连接不稳定或中断</li>'
                    '<li>Git服务器暂时不可用</li>'
                    '<li>防火墙阻止了连接</li>'
                    '</ul>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查网络连接</li>'
                    '<li>稍后重试</li>'
                    '</ul>'
                    '<br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    operation,
                    error_output
                )
            }
        
        # 通用错误
        else:
            return {
                'message': format_html(
                    '{}失败：{}'
                    '<br><br>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查仓库URL是否正确</li>'
                    '<li>确认网络连接正常</li>'
                    '<li>检查认证配置是否正确</li>'
                    '<li>稍后重试</li>'
                    '</ul>'
                    '<a href="{}" target="_blank" class="button" style="margin-top: 10px;">检查认证配置</a>'
                    '<br><br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    operation,
                    error_output.split('\n')[0] if error_output else '未知错误',
                    auth_config_url,
                    error_output
                ),
                'auth_config_url': auth_config_url
            }
    
    def _analyze_clone_error(self, error_output, repo, tenant):
        """分析克隆错误并提供解决建议"""
        auth_config_url = reverse('admin:grading_tenant_auth_config')
        error_lower = error_output.lower()
        
        # 认证相关错误
        if any(keyword in error_lower for keyword in ['authentication failed', 'permission denied', 'access denied', 'unauthorized']):
            if repo.url.startswith('git@') or repo.url.startswith('ssh://'):
                return {
                    'message': format_html(
                        '克隆失败：SSH认证失败'
                        '<br><br>'
                        '<strong>可能的原因：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>SSH私钥不正确或已过期</li>'
                        '<li>SSH私钥没有访问该仓库的权限</li>'
                        '<li>仓库地址不正确</li>'
                        '</ul>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查SSH配置</a>'
                        '<span style="color: #666;">请确认SSH私钥配置正确</span>'
                        '<br><br>'
                        '<details style="margin-top: 10px;">'
                        '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                        '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                        '</details>',
                        auth_config_url,
                        error_output
                    ),
                    'auth_config_url': auth_config_url
                }
            else:
                return {
                    'message': format_html(
                        '克隆失败：HTTPS认证失败'
                        '<br><br>'
                        '<strong>可能的原因：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>用户名或密码/令牌不正确</li>'
                        '<li>个人访问令牌已过期或权限不足</li>'
                        '<li>仓库是私有的，需要正确的访问权限</li>'
                        '</ul>'
                        '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">检查HTTPS配置</a>'
                        '<span style="color: #666;">请确认用户名和令牌配置正确</span>'
                        '<br><br>'
                        '<details style="margin-top: 10px;">'
                        '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                        '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                        '</details>',
                        auth_config_url,
                        error_output
                    ),
                    'auth_config_url': auth_config_url
                }
        
        # 网络相关错误
        elif any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'recv failure', 'could not resolve']):
            return {
                'message': format_html(
                    '克隆失败：网络连接问题'
                    '<br><br>'
                    '<strong>可能的原因：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>网络连接不稳定或中断</li>'
                    '<li>Git服务器暂时不可用</li>'
                    '<li>防火墙阻止了连接</li>'
                    '<li>仓库地址不正确</li>'
                    '</ul>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查网络连接</li>'
                    '<li>稍后重试</li>'
                    '<li>确认仓库URL是否正确</li>'
                    '</ul>'
                    '<br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    error_output
                )
            }
        
        # 仓库不存在错误
        elif any(keyword in error_lower for keyword in ['not found', 'does not exist', 'repository not found']):
            return {
                'message': format_html(
                    '克隆失败：仓库不存在或无法访问'
                    '<br><br>'
                    '<strong>可能的原因：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>仓库URL不正确</li>'
                    '<li>仓库已被删除或移动</li>'
                    '<li>没有访问该仓库的权限</li>'
                    '<li>仓库是私有的，需要认证</li>'
                    '</ul>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查仓库URL是否正确</li>'
                    '<li>确认仓库是否存在</li>'
                    '<li>如果是私有仓库，请配置正确的认证信息</li>'
                    '</ul>'
                    '<a href="{}" target="_blank" class="button" style="margin-top: 10px;">检查认证配置</a>'
                    '<br><br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    auth_config_url,
                    error_output
                ),
                'auth_config_url': auth_config_url
            }
        
        # 分支不存在错误
        elif 'remote branch' in error_lower and 'not found' in error_lower:
            return {
                'message': format_html(
                    '克隆失败：指定的分支不存在'
                    '<br><br>'
                    '<strong>错误原因：</strong>仓库中不存在分支 "{}"'
                    '<br><br>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查分支名称是否正确</li>'
                    '<li>使用默认分支（如 main 或 master）</li>'
                    '<li>先克隆默认分支，再切换到目标分支</li>'
                    '</ul>'
                    '<br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    repo.branch,
                    error_output
                )
            }
        
        # 通用错误
        else:
            return {
                'message': format_html(
                    '克隆失败：{}'
                    '<br><br>'
                    '<strong>建议解决方案：</strong>'
                    '<ul style="margin: 10px 0; padding-left: 20px;">'
                    '<li>检查仓库URL是否正确</li>'
                    '<li>确认网络连接正常</li>'
                    '<li>检查认证配置是否正确</li>'
                    '<li>稍后重试</li>'
                    '</ul>'
                    '<a href="{}" target="_blank" class="button" style="margin-top: 10px;">检查认证配置</a>'
                    '<br><br>'
                    '<details style="margin-top: 10px;">'
                    '<summary style="cursor: pointer; color: #666;">查看详细错误信息</summary>'
                    '<pre style="background: #f5f5f5; padding: 10px; margin: 5px 0; font-size: 12px;">{}</pre>'
                    '</details>',
                    error_output.split('\n')[0] if error_output else '未知错误',
                    auth_config_url,
                    error_output
                ),
                'auth_config_url': auth_config_url
            }

    def _handle_uncommitted_changes(self, git_repo, request):
        """处理未提交的更改"""
        if git_repo.is_dirty():
            logger.info("检测到未提交的更改，正在自动提交...")  # 调试信息
            try:
                # 添加所有更改
                git_repo.git.add("--all")
                # 提交更改
                commit_message = (
                    f'Auto commit before sync at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
                )
                git_repo.index.commit(commit_message)
                logger.info(f"自动提交成功: {commit_message}")  # 调试信息
                return True
            except Exception as e:
                logger.error(f"自动提交失败: {str(e)}")  # 调试信息
                self.message_user(
                    request,
                    f"自动提交更改失败：{str(e)}\n" "请手动处理未提交的更改后再进行同步。",
                    level=messages.ERROR,
                )
                return False
        return True

    def sync_repository(self, request, repo_id):
        """同步仓库"""
        try:
            repo = Repository.objects.get(id=repo_id)
            
            # 获取当前用户的租户
            if not hasattr(request, 'user_profile') or not request.user_profile:
                error_msg = "用户配置文件不存在，无法获取租户信息"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
            
            tenant = request.user_profile.tenant
            
            # 确保仓库关联到正确的租户
            if not repo.tenant:
                repo.tenant = tenant
                repo.save()
                logger.info(f"为仓库 {repo.name} 设置租户: {tenant.name}")
            
            # 验证认证配置
            auth_validation_result = self._validate_repo_auth_config(repo, tenant, "同步")
            if not auth_validation_result['valid']:
                error_msg = auth_validation_result['message']
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": False, 
                        "message": error_msg,
                        "auth_config_url": auth_validation_result.get('auth_config_url')
                    })
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            local_path = repo.get_local_path()

            # 检查目录是否存在
            if not local_path:
                error_msg = "无法获取仓库本地路径，请检查全局配置中的仓库基础目录设置"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            if not os.path.exists(local_path):
                error_msg = format_html(
                    '仓库目录不存在：{}'
                    '<br><br>'
                    '<strong>解决方案：</strong>请先克隆仓库，然后再进行同步操作。',
                    local_path
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查目录权限
            if not os.access(local_path, os.R_OK | os.W_OK):
                error_msg = format_html(
                    '仓库目录权限不足：{}'
                    '<br><br>'
                    '<strong>解决方案：</strong>请检查目录权限设置。',
                    local_path
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查目录是否是 Git 仓库
            try:
                git_repo = git.Repo(local_path)
                logger.info(f"Git 仓库对象创建成功: {git_repo.git_dir}")
            except git.InvalidGitRepositoryError:
                error_msg = format_html(
                    '目录不是有效的 Git 仓库：{}'
                    '<br><br>'
                    '<strong>解决方案：</strong>请重新克隆仓库。',
                    local_path
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查远程仓库配置
            if not git_repo.remotes:
                error_msg = "仓库没有配置远程地址，请重新克隆仓库。"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查是否有未提交的更改，如果有则自动提交
            if not self._handle_uncommitted_changes(git_repo, request):
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": "自动提交更改失败"})
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 设置认证环境
            auth_setup = self._setup_git_auth_env(repo, tenant)
            env = auth_setup['env']
            ssh_key_path = auth_setup['ssh_key_path']
            
            try:
                # 执行同步操作
                logger.info(f"开始同步仓库: {repo.name}")
                
                # 使用subprocess执行git命令以便更好地控制环境变量
                result = subprocess.run(
                    ["git", "fetch", "--all"],
                    cwd=local_path,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    error_analysis = self._analyze_git_error(result.stderr, repo, tenant, "同步")
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({
                            "success": False, 
                            "message": error_analysis['message'],
                            "auth_config_url": error_analysis.get('auth_config_url')
                        })
                    messages.error(request, format_html(error_analysis['message']))
                    return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
                
                # 检查分支是否存在
                result = subprocess.run(
                    ["git", "show-ref", f"refs/remotes/origin/{repo.branch}"],
                    cwd=local_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    # 获取所有可用分支
                    result = subprocess.run(
                        ["git", "branch", "-r"],
                        cwd=local_path,
                        capture_output=True,
                        text=True
                    )
                    
                    branches = []
                    if result.returncode == 0:
                        branches = [
                            line.strip().replace('origin/', '') 
                            for line in result.stdout.split('\n') 
                            if line.strip() and 'origin/' in line and '->' not in line
                        ]
                    
                    error_msg = format_html(
                        '分支 {} 不存在。'
                        '<br><br>'
                        '<strong>可用的分支有：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '{}'
                        '</ul>'
                        '<strong>解决方案：</strong>请修改仓库的分支设置。',
                        repo.branch,
                        ''.join(f'<li>{branch}</li>' for branch in branches) if branches else '<li>无法获取分支列表</li>'
                    )
                    
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": False, "message": error_msg})
                    messages.error(request, format_html(error_msg))
                    return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
                
                # 拉取最新代码
                result = subprocess.run(
                    ["git", "pull", "origin", repo.branch],
                    cwd=local_path,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    repo.last_sync_time = timezone.now()
                    
                    # 同步后更新分支信息
                    try:
                        branches = repo.get_actual_branches()
                        current_branch = repo.get_current_branch()
                        logger.info(f"同步后更新分支信息: 当前分支={current_branch}, 可用分支={branches}")
                    except Exception as e:
                        logger.warning(f"更新分支信息失败: {e}")
                    
                    repo.save()
                    success_msg = f"仓库 {repo.name} 同步成功"
                    logger.info(success_msg)
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": success_msg})
                    messages.success(request, success_msg)
                else:
                    error_analysis = self._analyze_git_error(result.stderr, repo, tenant, "同步")
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({
                            "success": False, 
                            "message": error_analysis['message'],
                            "auth_config_url": error_analysis.get('auth_config_url')
                        })
                    messages.error(request, format_html(error_analysis['message']))
                    
            finally:
                # 清理认证资源
                self._cleanup_auth_resources(ssh_key_path)

        except subprocess.TimeoutExpired:
            error_msg = "同步超时，请检查网络连接"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"同步失败：{str(e)}"
            logger.error(f"同步异常: {error_msg}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)

        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def push_repository(self, request, repo_id):
        """推送仓库更改"""
        try:
            repo = Repository.objects.get(id=repo_id)
            
            # 获取当前用户的租户
            if not hasattr(request, 'user_profile') or not request.user_profile:
                error_msg = "用户配置文件不存在，无法获取租户信息"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
            
            tenant = request.user_profile.tenant
            
            # 确保仓库关联到正确的租户
            if not repo.tenant:
                repo.tenant = tenant
                repo.save()
                logger.info(f"为仓库 {repo.name} 设置租户: {tenant.name}")
            
            # 验证认证配置
            auth_validation_result = self._validate_repo_auth_config(repo, tenant, "推送")
            if not auth_validation_result['valid']:
                error_msg = auth_validation_result['message']
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "success": False, 
                        "message": error_msg,
                        "auth_config_url": auth_validation_result.get('auth_config_url')
                    })
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            local_path = repo.get_local_path()
            if not local_path or not os.path.exists(local_path):
                error_msg = format_html(
                    '仓库本地目录不存在'
                    '<br><br>'
                    '<strong>解决方案：</strong>请先克隆仓库，然后再进行推送操作。'
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查目录是否是 Git 仓库
            try:
                git_repo = git.Repo(local_path)
            except git.InvalidGitRepositoryError:
                error_msg = format_html(
                    '目录不是有效的 Git 仓库：{}'
                    '<br><br>'
                    '<strong>解决方案：</strong>请重新克隆仓库。',
                    local_path
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, format_html(error_msg))
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 设置认证环境
            auth_setup = self._setup_git_auth_env(repo, tenant)
            env = auth_setup['env']
            ssh_key_path = auth_setup['ssh_key_path']
            
            try:
                # 检查是否有更改需要提交
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=local_path,
                    capture_output=True,
                    text=True
                )
                
                has_changes = bool(result.stdout.strip())
                
                if has_changes:
                    # 添加所有更改
                    result = subprocess.run(
                        ["git", "add", "--all"],
                        cwd=local_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        error_msg = f"添加文件失败：{result.stderr}"
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "message": error_msg})
                        messages.error(request, error_msg)
                        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
                    
                    # 提交更改
                    commit_message = f"Auto commit at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    result = subprocess.run(
                        ["git", "commit", "-m", commit_message],
                        cwd=local_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        error_msg = f"提交失败：{result.stderr}"
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "message": error_msg})
                        messages.error(request, error_msg)
                        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
                
                # 推送到远程仓库
                logger.info(f"开始推送仓库: {repo.name}")
                result = subprocess.run(
                    ["git", "push", "origin", repo.branch],
                    cwd=local_path,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    if has_changes:
                        success_msg = f"仓库 {repo.name} 提交并推送成功"
                    else:
                        success_msg = f"仓库 {repo.name} 推送成功（无新更改）"
                    
                    logger.info(success_msg)
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": success_msg})
                    messages.success(request, success_msg)
                else:
                    error_analysis = self._analyze_git_error(result.stderr, repo, tenant, "推送")
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({
                            "success": False, 
                            "message": error_analysis['message'],
                            "auth_config_url": error_analysis.get('auth_config_url')
                        })
                    messages.error(request, format_html(error_analysis['message']))
                    
            finally:
                # 清理认证资源
                self._cleanup_auth_resources(ssh_key_path)

        except subprocess.TimeoutExpired:
            error_msg = "推送超时，请检查网络连接"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"推送失败：{str(e)}"
            logger.error(f"推送异常: {error_msg}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)

        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def clear_repository(self, request, repo_id):
        """移除仓库"""
        try:
            repo = Repository.objects.get(id=repo_id)
            repo_name = repo.name
            local_path = repo.get_local_path()
            
            logger.info(f"开始移除仓库: {repo_name}")

            # 删除本地目录
            if local_path and os.path.exists(local_path):
                try:
                    # 在Windows上，有时需要多次尝试删除
                    import time
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            shutil.rmtree(local_path)
                            logger.info(f"本地仓库目录已删除: {local_path}")
                            break
                        except PermissionError as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"删除目录失败，重试中... ({attempt + 1}/{max_retries}): {e}")
                                time.sleep(1)
                            else:
                                raise
                except Exception as e:
                    error_msg = format_html(
                        '删除本地仓库文件失败：{}'
                        '<br><br>'
                        '<strong>可能的原因：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>文件被其他程序占用</li>'
                        '<li>权限不足</li>'
                        '<li>文件系统错误</li>'
                        '</ul>'
                        '<strong>解决方案：</strong>'
                        '<ul style="margin: 10px 0; padding-left: 20px;">'
                        '<li>关闭可能占用文件的程序</li>'
                        '<li>手动删除目录：{}</li>'
                        '</ul>'
                        '<span style="color: #666;">数据库记录将继续删除</span>',
                        str(e),
                        local_path
                    )
                    
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({
                            "success": False, 
                            "message": error_msg,
                            "partial_success": True  # 表示部分成功，将继续删除数据库记录
                        })
                    messages.warning(request, format_html(error_msg))
            else:
                logger.info("本地仓库目录不存在，跳过删除")

            # 删除数据库记录
            repo.delete()
            logger.info(f"仓库数据库记录已删除: {repo_name}")

            success_msg = f"仓库 {repo_name} 已成功移除"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": success_msg})
            messages.success(request, success_msg)
            
        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"移除仓库失败：{str(e)}"
            logger.error(f"移除仓库异常: {error_msg}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)

        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def get_actions(self, request):
        """获取批量操作"""
        actions = super().get_actions(request)
        return actions

    def change_branch(self, request, repo_id):
        """修改分支"""
        try:
            repo = Repository.objects.get(id=repo_id)

            if request.method == "POST":
                new_branch = request.POST.get("branch")
                if not new_branch:
                    self.message_user(request, "请选择分支", level=messages.ERROR)
                    return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                # 如果仓库已克隆，验证分支是否存在并切换
                if repo.is_cloned():
                    try:
                        import subprocess
                        local_path = repo.get_local_path()
                        
                        # 先获取最新的分支信息
                        subprocess.run(
                            ["git", "fetch", "--all"],
                            cwd=local_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        # 获取实际的分支列表
                        available_branches = repo.get_actual_branches()
                        
                        # 检查分支是否存在
                        if new_branch not in available_branches:
                            self.message_user(
                                request,
                                format_html(
                                    "分支 <strong>{}</strong> 不存在。<br><br>"
                                    "可用的分支有：<br>"
                                    "{}",
                                    new_branch,
                                    "<br>".join(f"• {branch}" for branch in available_branches)
                                ),
                                level=messages.ERROR,
                            )
                            return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                        # 切换到新分支
                        result = subprocess.run(
                            ["git", "checkout", new_branch],
                            cwd=local_path,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode != 0:
                            # 如果本地分支不存在，尝试创建并跟踪远程分支
                            result = subprocess.run(
                                ["git", "checkout", "-b", new_branch, f"origin/{new_branch}"],
                                cwd=local_path,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            if result.returncode != 0:
                                self.message_user(
                                    request,
                                    f"切换到分支 {new_branch} 失败：{result.stderr}",
                                    level=messages.ERROR,
                                )
                                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))
                        
                        logger.info(f"成功切换到分支: {new_branch}")
                        
                    except Exception as e:
                        self.message_user(
                            request,
                            f"切换分支时发生错误：{str(e)}",
                            level=messages.ERROR,
                        )
                        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                # 更新分支
                repo.branch = new_branch
                repo.save()

                self.message_user(
                    request, 
                    format_html("分支已成功切换为：<strong>{}</strong>", new_branch),
                    level=messages.SUCCESS
                )
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 显示分支选择页面
            if repo.is_cloned():
                # 获取实际的分支列表和当前分支
                branches = repo.get_actual_branches()
                current_branch = repo.get_current_branch()
            else:
                # 未克隆的仓库使用保存的分支列表
                branches = repo.branches
                current_branch = repo.branch
            
            context = {
                "title": f"切换分支 - {repo.name}",
                "repo": repo,
                "branches": branches,
                "current_branch": current_branch,
                "is_cloned": repo.is_cloned(),
                "opts": self.model._meta,
                "app_label": self.model._meta.app_label,
                "has_permission": self.has_change_permission(request),
            }

            return render(request, "admin/grading/repository/change_branch.html", context)

        except Repository.DoesNotExist:
            self.message_user(request, "仓库不存在", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"修改分支失败：{str(e)}", level=messages.ERROR)

        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def has_add_permission(self, request):
        """允许添加仓库"""
        return True

    def has_change_permission(self, request, obj=None):
        """允许修改仓库"""
        return True

    def has_delete_permission(self, request, obj=None):
        """允许删除仓库"""
        return True

    def has_view_permission(self, request, obj=None):
        """允许查看仓库"""
        return True

    def delete_model(self, request, obj):
        """删除单个仓库"""
        try:
            # 删除本地目录
            local_path = obj.get_local_path()
            if local_path and os.path.exists(local_path):
                try:
                    shutil.rmtree(local_path)
                except Exception as e:
                    messages.warning(
                        request,
                        f"删除本地仓库文件失败：{str(e)}，但将继续删除数据库记录",
                    )

            # 删除数据库记录
            obj.delete()
            messages.success(request, f"仓库 {obj.name} 已成功移除")
        except Exception as e:
            messages.error(request, f"移除仓库失败：{str(e)}")

    def delete_queryset(self, request, queryset):
        """批量删除仓库"""
        success_count = 0
        error_count = 0

        for obj in queryset:
            try:
                # 删除本地目录
                local_path = obj.get_local_path()
                if local_path and os.path.exists(local_path):
                    try:
                        shutil.rmtree(local_path)
                    except Exception as e:
                        messages.warning(
                            request,
                            f"删除仓库 {obj.name} 的本地文件失败：{str(e)}，但将继续删除数据库记录",
                        )

                # 删除数据库记录
                obj.delete()
                success_count += 1
            except Exception as e:
                messages.error(request, f"移除仓库 {obj.name} 失败：{str(e)}")
                error_count += 1

        if success_count > 0:
            messages.success(request, f"成功移除 {success_count} 个仓库")
        if error_count > 0:
            messages.error(request, f"移除 {error_count} 个仓库失败")


# 注册其他模型（没有使用装饰器的）
admin.site.register(Student, StudentAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
# Repository, GlobalConfig 等已通过装饰器注册


class SemesterAdmin(admin.ModelAdmin):
    """学期管理界面"""

    list_display = ("name", "start_date", "end_date", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    ordering = ("-start_date",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("name", "start_date", "end_date", "is_active", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        """保存时确保只有一个活跃学期"""
        if obj.is_active:
            # 将其他学期设为非活跃
            Semester.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """自定义编辑视图"""
        try:
            return super().change_view(request, object_id, form_url, extra_context)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"学期编辑页面错误: {str(e)}")
            # 返回一个简单的错误页面
            from django.http import HttpResponse

            return HttpResponse(f"编辑页面加载失败: {str(e)}", status=500)


class CourseAdmin(admin.ModelAdmin):
    """课程管理界面"""

    list_display = ("name", "semester", "teacher", "class_name", "location", "created_at")
    list_filter = ("semester", "teacher", "created_at")
    search_fields = ("name", "description", "location", "class_name")
    ordering = ("semester", "name")
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        """只显示当前用户的课程"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(teacher=request.user)
        return qs


# 注册校历相关模型
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
