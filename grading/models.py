from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from pathlib import Path
import os
import time
import random
import string
from urllib.parse import urlparse, urlunparse

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    class Meta:
        ordering = ['student_id']

class Assignment(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-due_date']

class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', '待评分'),
        ('graded', '已评分'),
        ('late', '逾期提交'),
        ('failed', '未通过'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    repository_url = models.URLField()

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['student', 'assignment']

class GlobalConfig(models.Model):
    """全局配置"""
    https_username = models.CharField(max_length=100, blank=True, null=True, help_text='HTTPS 认证用户名')
    https_password = models.CharField(max_length=100, blank=True, null=True, help_text='HTTPS 认证密码')
    ssh_key = models.TextField(blank=True, null=True, help_text='SSH 私钥内容')
    ssh_key_file = models.FileField(upload_to='ssh_keys/', null=True, blank=True, help_text='SSH 私钥文件')
    repo_base_dir = models.CharField(max_length=255, default='~/repo', help_text='仓库克隆的基础目录，默认为 ~/repo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '全局配置'
        verbose_name_plural = '全局配置'

    def __str__(self):
        if self.updated_at:
            return f'全局配置 ({self.updated_at.strftime("%Y-%m-%d %H:%M")})'
        return '全局配置'

    @classmethod
    def get_or_create_config(cls):
        """获取或创建全局配置实例"""
        config, created = cls.objects.get_or_create(
            defaults={
                'https_username': '',
                'https_password': '',
                'ssh_key': '',
                'repo_base_dir': '~/repo'
            }
        )
        return config

    def clean(self):
        """验证模型数据"""
        super().clean()
        # 验证 HTTPS 认证信息
        if bool(self.https_username) != bool(self.https_password):
            raise ValidationError('HTTPS 用户名和密码必须同时提供或同时为空')
        
        # 验证 SSH 密钥
        if self.ssh_key:
            key_content = self.ssh_key.strip()
            if not (key_content.startswith('-----BEGIN') and key_content.endswith('PRIVATE KEY-----')):
                raise ValidationError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件')

    def save(self, *args, **kwargs):
        """保存模型数据"""
        # 确保只有一个实例
        if not self.pk and GlobalConfig.objects.exists():
            raise ValidationError('只能创建一个全局配置实例')
        super().save(*args, **kwargs)

class Repository(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.CharField(max_length=255, unique=True)
    branch = models.CharField(max_length=255, default='main')
    _branches = models.JSONField(default=list, help_text='仓库的所有分支列表', db_column='branches')
    last_sync_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def branches(self):
        """获取分支列表"""
        return self._branches if isinstance(self._branches, list) else []

    @branches.setter
    def branches(self, value):
        """设置分支列表"""
        self._branches = value if isinstance(value, list) else []

    def get_local_path(self):
        """获取本地路径"""
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return None
        return os.path.join(config.repo_base_dir, self.name)

    def is_cloned(self):
        """检查仓库是否已克隆"""
        local_path = self.get_local_path()
        return local_path and os.path.exists(local_path)

    def is_ssh_protocol(self):
        """检查是否使用 SSH 协议"""
        return self.url.startswith('git@') or self.url.startswith('ssh://')

    def get_clone_url(self):
        """获取克隆 URL"""
        config = GlobalConfig.objects.first()
        if not config:
            return self.url

        if self.is_ssh_protocol():
            return self.url
        else:
            # 从 URL 中提取用户名和密码
            parsed = urlparse(self.url)
            netloc = f"{config.https_username}:{config.https_password}@{parsed.netloc}"
            return urlunparse(parsed._replace(netloc=netloc))

    @staticmethod
    def generate_name_from_url(url):
        """从 URL 生成仓库名称"""
        # 生成随机字符串
        def random_string(length=8):
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        
        # 移除 .git 后缀（如果有）
        url = url.replace('.git', '')
        
        # 分割主机和路径
        if url.startswith('git@'):
            # SSH 格式：git@host:username/repository
            parts = url.split(':')
            if len(parts) == 2:
                path_parts = parts[1].split('/')
                if len(path_parts) >= 2:
                    # 使用用户名和仓库名，添加随机字符串
                    return f"{path_parts[-2]}_{path_parts[-1]}_{random_string()}"
        elif url.startswith('http://') or url.startswith('https://'):
            # HTTPS 格式：https://host/username/repository
            path_parts = url.split('/')
            if len(path_parts) >= 4:
                # 使用用户名和仓库名，添加随机字符串
                return f"{path_parts[-2]}_{path_parts[-1]}_{random_string()}"
        
        # 如果无法解析，使用 URL 的最后一部分
        return f"repo_{random_string()}"