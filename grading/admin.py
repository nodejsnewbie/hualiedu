import logging
import os
import shutil
import subprocess
import tempfile

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
    CourseSchedule,
    CourseWeekSchedule,
    GlobalConfig,
    GradeTypeConfig,
    Repository,
    Semester,
    SemesterTemplate,
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

    list_display = ("user", "tenant", "repo_base_dir", "is_tenant_admin", "created_at")
    list_filter = ("tenant", "is_tenant_admin", "created_at")
    search_fields = ("user__username", "user__email", "tenant__name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    """租户配置管理界面"""

    list_display = ("tenant", "key", "value", "created_at", "updated_at")
    list_filter = ("tenant", "created_at")
    search_fields = ("tenant__name", "key", "value")
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at")


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
        fields = ["name", "path", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "输入仓库名称",
                }
            ),
            "path": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "style": "width: 100%;",
                    "placeholder": "仓库路径，相对于基础目录",
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
        path = cleaned_data.get("path")

        if name and path:
            # 验证名称唯一性（在同一租户内）
            existing = Repository.objects.filter(name=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("该仓库名称已存在")

        return cleaned_data

    class Media:
        js = ("admin/js/repository_form.js",)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    form = RepositoryForm
    list_display = (
        "name",
        "path",
        "description",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "path", "description")
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
                        "fields": ("name", "path", "description"),
                        "description": "输入仓库信息，包括名称、路径和描述。",
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


class SemesterTemplateAdmin(admin.ModelAdmin):
    """学期模板管理界面"""

    list_display = (
        "season",
        "start_month_day",
        "end_month_day",
        "duration_weeks",
        "name_pattern",
        "is_active",
        "created_at",
    )
    list_filter = ("season", "is_active", "created_at")
    search_fields = ("name_pattern",)
    ordering = ("season", "-created_at")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("基本信息", {"fields": ("season", "name_pattern", "is_active")}),
        (
            "时间配置",
            {"fields": (("start_month", "start_day"), ("end_month", "end_day"), "duration_weeks")},
        ),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def start_month_day(self, obj):
        """显示开始月日"""
        return f"{obj.start_month}月{obj.start_day}日"

    start_month_day.short_description = "开始日期"

    def end_month_day(self, obj):
        """显示结束月日"""
        return f"{obj.end_month}月{obj.end_day}日"

    end_month_day.short_description = "结束日期"

    def save_model(self, request, obj, form, change):
        """保存前验证数据"""
        try:
            obj.clean()
            super().save_model(request, obj, form, change)
            messages.success(request, f"学期模板 '{obj}' 保存成功")
        except ValidationError as e:
            messages.error(request, f"保存失败: {e}")

    def get_queryset(self, request):
        """自定义查询集"""
        return super().get_queryset(request).select_related()


class CourseScheduleInline(admin.TabularInline):
    """课程安排内联编辑"""

    model = CourseSchedule
    extra = 1
    fields = ("weekday", "period", "start_week", "end_week")


class CourseAdmin(admin.ModelAdmin):
    """课程管理界面"""

    list_display = ("name", "semester", "teacher", "class_name", "location", "created_at")
    list_filter = ("semester", "teacher", "created_at")
    search_fields = ("name", "description", "location", "class_name")
    ordering = ("semester", "name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CourseScheduleInline]

    def get_queryset(self, request):
        """只显示当前用户的课程"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(teacher=request.user)
        return qs


class CourseScheduleAdmin(admin.ModelAdmin):
    """课程安排管理界面"""

    list_display = (
        "course",
        "weekday",
        "period",
        "start_week",
        "end_week",
        "get_week_schedule_text",
    )
    list_filter = ("weekday", "period", "course__semester")
    search_fields = ("course__name",)
    ordering = ("weekday", "period")

    def get_week_schedule_text(self, obj):
        return obj.get_week_schedule_text()

    get_week_schedule_text.short_description = "周次安排"


class CourseWeekScheduleAdmin(admin.ModelAdmin):
    """课程周次安排管理界面"""

    list_display = ("course_schedule", "week_number", "is_active", "created_at")
    list_filter = ("is_active", "course_schedule__course__semester")
    search_fields = ("course_schedule__course__name",)
    ordering = ("course_schedule", "week_number")


# 注册校历相关模型
admin_site.register(Semester, SemesterAdmin)
admin_site.register(SemesterTemplate, SemesterTemplateAdmin)
admin_site.register(Course, CourseAdmin)
admin_site.register(CourseSchedule, CourseScheduleAdmin)
admin_site.register(CourseWeekSchedule, CourseWeekScheduleAdmin)
