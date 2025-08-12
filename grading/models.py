import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# 获取日志记录器
logger = logging.getLogger(__name__)


def get_default_branches():
    return ["main"]


class Tenant(models.Model):
    """租户模型 - 支持多租户系统"""

    name = models.CharField(max_length=100, unique=True, help_text="租户名称")
    description = models.TextField(blank=True, help_text="租户描述")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_tenant"
        verbose_name = "租户"
        verbose_name_plural = "租户"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """用户配置文件 - 扩展Django User模型"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users", help_text="所属租户"
    )
    repo_base_dir = models.CharField(max_length=500, blank=True, help_text="用户基础仓库目录")
    is_tenant_admin = models.BooleanField(default=False, help_text="是否为租户管理员")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_user_profile"
        verbose_name = "用户配置文件"
        verbose_name_plural = "用户配置文件"

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"

    def get_repo_base_dir(self):
        """获取用户的基础仓库目录"""
        if self.repo_base_dir:
            return self.repo_base_dir
        # 如果没有配置，使用租户的默认目录
        return self.tenant.default_repo_dir if hasattr(self.tenant, "default_repo_dir") else None


class GlobalConfig(models.Model):
    """全局配置 - 超级管理员配置"""

    key = models.CharField(
        max_length=100, unique=True, help_text="配置键", default="default_repo_base_dir"
    )
    value = models.TextField(help_text="配置值", default="~/jobs")
    description = models.TextField(blank=True, help_text="配置描述", default="默认仓库基础目录")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_global_config"
        verbose_name = "全局配置"
        verbose_name_plural = "全局配置"

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        """获取配置值"""
        try:
            config = cls.objects.get(key=key)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description=""):
        """设置配置值"""
        config, created = cls.objects.get_or_create(
            key=key, defaults={"value": value, "description": description}
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        return config


class TenantConfig(models.Model):
    """租户配置 - 每个租户的独立配置"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="configs")
    key = models.CharField(max_length=100, help_text="配置键")
    value = models.TextField(help_text="配置值")
    description = models.TextField(blank=True, help_text="配置描述")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_tenant_config"
        verbose_name = "租户配置"
        verbose_name_plural = "租户配置"
        unique_together = ["tenant", "key"]

    def __str__(self):
        return f"{self.tenant.name} - {self.key}: {self.value}"

    @classmethod
    def get_value(cls, tenant, key, default=None):
        """获取租户配置值"""
        try:
            config = cls.objects.get(tenant=tenant, key=key)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, tenant, key, value, description=""):
        """设置租户配置值"""
        config, created = cls.objects.get_or_create(
            tenant=tenant, key=key, defaults={"value": value, "description": description}
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        return config


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    class Meta:
        ordering = ["student_id"]


class Assignment(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-due_date"]


class Repository(models.Model):
    """仓库模型 - 支持多租户"""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="repositories", null=True, blank=True
    )
    name = models.CharField(max_length=255, help_text="仓库名称")
    path = models.CharField(max_length=500, help_text="仓库路径", default="")
    description = models.TextField(blank=True, help_text="仓库描述")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_repository"
        verbose_name = "仓库"
        verbose_name_plural = "仓库"
        unique_together = ["tenant", "name"]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

    def get_full_path(self):
        """获取完整路径"""
        user_profile = self.tenant.users.first()
        if user_profile and user_profile.repo_base_dir:
            return f"{user_profile.repo_base_dir}/{self.path}"
        return self.path


class Submission(models.Model):
    """提交模型 - 支持多租户"""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="submissions", null=True, blank=True
    )
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="submissions", null=True, blank=True
    )
    file_path = models.CharField(max_length=500, help_text="文件路径")
    file_name = models.CharField(max_length=255, help_text="文件名")
    file_size = models.BigIntegerField(default=0, help_text="文件大小")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="提交时间")
    graded_at = models.DateTimeField(null=True, blank=True, help_text="评分时间")
    grade = models.CharField(max_length=50, blank=True, help_text="评分")
    comment = models.TextField(blank=True, help_text="评语")

    class Meta:
        db_table = "grading_submission"
        verbose_name = "提交"
        verbose_name_plural = "提交"
        unique_together = ["tenant", "repository", "file_path"]

    def __str__(self):
        return f"{self.tenant.name} - {self.file_name}"

    def save(self, *args, **kwargs):
        if self.grade and not self.graded_at:
            self.graded_at = timezone.now()
        super().save(*args, **kwargs)


class GradeTypeConfig(models.Model):
    """评分类型配置模型 - 支持多租户"""

    GRADE_TYPE_CHOICES = [
        ("letter", "字母等级 (A/B/C/D/E)"),
        ("text", "文本等级 (优秀/良好/中等/及格/不及格)"),
        ("numeric", "数字等级 (90-100/80-89/70-79/60-69/0-59)"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="grade_type_configs", null=True, blank=True
    )
    class_identifier = models.CharField(max_length=255, help_text="班级标识，如班级名称或路径")
    grade_type = models.CharField(
        max_length=20, choices=GRADE_TYPE_CHOICES, default="letter", help_text="评分类型"
    )
    is_locked = models.BooleanField(default=False, help_text="是否已锁定评分类型")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_grade_type_config"
        verbose_name = "评分类型配置"
        verbose_name_plural = "评分类型配置"
        unique_together = ["tenant", "class_identifier"]

    def __str__(self):
        return f"{self.tenant.name} - {self.class_identifier} - {self.get_grade_type_display()}"

    def lock_grade_type(self):
        """锁定评分类型"""
        self.is_locked = True
        self.save()

    def can_change_grade_type(self):
        """检查是否可以更改评分类型"""
        return not self.is_locked
