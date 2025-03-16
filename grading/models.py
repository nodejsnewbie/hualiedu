from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from pathlib import Path
import os

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
    https_username = models.CharField('HTTPS用户名', max_length=100, blank=True, null=True,
                                    help_text='用于访问私有仓库的HTTPS认证用户名')
    https_password = models.CharField('HTTPS密码', max_length=100, blank=True, null=True,
                                    help_text='用于访问私有仓库的HTTPS认证密码')
    ssh_key = models.TextField('SSH私钥', blank=True, null=True,
                             help_text='SSH私钥内容，包含BEGIN和END行')
    ssh_key_file = models.FileField('SSH私钥文件', upload_to='ssh_keys/', blank=True, null=True,
                                   help_text='上传SSH私钥文件（.pem或.key格式）')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def clean(self):
        # 验证SSH密钥格式
        if self.ssh_key and not (
            self.ssh_key.strip().startswith('-----BEGIN') and 
            'PRIVATE KEY-----' in self.ssh_key
        ):
            raise ValidationError({
                'ssh_key': 'SSH私钥格式不正确，请确保包含完整的BEGIN和END行'
            })
        
        # 如果上传了文件，读取文件内容
        if self.ssh_key_file:
            try:
                self.ssh_key = self.ssh_key_file.read().decode('utf-8')
                self.ssh_key_file = None  # 清除文件字段，只保存内容
            except Exception as e:
                raise ValidationError({
                    'ssh_key_file': f'无法读取SSH私钥文件：{str(e)}'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        if GlobalConfig.objects.exists() and not self.pk:
            raise ValidationError('只能创建一个全局配置')
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = '全局配置'
        verbose_name_plural = '全局配置'

    def __str__(self):
        return f'全局配置 #{self.id}'

class Repository(models.Model):
    name = models.CharField('仓库名称', max_length=100, blank=True)
    url = models.CharField('仓库地址', max_length=255, help_text='支持 HTTPS 和 SSH 协议')
    branch = models.CharField('分支', max_length=100, default='main')
    local_path = models.CharField('本地路径', max_length=255)
    last_sync = models.DateTimeField('最后同步时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '作业仓库'
        verbose_name_plural = '作业仓库'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

    @staticmethod
    def generate_name_from_url(url):
        """从仓库 URL 生成仓库名称"""
        # 移除协议前缀
        if '://' in url:
            url = url.split('://', 1)[1]
        elif '@' in url:
            url = url.split('@', 1)[1]

        # 移除 .git 后缀
        if url.endswith('.git'):
            url = url[:-4]

        # 处理 SSH 和 HTTPS 格式
        parts = url.replace(':', '/').split('/')
        if len(parts) >= 2:
            # 使用最后两部分作为名称
            name = f"{parts[-2]}_{parts[-1]}"
        else:
            name = parts[-1]

        # 清理名称，只保留字母、数字、下划线
        import re
        name = re.sub(r'[^\w\-]', '_', name)
        return name

    def get_clone_url(self):
        """获取克隆 URL，添加认证信息"""
        config = GlobalConfig.objects.first()
        if not config:
            return self.url

        if self.url.startswith('git@') or self.url.startswith('ssh://'):
            return self.url
        elif config.https_username and config.https_password:
            # HTTPS 协议，添加认证信息
            base_url = self.url.replace('https://', '')
            return f'https://{config.https_username}:{config.https_password}@{base_url}'
        return self.url

    def get_local_path(self):
        """获取本地仓库路径"""
        from django.conf import settings
        import os
        return os.path.join(settings.MEDIA_ROOT, 'repo', self.name)

    def is_ssh_protocol(self):
        """判断是否是 SSH 协议"""
        return self.url.startswith('git@') or self.url.startswith('ssh://')