import logging
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

import git
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Assignment, GlobalConfig, Repository, Student, Submission

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
        "student",
        "assignment",
        "submitted_at",
        "grade",
        "status",
        "teacher_comment_action",
    ]
    search_fields = ["student__name", "student__student_id", "assignment__name"]
    list_filter = ["status", "submitted_at", "assignment"]
    date_hierarchy = "submitted_at"
    raw_id_fields = ["student", "assignment"]

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "teacher_comment/<int:submission_id>/",
                self.admin_site.admin_view(self.teacher_comment_view),
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
            self.admin_site.each_context(request),
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
        fields = (
            "https_username",
            "https_password",
            "ssh_key",
            "ssh_key_file",
            "repo_base_dir",
        )
        widgets = {
            "https_password": forms.PasswordInput(render_value=True),
            "ssh_key": forms.Textarea(
                attrs={
                    "rows": 10,
                    "cols": 80,
                    "class": "vLargeTextField",
                    "style": "display: block !important; width: 100%; height: 200px; font-family: monospace; margin-bottom: 10px;",
                    "placeholder": "如果不上传文件，也可以直接粘贴 SSH 私钥内容到这里（支持 RSA 格式）",
                }
            ),
            "repo_base_dir": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "例如：~/jobs",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.ssh_key:
            self.initial["ssh_key"] = self.instance.ssh_key
            self.fields["ssh_key"].widget.attrs[
                "style"
            ] = "display: block !important; width: 100%; height: 200px; font-family: monospace; margin-bottom: 10px;"
        # 设置 repo_base_dir 的默认值
        if not self.instance.pk:
            self.initial["repo_base_dir"] = "~/jobs"

    def clean(self):
        """验证表单数据"""
        cleaned_data = super().clean()

        # 处理 SSH 密钥文件
        ssh_key_file = cleaned_data.get("ssh_key_file")
        if ssh_key_file:
            try:
                content = ssh_key_file.read().decode("utf-8")
                cleaned_data["ssh_key"] = content
            except Exception:
                pass

        return cleaned_data

    def save(self, commit=True):
        """保存表单数据"""
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

    class Media:
        css = {"all": ("grading/admin/css/grading_ssh_key_input.css",)}
        js = (
            "grading/admin/js/grading_ssh_key_input.js",
            "grading/admin/js/grading_repo_dir_browser.js",
        )


@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    """全局配置管理界面"""

    form = GlobalConfigForm
    list_display = ("updated_at", "has_https_auth", "has_ssh_key", "get_repo_base_dir")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "认证信息",
            {
                "fields": (
                    "https_username",
                    "https_password",
                    "ssh_key_file",
                    "ssh_key",
                ),
                "description": "配置访问 Git 仓库所需的认证信息。可以使用 HTTPS 用户名密码或 SSH 私钥。",
            },
        ),
        (
            "仓库配置",
            {
                "fields": ("repo_base_dir",),
                "description": "配置仓库克隆的基础目录。默认为 ~/jobs。",
            },
        ),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": "系统自动记录的时间信息。",
            },
        ),
    )

    def has_https_auth(self, obj):
        """检查是否配置了 HTTPS 认证"""
        return bool(obj.https_username and obj.https_password)

    has_https_auth.boolean = True
    has_https_auth.short_description = "HTTPS 认证"

    def has_ssh_key(self, obj):
        """检查是否配置了 SSH 密钥"""
        return bool(obj.ssh_key)

    has_ssh_key.boolean = True
    has_ssh_key.short_description = "SSH 密钥"

    def get_repo_base_dir(self, obj):
        """获取仓库基础目录"""
        return obj.repo_base_dir

    get_repo_base_dir.short_description = "仓库目录"

    def get_readonly_fields(self, request, obj=None):
        """获取只读字段"""
        if obj:  # 编辑现有对象
            return self.readonly_fields + ("created_at",)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """保存模型时的处理"""
        # 直接保存模型
        super().save_model(request, obj, form, change)
        messages.success(request, "全局配置已保存")

    def has_add_permission(self, request):
        """控制是否允许添加新对象"""
        return not GlobalConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """控制是否允许删除对象"""
        return False

    def get_urls(self):
        """添加目录浏览 URL"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "browse-directory/",
                self.admin_site.admin_view(self.browse_directory),
                name="grading_globalconfig_browse_directory",
            ),
        ]
        return custom_urls + urls

    def browse_directory(self, request):
        """浏览目录"""
        if not request.user.is_staff:
            return HttpResponseForbidden("只有管理员可以浏览目录")

        try:
            # 获取要浏览的目录
            dir_path = request.GET.get("dir", "")

            # 如果是空路径，从用户家目录开始
            if not dir_path:
                dir_path = os.path.expanduser("~")

            # 确保路径是绝对路径
            if not os.path.isabs(dir_path):
                dir_path = os.path.abspath(dir_path)

            # 确保路径存在且是目录
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                return JsonResponse({"error": "目录不存在"}, status=400)

            # 获取目录内容
            items = []
            for item in os.listdir(dir_path):
                # 跳过隐藏目录（以.开头的目录）
                if item.startswith("."):
                    continue

                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    items.append({"name": item, "path": full_path, "type": "dir"})

            # 按名称排序
            items.sort(key=lambda x: x["name"].lower())

            return JsonResponse({"current_path": dir_path, "items": items})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class RepositoryForm(forms.ModelForm):
    """仓库表单"""

    class Meta:
        model = Repository
        fields = ["url", "name", "branch"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "输入仓库名称，如果不输入则自动从 URL 生成",
                }
            ),
            "url": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "oninput": "updateRepoName(this.value)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是新建仓库，隐藏 branch 字段
        if not self.instance.pk and "branch" in self.fields:
            self.fields["branch"].widget = forms.HiddenInput()

        # 如果是编辑仓库，禁用 URL 字段
        if self.instance.pk:
            self.fields["url"].widget.attrs["readonly"] = True
            self.fields["url"].widget.attrs["style"] = "width: 100%; background-color: #f5f5f5;"
            self.fields["url"].help_text = "编辑仓库时不允许修改 URL"

        # 保存原始 URL，用于判断是否修改了 URL
        if self.instance.pk:
            self.instance._original_url = self.instance.url

    def clean(self):
        """验证表单数据"""
        cleaned_data = super().clean()
        url = cleaned_data.get("url")

        if url:
            try:
                # 验证 URL 格式
                if url.startswith("git@"):
                    # SSH 格式：git@host:username/repository
                    if ":" not in url:
                        raise ValidationError("无效的 SSH URL 格式")
                    host, repo_path = url.split(":", 1)
                    if not repo_path or "/" not in repo_path:
                        raise ValidationError("无效的仓库路径")
                else:
                    # HTTPS 格式：https://host/username/repository
                    parsed = urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        raise ValidationError("无效的 HTTPS URL 格式")
                    if not parsed.path or len(parsed.path.strip("/").split("/")) < 2:
                        raise ValidationError("无效的仓库路径")

                # 如果没有提供名称，从 URL 生成
                if not cleaned_data.get("name"):
                    cleaned_data["name"] = Repository.generate_name_from_url(url)

                # 验证名称唯一性
                name = cleaned_data.get("name")
                if name:
                    existing = Repository.objects.filter(name=name)
                    if self.instance.pk:
                        existing = existing.exclude(pk=self.instance.pk)
                    if existing.exists():
                        raise ValidationError("该仓库名称已存在")

                # 验证 URL 唯一性
                existing = Repository.objects.filter(url=url)
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise ValidationError("该仓库 URL 已存在")

            except Exception as e:
                raise ValidationError(f"URL 验证失败: {str(e)}")

        return cleaned_data

    def save(self, commit=True):
        """保存表单数据"""
        instance = super().save(commit=False)

        # 只有在新建仓库或修改 URL 时才获取分支列表
        if not instance.pk or instance.url != getattr(instance, "_original_url", None):
            try:
                config = GlobalConfig.objects.first()
                if not config:
                    raise ValueError("请先配置全局认证信息")

                # 准备环境变量
                env = os.environ.copy()
                if instance.is_ssh_protocol() and config.ssh_key:
                    # 创建临时 SSH 密钥文件
                    ssh_key_path = os.path.join(os.path.expanduser("~"), ".ssh", "id_rsa_temp")
                    os.makedirs(os.path.dirname(ssh_key_path), exist_ok=True)
                    with open(ssh_key_path, "w") as f:
                        f.write(config.ssh_key)
                    os.chmod(ssh_key_path, 0o600)
                    env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"

                # 使用 git ls-remote 获取分支列表
                clone_url = instance.get_clone_url()
                result = subprocess.run(
                    ["git", "ls-remote", "--heads", clone_url],
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    # 解析分支列表
                    branches = []
                    for line in result.stdout.splitlines():
                        if line.strip():
                            # 提取分支名
                            branch = line.split("refs/heads/")[-1]
                            branches.append(branch)

                    if not branches:
                        raise ValueError("仓库没有可用的分支")

                    # 设置分支列表
                    instance.branches = branches

                    # 设置默认分支
                    if "main" in branches:
                        instance.branch = "main"
                    elif "master" in branches:
                        instance.branch = "master"
                    else:
                        instance.branch = branches[0]
                else:
                    raise ValueError(f"获取分支列表失败：{result.stderr}")

                # 清理临时文件
                if instance.is_ssh_protocol() and config.ssh_key:
                    try:
                        os.remove(ssh_key_path)
                    except Exception:
                        pass

            except Exception as e:
                self.add_error(
                    "url",
                    format_html(
                        '<div class="alert alert-danger" style="margin-top: 10px;">'
                        "<strong>获取分支列表失败</strong><br>"
                        "错误信息：{}"
                        "</div>",
                        str(e),
                    ),
                )
                return instance

        if commit:
            instance.save()
        return instance

    class Media:
        js = ("admin/js/repository_form.js",)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    form = RepositoryForm
    list_display = (
        "name",
        "url",
        "get_branch",
        "get_last_sync_time",
        "get_sync_status",
        "get_action_buttons",
    )
    readonly_fields = ("branch", "get_last_sync_time", "get_sync_status")
    change_list_template = "admin/grading/repository/change_list.html"

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
                self.admin_site.admin_view(self.grading_view),
                name="grading_system",
            ),
            path(
                "<int:repo_id>/clone/",
                self.admin_site.admin_view(self.clone_repository),
                name="grading_repository_clone",
            ),
            path(
                "<int:repo_id>/sync/",
                self.admin_site.admin_view(self.sync_repository),
                name="grading_repository_sync",
            ),
            path(
                "<int:repo_id>/push/",
                self.admin_site.admin_view(self.push_repository),
                name="grading_repository_push",
            ),
            path(
                "<int:repo_id>/clear/",
                self.admin_site.admin_view(self.clear_repository),
                name="grading_repository_clear",
            ),
            path(
                "<int:repo_id>/change_branch/",
                self.admin_site.admin_view(self.change_branch),
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
                        "fields": ("name", "url"),
                        "description": "输入仓库的 URL，系统会自动提取仓库名称并使用默认分支。",
                    },
                ),
            )
        return self.fieldsets  # 编辑页面显示所有字段

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
        return format_html(
            '{} <a href="{}" class="button">修改</a>',
            obj.branch,
            reverse("admin:grading_repository_change_branch", args=[obj.pk]),
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
            config = GlobalConfig.objects.first()

            if not config:
                error_msg = "请先配置全局认证信息"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 获取本地路径
            local_path = repo.get_local_path()
            if not local_path:
                error_msg = "无法获取本地路径"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 如果目录已存在，先删除
            if os.path.exists(local_path):
                shutil.rmtree(local_path)

            # 确保父目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 获取克隆 URL
            clone_url = repo.get_clone_url()

            # 准备环境变量
            env = os.environ.copy()
            if repo.is_ssh_protocol() and config.ssh_key:
                # 创建临时 SSH 密钥文件
                ssh_key_path = os.path.join(os.path.expanduser("~"), ".ssh", "id_rsa_temp")
                os.makedirs(os.path.dirname(ssh_key_path), exist_ok=True)
                with open(ssh_key_path, "w") as f:
                    f.write(config.ssh_key)
                os.chmod(ssh_key_path, 0o600)

                # 配置 Git SSH 命令
                env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"

            # 执行克隆命令
            result = subprocess.run(
                ["git", "clone", "-b", repo.branch, clone_url, local_path],
                env=env,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # 更新最后同步时间
                repo.last_sync_time = timezone.now()
                repo.save()
                success_msg = f"仓库 {repo.name} 克隆成功"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True, "message": success_msg})
                messages.success(request, success_msg)
            else:
                error_msg = f"克隆失败：{result.stderr}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                messages.error(request, error_msg)

            # 清理临时文件
            if repo.is_ssh_protocol() and config.ssh_key:
                try:
                    os.remove(ssh_key_path)
                except Exception:
                    pass

        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"克隆失败：{str(e)}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            messages.error(request, error_msg)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "未知错误"})
        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

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
            local_path = repo.get_local_path()

            # 检查目录是否存在
            if not local_path:
                error_msg = "无法获取仓库本地路径，请检查全局配置中的仓库基础目录设置"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                self.message_user(request, error_msg, level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            logger.info(f"仓库本地路径: {local_path}")  # 调试信息

            if not os.path.exists(local_path):
                error_msg = f"仓库目录不存在：{local_path}\n请先克隆仓库，然后再进行同步操作。"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                self.message_user(request, error_msg, level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查目录权限
            if not os.access(local_path, os.R_OK | os.W_OK):
                error_msg = f"仓库目录权限不足：{local_path}\n请检查目录权限设置。"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                self.message_user(request, error_msg, level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查目录是否是 Git 仓库
            try:
                git_repo = git.Repo(local_path)
                logger.info(f"Git 仓库对象创建成功: {git_repo.git_dir}")  # 调试信息
            except git.InvalidGitRepositoryError:
                error_msg = f"目录不是有效的 Git 仓库：{local_path}\n请重新克隆仓库。"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                self.message_user(request, error_msg, level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查远程仓库配置
            if not git_repo.remotes:
                error_msg = "仓库没有配置远程地址\n请重新克隆仓库。"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})
                self.message_user(request, error_msg, level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            logger.info(f"远程仓库配置: {[remote.name for remote in git_repo.remotes]}")  # 调试信息

            # 检查是否有未提交的更改，如果有则自动提交
            if not self._handle_uncommitted_changes(git_repo, request):
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": "自动提交更改失败"})
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 检查 SSH 密钥配置
            if repo.is_ssh_protocol():
                config = GlobalConfig.objects.first()
                if not config or not config.ssh_key:
                    error_msg = "SSH 密钥未配置\n请先在全局配置中设置 SSH 密钥"
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": False, "message": error_msg})
                    self.message_user(request, error_msg, level=messages.ERROR)
                    return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                # 创建临时 SSH 密钥文件
                import tempfile

                with tempfile.NamedTemporaryFile(mode="w", delete=False) as key_file:
                    key_file.write(config.ssh_key)
                    key_path = key_file.name

                try:
                    # 设置 SSH 密钥文件权限
                    os.chmod(key_path, 0o600)
                    logger.info(f"SSH 密钥文件创建成功: {key_path}")  # 调试信息

                    # 配置 Git 使用临时 SSH 密钥
                    with git_repo.git.custom_environment(
                        GIT_SSH_COMMAND=f"ssh -i {key_path} -o StrictHostKeyChecking=no"
                    ):
                        # 尝试获取远程信息
                        try:
                            logger.info("开始获取远程信息...")  # 调试信息
                            git_repo.git.fetch("-v", "--all")
                            logger.info("远程信息获取成功")  # 调试信息
                        except git.exc.GitCommandError as e:
                            logger.error(f"Git 操作失败: {str(e)}")  # 调试信息
                            error_msg = "无法访问远程仓库，请检查：\n1. SSH 密钥是否正确配置\n2. 远程仓库地址是否正确\n3. 是否有权限访问该仓库"
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "message": error_msg})
                            self.message_user(request, error_msg, level=messages.ERROR)
                            return HttpResponseRedirect(
                                reverse("admin:grading_repository_changelist")
                            )

                        # 检查分支是否存在
                        try:
                            logger.info(f"检查分支 {repo.branch} 是否存在...")  # 调试信息
                            git_repo.git.show_ref(f"refs/remotes/origin/{repo.branch}")
                            logger.info("分支存在")  # 调试信息
                        except git.exc.GitCommandError:
                            # 获取所有可用分支
                            branches = [
                                ref.name.split("/")[-1]
                                for ref in git_repo.refs
                                if ref.name.startswith("refs/remotes/origin/")
                            ]
                            logger.info(f"可用分支: {branches}")  # 调试信息
                            error_msg = (
                                f"分支 {repo.branch} 不存在。\n可用的分支有：\n"
                                + "\n".join(f"- {branch}" for branch in branches)
                                + "\n\n请修改仓库的分支设置。"
                            )
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "message": error_msg})
                            self.message_user(request, error_msg, level=messages.ERROR)
                            return HttpResponseRedirect(
                                reverse("admin:grading_repository_changelist")
                            )

                        # 更新代码
                        logger.info("开始更新代码...")  # 调试信息
                        git_repo.git.pull("origin", repo.branch)
                        logger.info("代码更新成功")  # 调试信息
                        repo.last_sync_time = timezone.now()
                        repo.save()

                        success_msg = "仓库同步成功"
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": True, "message": success_msg})
                        self.message_user(request, success_msg)
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(key_path)
                        logger.info("临时 SSH 密钥文件已清理")  # 调试信息
                    except Exception:
                        pass
            else:
                # HTTPS 方式
                config = GlobalConfig.objects.first()
                if not config or not config.https_username or not config.https_password:
                    error_msg = "HTTPS 认证信息未配置\n请先在全局配置中设置用户名和密码"
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": False, "message": error_msg})
                    self.message_user(request, error_msg, level=messages.ERROR)
                    return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                # 配置 Git 使用 HTTPS 认证
                with git_repo.git.custom_environment(
                    GIT_ASKPASS="echo",
                    GIT_USERNAME=config.https_username,
                    GIT_PASSWORD=config.https_password,
                ):
                    try:
                        logger.info("开始获取远程信息...")  # 调试信息
                        git_repo.git.fetch("-v", "--all")
                        logger.info("远程信息获取成功")  # 调试信息

                        # 检查分支是否存在
                        try:
                            logger.info(f"检查分支 {repo.branch} 是否存在...")  # 调试信息
                            git_repo.git.show_ref(f"refs/remotes/origin/{repo.branch}")
                            logger.info("分支存在")  # 调试信息
                        except git.exc.GitCommandError:
                            # 获取所有可用分支
                            branches = [
                                ref.name.split("/")[-1]
                                for ref in git_repo.refs
                                if ref.name.startswith("refs/remotes/origin/")
                            ]
                            logger.info(f"可用分支: {branches}")  # 调试信息
                            error_msg = (
                                f"分支 {repo.branch} 不存在。\n可用的分支有：\n"
                                + "\n".join(f"- {branch}" for branch in branches)
                                + "\n\n请修改仓库的分支设置。"
                            )
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "message": error_msg})
                            self.message_user(request, error_msg, level=messages.ERROR)
                            return HttpResponseRedirect(
                                reverse("admin:grading_repository_changelist")
                            )

                        logger.info("开始更新代码...")  # 调试信息
                        git_repo.git.pull("origin", repo.branch)
                        logger.info("代码更新成功")  # 调试信息
                        repo.last_sync_time = timezone.now()
                        repo.save()

                        success_msg = "仓库同步成功"
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": True, "message": success_msg})
                        self.message_user(request, success_msg)
                    except git.exc.GitCommandError as e:
                        logger.error(f"Git 操作失败: {str(e)}")  # 调试信息
                        error_msg = "仓库同步失败，请检查：\n1. HTTPS 认证信息是否正确\n2. 远程仓库地址是否正确\n3. 是否有权限访问该仓库"
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "message": error_msg})
                        self.message_user(request, error_msg, level=messages.ERROR)

        except Repository.DoesNotExist:
            error_msg = "仓库不存在"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            self.message_user(request, error_msg, level=messages.ERROR)
        except Exception as e:
            logger.error(f"同步失败: {str(e)}")  # 调试信息
            error_msg = f"同步失败：{str(e)}\n请检查仓库配置和权限设置。"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_msg})
            self.message_user(request, error_msg, level=messages.ERROR)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "未知错误"})
        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def push_repository(self, request, repo_id):
        """推送仓库更改"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        repo = Repository.objects.get(id=repo_id)
        config = GlobalConfig.objects.first()

        try:
            local_path = repo.get_local_path()
            if not local_path or not os.path.exists(local_path):
                messages.error(request, "仓库本地目录不存在，请先克隆仓库")
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            git_repo = git.Repo(local_path)

            # 添加所有更改
            git_repo.git.add("--all")

            # 检查是否有更改需要提交
            if git_repo.is_dirty():
                # 提交更改
                git_repo.index.commit(f"Auto commit at {timezone.now()}")

                # 处理 SSH 密钥
                if repo.is_ssh_protocol() and config and config.ssh_key:
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as key_file:
                        key_file.write(config.ssh_key)
                        key_file.flush()
                        os.chmod(key_file.name, 0o600)

                        # 配置 SSH 命令
                        git_ssh_cmd = f"ssh -i {key_file.name} -o StrictHostKeyChecking=no"
                        with git_repo.git.custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                            git_repo.remotes.origin.push()

                        # 清理临时文件
                        os.unlink(key_file.name)
                else:
                    # 处理 HTTPS 认证
                    if config and config.https_username and config.https_password:
                        origin = git_repo.remotes.origin
                        url = repo.get_clone_url()
                        origin.set_url(url)

                    git_repo.remotes.origin.push()

                messages.success(request, f"仓库 {repo.name} 提交并推送成功")
            else:
                messages.info(request, f"仓库 {repo.name} 没有需要提交的更改")
        except Exception as e:
            messages.error(request, f"仓库推送失败：{str(e)}")

        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

    def clear_repository(self, request, repo_id):
        """移除仓库"""
        try:
            repo = Repository.objects.get(id=repo_id)
            repo_name = repo.name

            # 删除本地目录
            local_path = repo.get_local_path()
            if local_path and os.path.exists(local_path):
                try:
                    shutil.rmtree(local_path)
                except Exception as e:
                    messages.warning(
                        request,
                        f"删除本地仓库文件失败：{str(e)}，但将继续删除数据库记录",
                    )

            # 删除数据库记录
            repo.delete()

            messages.success(request, f"仓库 {repo_name} 已成功移除")
        except Repository.DoesNotExist:
            messages.error(request, "仓库不存在")
        except Exception as e:
            messages.error(request, f"移除仓库失败：{str(e)}")

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
                    git_repo = git.Repo(repo.get_local_path())
                    git_repo.git.fetch("--all")

                    # 检查分支是否存在
                    if new_branch not in repo.branches:
                        self.message_user(
                            request,
                            f"分支 {new_branch} 不存在。\n"
                            f"可用的分支有：\n"
                            + "\n".join(f"- {branch}" for branch in repo.branches),
                            level=messages.ERROR,
                        )
                        return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

                    # 切换到新分支
                    git_repo.git.checkout(new_branch)

                # 更新分支
                repo.branch = new_branch
                repo.save()

                self.message_user(request, f"分支已修改为：{new_branch}")
                return HttpResponseRedirect(reverse("admin:grading_repository_changelist"))

            # 显示分支选择页面
            context = {
                "title": "修改分支",
                "repo": repo,
                "branches": repo.branches,  # 使用保存的分支列表
                "current_branch": repo.branch,
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


# 注册其他模型
admin_site.register(Student, StudentAdmin)
admin_site.register(Assignment, AssignmentAdmin)
admin_site.register(Submission, SubmissionAdmin)
admin_site.register(Repository, RepositoryAdmin)
admin_site.register(GlobalConfig, GlobalConfigAdmin)
