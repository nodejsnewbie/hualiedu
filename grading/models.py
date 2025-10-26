
import logging
import os
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
    # 租户级别的仓库目录（相对于全局基础目录）
    tenant_repo_dir = models.CharField(
        max_length=255, 
        help_text="租户仓库目录（相对于全局基础目录）",
        default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_tenant"
        verbose_name = "租户"
        verbose_name_plural = "租户"

    def __str__(self):
        return self.name
    
    def get_full_repo_path(self):
        """获取租户的完整仓库路径"""
        global_base = GlobalConfig.get_value("global_repo_base_dir", "~/jobs")
        expanded_base = os.path.expanduser(global_base)
        # 确保路径使用正确的分隔符
        expanded_base = os.path.normpath(expanded_base)
        if self.tenant_repo_dir:
            return os.path.normpath(os.path.join(expanded_base, self.tenant_repo_dir))
        return os.path.normpath(os.path.join(expanded_base, self.name))


class TenantConfig(models.Model):
    """租户配置 - 每个租户的独立配置（SSH/HTTPS等）"""
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
        return f"{self.tenant.name} - {self.key}"

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


class UserProfile(models.Model):
    """用户配置文件 - 扩展Django User模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users", help_text="所属租户"
    )
    is_tenant_admin = models.BooleanField(default=False, help_text="是否为租户管理员")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_user_profile"
        verbose_name = "用户配置文件"
        verbose_name_plural = "用户配置文件"

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"


class GlobalConfig(models.Model):
    """全局配置 - 超级管理员配置"""
    key = models.CharField(max_length=100, unique=True, help_text="配置键")
    value = models.TextField(help_text="配置值")
    description = models.TextField(blank=True, help_text="配置描述")
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


class Student(models.Model):
    """学生模型 - 添加租户支持"""
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="students", 
        null=True, blank=True, help_text="所属租户"
    )
    student_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    class Meta:
        ordering = ["student_id"]
        unique_together = ["tenant", "student_id"]  # 租户内学号唯一


class Assignment(models.Model):
    """作业模型 - 添加租户支持"""
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="assignments",
        null=True, blank=True, help_text="所属租户"
    )
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
    """仓库模型 - 保留原有字段并添加租户支持"""
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="repositories",
        null=True, blank=True, help_text="所属租户"
    )
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255, help_text="仓库URL", default="", blank=True)
    branch = models.CharField(max_length=255, default="main")
    _branches = models.JSONField(
        default=get_default_branches, help_text="仓库的所有分支列表", db_column="branches"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, help_text="仓库所有者"
    )
    last_sync_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, help_text="仓库描述")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_repository"
        verbose_name = "仓库"
        verbose_name_plural = "仓库"
        unique_together = ["tenant", "url"]  # 租户内URL唯一

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "全局"
        return f"{tenant_name} - {self.name}"

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
        if self.tenant:
            base_dir = self.tenant.get_full_repo_path()
        else:
            # 全局仓库使用全局基础目录
            base_dir = os.path.expanduser(GlobalConfig.get_value("global_repo_base_dir", "~/jobs"))
            base_dir = os.path.normpath(base_dir)
        return os.path.normpath(os.path.join(base_dir, self.name))

    def is_cloned(self):
        """检查是否已克隆"""
        local_path = self.get_local_path()
        return os.path.exists(local_path) and os.path.exists(os.path.join(local_path, ".git"))
    
    def get_actual_branches(self):
        """获取仓库的实际分支列表"""
        if not self.is_cloned():
            return self.branches  # 返回保存的分支列表
        
        try:
            import git
            import subprocess
            
            local_path = self.get_local_path()
            
            # 使用git命令获取所有分支（包括远程分支）
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                branches = []
                current_branch = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 当前分支标记为 * branch_name
                    if line.startswith('* '):
                        current_branch = line[2:].strip()
                        if current_branch not in branches:
                            branches.append(current_branch)
                    # 本地分支
                    elif not line.startswith('remotes/'):
                        if line not in branches:
                            branches.append(line)
                    # 远程分支 remotes/origin/branch_name
                    elif line.startswith('remotes/origin/') and '->' not in line:
                        branch_name = line.replace('remotes/origin/', '')
                        if branch_name not in branches:
                            branches.append(branch_name)
                
                # 更新保存的分支列表
                if branches:
                    self.branches = branches
                    self.save(update_fields=['_branches'])
                
                return branches
            else:
                # 如果命令失败，返回保存的分支列表
                return self.branches
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"获取仓库 {self.name} 分支列表失败: {e}")
            return self.branches
    
    def get_current_branch(self):
        """获取当前分支"""
        if not self.is_cloned():
            return self.branch
        
        try:
            import subprocess
            
            local_path = self.get_local_path()
            
            # 获取当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                current_branch = result.stdout.strip()
                # 如果当前分支与保存的不同，更新数据库
                if current_branch != self.branch:
                    self.branch = current_branch
                    self.save(update_fields=['branch'])
                return current_branch
            else:
                return self.branch
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"获取仓库 {self.name} 当前分支失败: {e}")
            return self.branch

    def is_ssh_protocol(self):
        """检查是否为SSH协议"""
        return self.url.startswith("git@") or self.url.startswith("ssh://")

    def get_clone_url(self):
        """获取克隆URL，根据租户认证配置智能选择"""
        if not self.tenant:
            return self.url
        
        # 获取租户的默认认证方式
        default_auth = TenantConfig.get_value(self.tenant, "default_auth_method", "https")
        
        # 检查租户的认证配置
        has_ssh_key = bool(TenantConfig.get_value(self.tenant, "ssh_private_key"))
        has_https_auth = bool(
            TenantConfig.get_value(self.tenant, "https_username") or 
            TenantConfig.get_value(self.tenant, "https_token")
        )
        
        # 如果URL已经是SSH格式，检查是否有SSH密钥
        if self.url.startswith("git@") or self.url.startswith("ssh://"):
            if has_ssh_key:
                return self.url
            elif has_https_auth:
                # 尝试转换为HTTPS URL
                return self.convert_ssh_to_https(self.url)
            else:
                return self.url  # 返回原URL，让用户配置认证
        
        # 如果URL是HTTPS格式
        if self.url.startswith("https://"):
            # 根据默认认证方式和可用认证决定
            if default_auth == "ssh" and has_ssh_key:
                return self.convert_https_to_ssh(self.url)
            elif has_https_auth:
                return self.url
            elif has_ssh_key:
                return self.convert_https_to_ssh(self.url)
            else:
                return self.url  # 返回原URL，让用户配置认证
        
        return self.url
    
    def convert_https_to_ssh(self, https_url):
        """将HTTPS URL转换为SSH URL"""
        try:
            parsed = urlparse(https_url)
            if parsed.netloc and parsed.path:
                return f"git@{parsed.netloc}:{parsed.path.lstrip('/')}"
        except:
            pass
        return https_url
    
    def convert_ssh_to_https(self, ssh_url):
        """将SSH URL转换为HTTPS URL"""
        try:
            if ssh_url.startswith("git@"):
                # git@github.com:user/repo.git -> https://github.com/user/repo.git
                parts = ssh_url.replace("git@", "").split(":")
                if len(parts) == 2:
                    host, path = parts
                    return f"https://{host}/{path}"
            elif ssh_url.startswith("ssh://"):
                # ssh://git@github.com/user/repo.git -> https://github.com/user/repo.git
                parsed = urlparse(ssh_url)
                if parsed.netloc and parsed.path:
                    return f"https://{parsed.netloc}{parsed.path}"
        except:
            pass
        return ssh_url
    
    def get_auth_config(self):
        """获取仓库的认证配置"""
        if not self.tenant:
            return None
        
        clone_url = self.get_clone_url()
        
        if clone_url.startswith("git@") or clone_url.startswith("ssh://"):
            # SSH认证
            return {
                'method': 'ssh',
                'private_key': TenantConfig.get_value(self.tenant, "ssh_private_key"),
                'passphrase': TenantConfig.get_value(self.tenant, "ssh_key_passphrase"),
                'user_name': TenantConfig.get_value(self.tenant, "git_user_name"),
                'user_email': TenantConfig.get_value(self.tenant, "git_user_email"),
            }
        else:
            # HTTPS认证
            return {
                'method': 'https',
                'username': TenantConfig.get_value(self.tenant, "https_username"),
                'password': TenantConfig.get_value(self.tenant, "https_password"),
                'token': TenantConfig.get_value(self.tenant, "https_token"),
                'user_name': TenantConfig.get_value(self.tenant, "git_user_name"),
                'user_email': TenantConfig.get_value(self.tenant, "git_user_email"),
            }

    @staticmethod
    def generate_name_from_url(url):
        """从URL生成仓库名称"""
        parsed = urlparse(url)
        name = os.path.splitext(os.path.basename(parsed.path))[0]
        return name if name else "unknown"


class Submission(models.Model):
    """提交模型 - 保留原有字段并添加租户支持"""
    STATUS_CHOICES = [
        ("pending", "待评分"),
        ("graded", "已评分"),
        ("late", "逾期提交"),
        ("failed", "未通过"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="submissions",
        null=True, blank=True, help_text="所属租户"
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions", null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions", null=True, blank=True)
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="submissions",
        null=True, blank=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="提交时间")
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    comments = models.TextField(blank=True)
    repository_url = models.URLField(default="", blank=True)
    teacher_comments = models.TextField(blank=True, null=True, verbose_name="教师评价")
    # 新增字段
    file_name = models.CharField(max_length=255, help_text="文件名", default="")
    file_path = models.CharField(max_length=500, help_text="文件路径", default="")
    file_size = models.BigIntegerField(default=0, help_text="文件大小")
    graded_at = models.DateTimeField(blank=True, help_text="评分时间", null=True)

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    class Meta:
        db_table = "grading_submission"
        verbose_name = "提交"
        verbose_name_plural = "提交"
        ordering = ["-submitted_at"]
        unique_together = ["tenant", "student", "assignment"]  # 租户内学生作业唯一


class GradeTypeConfig(models.Model):
    """评分类型配置模型 - 添加租户支持"""
    GRADE_TYPE_CHOICES = [
        ("letter", "字母等级 (A/B/C/D/E)"),
        ("text", "文本等级 (优秀/良好/中等/及格/不及格)"),
        ("numeric", "数字等级 (90-100/80-89/70-79/60-69/0-59)"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="grade_type_configs",
        null=True, blank=True
    )
    class_identifier = models.CharField(
        max_length=255, help_text="班级标识，如班级名称或路径"
    )
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
        tenant_name = self.tenant.name if self.tenant else "全局"
        return f"{tenant_name} - {self.class_identifier} - {self.get_grade_type_display()}"

    def lock_grade_type(self):
        """锁定评分类型"""
        self.is_locked = True
        self.save()

    def can_change_grade_type(self):
        """检查是否可以更改评分类型"""
        return not self.is_locked


# 学期和课程模型（如果需要的话）
class Semester(models.Model):
    """学期模型"""
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="semesters",
        null=True, blank=True, help_text="所属租户"
    )
    name = models.CharField(max_length=100, help_text="学期名称，如：2024年春季学期")
    start_date = models.DateField(help_text="学期第一周第一天上课日期")
    end_date = models.DateField(help_text="学期结束日期")
    is_active = models.BooleanField(default=True, help_text="是否为当前学期")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_semester"
        verbose_name = "学期"
        verbose_name_plural = "学期"
        ordering = ["-start_date"]
        unique_together = ["tenant", "name"]

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "全局"
        return f"{tenant_name} - {self.name}"


class Course(models.Model):
    """课程模型"""
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="courses",
        null=True, blank=True, help_text="所属租户"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="courses", help_text="所属学期"
    )
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="courses", help_text="授课教师"
    )
    name = models.CharField(max_length=200, help_text="课程名称")
    description = models.TextField(blank=True, help_text="课程描述")
    location = models.CharField(max_length=100, help_text="上课地点")
    class_name = models.CharField(max_length=100, help_text="班级名称", default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_course"
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ["semester", "name"]
        unique_together = ["tenant", "semester", "name"]

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "全局"
        return f"{tenant_name} - {self.name}"
