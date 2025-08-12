import logging
import os
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

# 获取日志记录器
logger = logging.getLogger(__name__)


def get_default_branches():
    return ["main"]


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


class Submission(models.Model):
    STATUS_CHOICES = [
        ("pending", "待评分"),
        ("graded", "已评分"),
        ("late", "逾期提交"),
        ("failed", "未通过"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    comments = models.TextField(blank=True)
    repository_url = models.URLField()
    teacher_comments = models.TextField(blank=True, null=True, verbose_name="教师评价")

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = ["student", "assignment"]


class GlobalConfig(models.Model):
    """全局配置"""

    https_username = models.CharField(
        max_length=100, blank=True, null=True, help_text="HTTPS 认证用户名"
    )
    https_password = models.CharField(
        max_length=100, blank=True, null=True, help_text="HTTPS 认证密码"
    )
    ssh_key = models.TextField(blank=True, null=True, help_text="SSH 私钥内容")
    ssh_key_file = models.FileField(
        upload_to="ssh_keys/", null=True, blank=True, help_text="SSH 私钥文件"
    )
    repo_base_dir = models.CharField(
        max_length=255, default="~/jobs", help_text="仓库克隆的基础目录，默认为 ~/jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "全局配置"
        verbose_name_plural = "全局配置"

    def __str__(self):
        return f"GlobalConfig(id={self.id}, repo_base_dir={self.repo_base_dir})"

    @classmethod
    def get_or_create_config(cls):
        """获取或创建全局配置实例"""
        config, created = cls.objects.get_or_create(
            defaults={
                "repo_base_dir": "~/jobs",
            }
        )
        return config

    def clean(self):
        """验证配置"""
        if self.repo_base_dir:
            # 检查路径是否有效
            expanded_path = os.path.expanduser(self.repo_base_dir)
            if not os.path.exists(expanded_path):
                try:
                    os.makedirs(expanded_path, exist_ok=True)
                except Exception as e:
                    raise ValidationError(f"无法创建目录 {expanded_path}: {str(e)}")

    def save(self, *args, **kwargs):
        """保存前验证"""
        self.clean()
        super().save(*args, **kwargs)


class Repository(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255, unique=True)
    branch = models.CharField(max_length=255, default="main")
    _branches = models.JSONField(
        default=get_default_branches, help_text="仓库的所有分支列表", db_column="branches"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, help_text="仓库所有者"
    )
    last_sync_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name", "owner")

    def __str__(self):
        return f"Repository(id={self.id}, name={self.name}, branch={self.branch})"

    @property
    def branches(self):
        """获取分支列表"""
        if self._branches is None:
            return ["main"]
        return self._branches

    @branches.setter
    def branches(self, value):
        """设置分支列表"""
        if isinstance(value, list):
            self._branches = value
        else:
            self._branches = list(value) if value else []

    def get_local_path(self):
        """获取本地路径"""
        config = GlobalConfig.get_or_create_config()
        base_dir = os.path.expanduser(config.repo_base_dir)
        return os.path.join(base_dir, self.name)

    def is_cloned(self):
        """检查是否已克隆"""
        local_path = self.get_local_path()
        return os.path.exists(local_path) and os.path.exists(os.path.join(local_path, ".git"))

    def is_ssh_protocol(self):
        """检查是否为SSH协议"""
        return self.url.startswith("git@") or self.url.startswith("ssh://")

    def get_clone_url(self):
        """获取克隆URL"""
        # 如果有SSH密钥配置，使用SSH URL
        config = GlobalConfig.get_or_create_config()
        if config.ssh_key or config.ssh_key_file:
            if self.url.startswith("https://"):
                # 将HTTPS URL转换为SSH URL
                parsed = urlparse(self.url)
                return f"git@{parsed.netloc}:{parsed.path.lstrip('/')}"
        return self.url

    @staticmethod
    def generate_name_from_url(url):
        """从URL生成仓库名称"""
        parsed = urlparse(url)
        name = os.path.splitext(os.path.basename(parsed.path))[0]
        return name if name else "unknown"

    def clean(self):
        """验证仓库配置"""
        if not self.name:
            self.name = self.generate_name_from_url(self.url)

    def save(self, *args, **kwargs):
        """保存前验证"""
        self.clean()
        super().save(*args, **kwargs)


class GradeTypeConfig(models.Model):
    """评分类型配置模型"""

    GRADE_TYPE_CHOICES = [
        ("letter", "字母等级 (A/B/C/D/E)"),
        ("text", "文本等级 (优秀/良好/中等/及格/不及格)"),
        ("numeric", "数字等级 (90-100/80-89/70-79/60-69/0-59)"),
    ]

    # 班级标识（可以是班级名称或路径）
    class_identifier = models.CharField(
        max_length=255, unique=True, help_text="班级标识，如班级名称或路径"
    )

    # 评分类型
    grade_type = models.CharField(
        max_length=20, choices=GRADE_TYPE_CHOICES, default="letter", help_text="评分类型"
    )

    # 是否已锁定（第一次评分后锁定）
    is_locked = models.BooleanField(default=False, help_text="是否已锁定评分类型")

    # 创建和更新时间
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_grade_type_config"
        verbose_name = "评分类型配置"
        verbose_name_plural = "评分类型配置"

    def __str__(self):
        return f"{self.class_identifier} - {self.get_grade_type_display()}"

    def lock_grade_type(self):
        """锁定评分类型"""
        self.is_locked = True
        self.save()

    def can_change_grade_type(self):
        """检查是否可以更改评分类型"""
        return not self.is_locked
