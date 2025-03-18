from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from pathlib import Path
import os
import time
import random
import string

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
    """Git 仓库模型"""
    name = models.CharField(max_length=100, unique=True)
    url = models.CharField(max_length=255, help_text='支持 SSH 和 HTTPS 格式。SSH 格式示例：git@gitee.com:username/repository.git，HTTPS 格式示例：https://gitee.com/username/repository.git')
    branch = models.CharField(max_length=100, default='main')
    local_path = models.CharField(max_length=255, blank=True)
    last_sync_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '仓库'
        verbose_name_plural = '仓库'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_local_path(self):
        """获取本地仓库路径"""
        if not self.local_path:
            # 使用仓库名称作为目录名
            repo_name = self.name
            # 确保 media/repo 目录存在
            repo_dir = os.path.join(settings.MEDIA_ROOT, 'repo')
            os.makedirs(repo_dir, exist_ok=True)
            # 设置仓库的本地路径
            self.local_path = os.path.join(repo_dir, repo_name)
            self.save()  # 保存更新后的路径
        return self.local_path

    def is_cloned(self):
        """检查仓库是否已克隆"""
        local_path = self.get_local_path()
        return os.path.exists(local_path) and os.path.exists(os.path.join(local_path, '.git'))

    def get_clone_url(self):
        """获取克隆 URL"""
        if not self.url:
            raise ValueError('仓库 URL 不能为空')

        config = GlobalConfig.objects.first()
        if not config:
            return self.url

        if self.is_ssh_protocol():
            return self.url
        else:
            # 使用 HTTPS 认证
            if config.https_username and config.https_password:
                # 在 URL 中插入用户名和密码
                url_parts = self.url.split('://')
                if len(url_parts) == 2:
                    return f"{url_parts[0]}://{config.https_username}:{config.https_password}@{url_parts[1]}"
            return self.url

    def is_ssh_protocol(self):
        """检查是否使用 SSH 协议"""
        return self.url.startswith('git@') or self.url.startswith('ssh://')

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