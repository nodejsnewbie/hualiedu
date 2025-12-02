import logging
import os

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
    tenant_repo_dir = models.CharField(
        max_length=255, default="", help_text="租户仓库目录（相对于全局基础目录）"
    )
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
        # 如果没有配置，使用租户级目录（为空则返回None）
        tenant_dir = getattr(self.tenant, "tenant_repo_dir", "")
        return tenant_dir or None


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


# Old Assignment model removed - was never migrated and not used
# Replaced by new Assignment model for assignment management refactor


class Repository(models.Model):
    """仓库模型 - 用户级仓库管理"""

    REPO_TYPE_CHOICES = [
        ("git", "Git仓库"),
        ("filesystem", "文件系统"),
    ]

    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="repositories",
        null=True,
        blank=True,
        help_text="仓库所有者",
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="repositories", null=True, blank=True
    )
    class_obj = models.ForeignKey(
        "Class",
        on_delete=models.CASCADE,
        related_name="repositories",
        null=True,
        blank=True,
        help_text="关联班级",
    )
    name = models.CharField(max_length=255, help_text="仓库名称")
    path = models.CharField(max_length=500, help_text="仓库路径", default="")
    repo_type = models.CharField(
        max_length=20,
        choices=REPO_TYPE_CHOICES,
        default="filesystem",
        help_text="仓库类型",
    )

    # Git仓库方式字段
    git_url = models.URLField(blank=True, null=True, help_text="Git仓库URL")
    git_branch = models.CharField(max_length=100, blank=True, default="main", help_text="Git分支")
    git_username = models.CharField(max_length=100, blank=True, help_text="Git用户名")
    git_password = models.CharField(max_length=200, blank=True, help_text="Git密码（加密存储）")

    # 文件系统方式字段
    filesystem_path = models.CharField(max_length=500, blank=True, help_text="文件系统路径")
    allocated_space_mb = models.IntegerField(default=1024, help_text="分配空间（MB）")

    # 兼容旧字段
    url = models.URLField(blank=True, help_text="仓库URL（兼容旧版本）")
    branch = models.CharField(max_length=100, default="main", help_text="默认分支（兼容旧版本）")

    description = models.TextField(blank=True, help_text="仓库描述")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    last_sync = models.DateTimeField(null=True, blank=True, help_text="最后同步时间")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_repository"
        verbose_name = "仓库"
        verbose_name_plural = "仓库"
        unique_together = ["owner", "name"]
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["class_obj", "is_active"]),
            models.Index(fields=["repo_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.owner.username} - {self.name}"

    def _get_user_root_base_dir(self) -> str:
        """根据全局基础目录 + 用户名 计算用户仓库根目录。

        最终目录结构：<global_base_dir>/<username>/
        - 全局基础目录仅超级管理员可配置（default_repo_base_dir）
        - 不再使用租户级基础仓库名
        """
        global_base = GlobalConfig.get_value("default_repo_base_dir", "~/jobs") or "~/jobs"
        global_base = os.path.expanduser(global_base)
        username = self.owner.username if self.owner and self.owner.username else "unknown"
        return os.path.join(global_base, username)

    def get_repo_dir_name(self) -> str:
        """获取仓库目录名：
        - 若为 Git 仓库并配置了 URL，则使用远程仓库名（去掉 .git）
        - 否则使用 self.path（去首尾 /），为空时回退 self.name
        """
        if self.is_git_repository():
            try:
                from urllib.parse import urlparse

                parsed = urlparse(self.url)
                # 取路径最后一段
                tail = parsed.path.rstrip("/").split("/")[-1]
                if tail.endswith(".git"):
                    tail = tail[:-4]
                if tail:
                    return tail
            except Exception:
                pass
        if self.path:
            return self.path.strip("/")
        return self.name

    def get_full_path(self):
        """获取仓库在本机的完整路径。
        规则：<global_base>/<username>/<repo_dir_name>
        """
        root = self._get_user_root_base_dir()
        sub_path = self.get_repo_dir_name()
        return os.path.join(root, sub_path)

    def get_display_path(self):
        """获取显示路径"""
        if self.repo_type == "git" and self.url:
            return self.url
        return self.get_full_path()

    def is_git_repository(self):
        """检查是否为Git仓库"""
        return self.repo_type == "git" and bool(self.url)

    def can_sync(self):
        """检查是否可以同步"""
        return self.is_git_repository() and self.is_active


class Submission(models.Model):
    """学生作业提交模型"""

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
        help_text="所属租户",
    )
    homework = models.ForeignKey(
        "Homework",
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
        help_text="所属作业",
    )
    student = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
        help_text="提交学生",
    )
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
        help_text="所属仓库",
    )
    file_path = models.CharField(max_length=500, help_text="文件路径")
    file_name = models.CharField(max_length=200, help_text="文件名")
    file_size = models.IntegerField(default=0, help_text="文件大小（字节）")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="提交时间")
    version = models.IntegerField(default=1, help_text="版本号")
    graded_at = models.DateTimeField(null=True, blank=True, help_text="评分时间")
    grade = models.CharField(max_length=50, blank=True, default="", help_text="评分")
    comment = models.TextField(blank=True, default="", help_text="评语")

    class Meta:
        db_table = "grading_submission"
        verbose_name = "提交"
        verbose_name_plural = "提交"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["homework", "student", "-submitted_at"]),
            models.Index(fields=["repository", "-submitted_at"]),
            models.Index(fields=["tenant", "-submitted_at"]),
            models.Index(fields=["student", "-submitted_at"]),
        ]

    def __str__(self):
        if self.homework and self.student:
            return f"{self.student.username} - {self.homework.title} - v{self.version}"
        return f"{self.file_name} - v{self.version}"

    def save(self, *args, **kwargs):
        if self.grade and not self.graded_at:
            self.graded_at = timezone.now()
        super().save(*args, **kwargs)


class GradeTypeConfig(models.Model):
    """评分类型配置模型 - 支持多租户"""

    GRADE_TYPE_CHOICES = [
        ("letter", "字母等级 (A/B/C/D/E)"),
        ("text", "文本等级 (优秀/良好/中等/及格/不及格)"),
        ("percentage", "百分制 (0-100)"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="grade_type_configs",
        null=True,
        blank=True,
        help_text="所属租户",
    )
    class_obj = models.ForeignKey(
        "Class",
        on_delete=models.CASCADE,
        related_name="grade_type_configs",
        null=True,
        blank=True,
        help_text="关联班级",
    )
    class_identifier = models.CharField(
        max_length=255, blank=True, help_text="班级标识，如班级名称或路径（兼容旧版本）"
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
        indexes = [
            models.Index(fields=["tenant", "class_obj"]),
        ]

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "无租户"
        class_name = self.class_obj.name if self.class_obj else self.class_identifier
        return f"{tenant_name} - {class_name} - {self.get_grade_type_display()}"

    def lock_grade_type(self):
        """锁定评分类型"""
        self.is_locked = True
        self.save()

    def can_change_grade_type(self):
        """检查是否可以更改评分类型"""
        return not self.is_locked


class Semester(models.Model):
    """学期模型"""

    SEASON_CHOICES = [
        ("spring", "春季"),
        ("autumn", "秋季"),
    ]

    name = models.CharField(max_length=100, help_text="学期名称，如：2024年春季学期")
    start_date = models.DateField(help_text="学期第一周第一天上课日期")
    end_date = models.DateField(help_text="学期结束日期")
    is_active = models.BooleanField(default=False, help_text="是否为当前学期")

    # 自动创建相关字段
    auto_created = models.BooleanField(default=False, help_text="是否为自动创建")
    reference_semester = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="参考学期（用于自动创建）",
    )
    season = models.CharField(
        max_length=10, choices=SEASON_CHOICES, null=True, blank=True, help_text="学期季节"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_semester"
        verbose_name = "学期"
        verbose_name_plural = "学期"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["start_date", "end_date"], name="unique_semester_period"
            )
        ]

    def __str__(self):
        return self.name

    def get_week_count(self):
        """获取学期总周数"""
        delta = self.end_date - self.start_date
        return (delta.days // 7) + 1

    def get_week_dates(self, week_number):
        """获取指定周的开始和结束日期"""
        from datetime import timedelta

        start = self.start_date + timedelta(days=(week_number - 1) * 7)
        end = start + timedelta(days=6)
        return start, end

    def get_season(self):
        """获取学期季节"""
        if self.season:
            return self.season

        # 根据开始日期自动判断季节
        # 春季学期：3月-7月开始
        # 秋季学期：8月-2月开始（跨年）
        start_month = self.start_date.month
        if 3 <= start_month <= 7:
            return "spring"
        else:
            return "autumn"

    def is_current_semester(self, current_date=None):
        """判断是否为当前学期"""
        from datetime import date

        if current_date is None:
            current_date = date.today()

        return self.start_date <= current_date <= self.end_date

    def get_next_year_dates(self):
        """获取下一年对应的日期"""
        from datetime import date

        try:
            next_start = self.start_date.replace(year=self.start_date.year + 1)
            next_end = self.end_date.replace(year=self.end_date.year + 1)
            return next_start, next_end
        except ValueError:
            # 处理2月29日的特殊情况
            from datetime import timedelta

            next_start = self.start_date.replace(year=self.start_date.year + 1, month=2, day=28)
            next_end = self.end_date.replace(year=self.end_date.year + 1)
            return next_start, next_end


class SemesterTemplate(models.Model):
    """学期模板配置"""

    SEASON_CHOICES = [
        ("spring", "春季"),
        ("autumn", "秋季"),
    ]

    season = models.CharField(max_length=10, choices=SEASON_CHOICES, help_text="学期季节")
    start_month = models.IntegerField(help_text="开始月份 (1-12)")
    start_day = models.IntegerField(help_text="开始日期 (1-31)")
    end_month = models.IntegerField(help_text="结束月份 (1-12)")
    end_day = models.IntegerField(help_text="结束日期 (1-31)")
    duration_weeks = models.IntegerField(default=16, help_text="学期周数")
    name_pattern = models.CharField(
        max_length=50, help_text="命名模式，如'{year}年{season}'", default="{year}年{season}"
    )
    is_active = models.BooleanField(default=True, help_text="是否启用此模板")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_semester_template"
        verbose_name = "学期模板"
        verbose_name_plural = "学期模板"
        constraints = [
            models.UniqueConstraint(
                fields=["season"],
                condition=models.Q(is_active=True),
                name="unique_active_season_template",
            )
        ]

    def __str__(self):
        return f"{self.get_season_display()}模板"

    def clean(self):
        """验证模板数据"""
        from django.core.exceptions import ValidationError

        # 验证月份范围
        if not (1 <= self.start_month <= 12):
            raise ValidationError("开始月份必须在1-12之间")
        if not (1 <= self.end_month <= 12):
            raise ValidationError("结束月份必须在1-12之间")

        # 验证日期范围
        if not (1 <= self.start_day <= 31):
            raise ValidationError("开始日期必须在1-31之间")
        if not (1 <= self.end_day <= 31):
            raise ValidationError("结束日期必须在1-31之间")

        # 验证学期周数
        if not (1 <= self.duration_weeks <= 52):
            raise ValidationError("学期周数必须在1-52之间")

    def generate_semester_dates(self, year):
        """为指定年份生成学期日期"""
        from datetime import date

        try:
            start_date = date(year, self.start_month, self.start_day)

            # 处理跨年情况
            end_year = year
            if self.season == "autumn" and self.end_month <= 7:
                end_year = year + 1

            end_date = date(end_year, self.end_month, self.end_day)

            return start_date, end_date
        except ValueError as e:
            # 处理无效日期（如2月30日）
            raise ValueError(f"无法生成有效日期: {e}")

    def generate_semester_name(self, year):
        """为指定年份生成学期名称"""
        season_map = {"spring": "春季", "autumn": "秋季"}

        return self.name_pattern.format(year=year, season=season_map.get(self.season, self.season))

    @classmethod
    def get_template_for_season(cls, season):
        """获取指定季节的活跃模板"""
        try:
            return cls.objects.get(season=season, is_active=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_template_for_date(cls, target_date):
        """根据日期获取对应的学期模板"""
        month = target_date.month

        # 根据月份判断季节
        # 春季学期：3月-7月
        # 秋季学期：8月-2月（跨年）
        if 3 <= month <= 7:
            season = "spring"
        else:
            season = "autumn"

        return cls.get_template_for_season(season)

    @classmethod
    def get_current_semester_auto(cls, current_date=None):
        """自动获取当前学期

        使用学期管理器自动识别并返回当前学期

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            当前学期对象，如果没有找到则返回None
        """
        try:
            from grading.services.semester_manager import SemesterManager

            manager = SemesterManager()
            return manager.get_current_semester(current_date)
        except Exception:
            # 如果自动识别失败，回退到数据库查询
            return cls.objects.filter(is_active=True).first()


class Course(models.Model):
    """课程模型"""

    COURSE_TYPE_CHOICES = [
        ("theory", "理论课"),
        ("lab", "实验课"),
        ("practice", "实践课"),
        ("mixed", "理论+实验"),
    ]

    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="courses", help_text="所属学期"
    )
    teacher = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="courses", help_text="授课教师"
    )
    name = models.CharField(max_length=200, help_text="课程名称")
    course_type = models.CharField(
        max_length=20, choices=COURSE_TYPE_CHOICES, default="theory", help_text="课程类型"
    )
    description = models.TextField(blank=True, help_text="课程描述")
    location = models.CharField(max_length=100, blank=True, help_text="上课地点")
    class_name = models.CharField(
        max_length=100, blank=True, help_text="班级名称，如：计算机科学1班"
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True,
        help_text="所属租户",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_course"
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ["semester", "name"]
        indexes = [
            models.Index(fields=["teacher", "semester"]),
            models.Index(fields=["tenant", "semester"]),
        ]

    def __str__(self):
        class_info = f" - {self.class_name}" if self.class_name else ""
        return f"{self.semester.name} - {self.name}{class_info}"


class Class(models.Model):
    """班级模型"""

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="classes",
        null=True,
        blank=True,
        help_text="所属租户",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="classes", help_text="所属课程"
    )
    name = models.CharField(max_length=200, help_text="班级名称")
    student_count = models.IntegerField(default=0, help_text="学生人数")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_class"
        verbose_name = "班级"
        verbose_name_plural = "班级"
        ordering = ["course", "name"]
        indexes = [
            models.Index(fields=["course", "tenant"]),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class CourseSchedule(models.Model):
    """课程安排模型"""

    WEEKDAY_CHOICES = [
        (1, "周一"),
        (2, "周二"),
        (3, "周三"),
        (4, "周四"),
        (5, "周五"),
        (6, "周六"),
        (7, "周日"),
    ]

    PERIOD_CHOICES = [
        (1, "第一大节 (8:00-9:40)"),
        (2, "第二大节 (10:00-11:40)"),
        (3, "第三大节 (14:00-15:40)"),
        (4, "第四大节 (16:00-17:40)"),
        (5, "第五大节 (19:00-20:40)"),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="schedules", help_text="课程"
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, help_text="星期几")
    period = models.IntegerField(choices=PERIOD_CHOICES, help_text="第几大节")
    start_week = models.IntegerField(help_text="开始周次")
    end_week = models.IntegerField(help_text="结束周次")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_course_schedule"
        verbose_name = "课程安排"
        verbose_name_plural = "课程安排"
        ordering = ["weekday", "period"]
        unique_together = ["course", "weekday", "period"]

    def __str__(self):
        return f"{self.course.name} - {self.get_weekday_display()} {self.get_period_display()}"

    def is_in_week(self, week_number):
        """检查是否在指定周次上课"""
        # 首先检查是否在基本周次范围内
        if not (self.start_week <= week_number <= self.end_week):
            return False

        # 检查是否有具体的周次安排
        week_schedule = self.week_schedules.filter(week_number=week_number).first()
        if week_schedule:
            return week_schedule.is_active

        # 如果没有具体安排，检查是否有任何周次安排记录
        if self.week_schedules.exists():
            # 如果有周次安排记录但当前周次没有记录，说明被设置为不上课
            return False
        else:
            # 如果没有任何周次安排记录，默认在基本范围内都上课
            return True

    def get_week_schedule_text(self):
        """获取周次安排文本描述"""
        if self.week_schedules.exists():
            active_weeks = [ws.week_number for ws in self.week_schedules.filter(is_active=True)]
            inactive_weeks = [ws.week_number for ws in self.week_schedules.filter(is_active=False)]

            if active_weeks and inactive_weeks:
                # 检查活跃周次是否连续
                active_weeks.sort()
                continuous_ranges = []
                start = active_weeks[0]
                end = active_weeks[0]

                for i in range(1, len(active_weeks)):
                    if active_weeks[i] == end + 1:
                        end = active_weeks[i]
                    else:
                        if start == end:
                            continuous_ranges.append(str(start))
                        else:
                            continuous_ranges.append(f"{start}-{end}")
                        start = end = active_weeks[i]

                # 处理最后一个范围
                if start == end:
                    continuous_ranges.append(str(start))
                else:
                    continuous_ranges.append(f"{start}-{end}")

                return f"第{', '.join(continuous_ranges)}周（跳过：{', '.join(map(str, inactive_weeks))}周）"
            elif active_weeks:
                return f"第{min(active_weeks)}-{max(active_weeks)}周"
            else:
                return f"第{self.start_week}-{self.end_week}周（无具体安排）"
        else:
            return f"第{self.start_week}-{self.end_week}周"


class CourseWeekSchedule(models.Model):
    """课程周次安排模型 - 支持不连续的周次"""

    course_schedule = models.ForeignKey(
        CourseSchedule,
        on_delete=models.CASCADE,
        related_name="week_schedules",
        help_text="课程安排",
    )
    week_number = models.IntegerField(help_text="周次")
    is_active = models.BooleanField(default=True, help_text="是否在该周上课")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_course_week_schedule"
        verbose_name = "课程周次安排"
        verbose_name_plural = "课程周次安排"
        ordering = ["week_number"]
        unique_together = ["course_schedule", "week_number"]

    def __str__(self):
        status = "上课" if self.is_active else "不上课"
        return f"{self.course_schedule} - 第{self.week_number}周({status})"


class Assignment(models.Model):
    """作业配置模型 - 管理学生作业提交方式

    作业配置定义了学生如何提交作业，支持两种提交方式：
    1. Git仓库方式：学生通过Git仓库提交，系统直接从远程仓库读取
    2. 文件上传方式：学生通过系统上传文件，存储在本地文件系统

    重要特性：
    - 每个作业配置关联一个课程和班级
    - 同一课程的不同班级有独立的作业配置和目录
    - Git方式采用远程直接访问，无需本地克隆
    - 文件上传方式自动创建目录结构：<课程名>/<班级名>/<作业次数>/
    - 支持教师隔离：每个教师只能看到自己创建的作业配置

    术语说明：
    - 本模型原名为 Repository，已重构为 Assignment
    - storage_type 原名为 repo_type
    - 界面上显示为"作业管理"而非"仓库管理"

    设计决策：
    - 采用远程优先架构：Git方式直接访问远程仓库，避免本地存储占用和同步延迟
    - 使用存储抽象层：通过StorageAdapter统一Git和文件系统访问接口
    - 密码加密存储：Git密码使用CredentialEncryption加密后存储在git_password_encrypted字段
    - 路径安全验证：所有文件路径操作都经过PathValidator验证，防止路径遍历攻击

    数据隔离：
    - 教师隔离：通过owner字段确保教师只能访问自己创建的作业配置
    - 租户隔离：通过tenant字段实现多租户数据隔离
    - 班级隔离：通过class_obj字段确保不同班级的作业目录独立

    目录结构示例：
    文件系统方式：
        数据结构/
          ├── 计算机1班/
          │   ├── 第一次作业/
          │   │   ├── 张三-作业1.docx
          │   │   └── 李四-作业1.pdf
          │   └── 第二次作业/
          └── 计算机2班/
              └── 第一次作业/

    Git方式：
        直接从远程仓库读取，无本地目录
    """

    STORAGE_TYPE_CHOICES = [
        ("git", "Git仓库"),
        ("filesystem", "文件上传"),
    ]

    # 基本信息
    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="assignments",
        help_text="作业创建者（教师）",
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="assignments", help_text="所属租户"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments", help_text="关联课程"
    )
    class_obj = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="assignments", help_text="关联班级"
    )
    name = models.CharField(max_length=255, help_text="作业名称")
    description = models.TextField(blank=True, help_text="作业描述")
    storage_type = models.CharField(
        max_length=20, choices=STORAGE_TYPE_CHOICES, default="filesystem", help_text="存储类型"
    )

    # Git 存储配置
    git_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Git仓库URL（支持 http://, https://, git://, ssh://, git@ 格式）",
    )
    git_branch = models.CharField(max_length=100, default="main", blank=True, help_text="Git分支")
    git_username = models.CharField(max_length=100, blank=True, help_text="Git用户名")
    git_password_encrypted = models.CharField(max_length=500, blank=True, help_text="加密的Git密码")

    # 文件系统存储配置
    base_path = models.CharField(max_length=500, blank=True, help_text="文件系统基础路径")

    # 元数据
    is_active = models.BooleanField(default=True, help_text="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_assignment"
        verbose_name = "作业配置"
        verbose_name_plural = "作业配置"
        ordering = ["-created_at"]
        unique_together = ["owner", "course", "class_obj", "name"]
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["course", "class_obj"]),
            models.Index(fields=["storage_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.class_obj.name} - {self.name}"

    def is_git_storage(self):
        """检查是否为Git存储方式

        Returns:
            bool: 如果storage_type为"git"且配置了git_url则返回True

        Note:
            Git方式要求必须配置git_url，否则无法访问远程仓库
        """
        return self.storage_type == "git" and bool(self.git_url)

    def is_filesystem_storage(self):
        """检查是否为文件系统存储方式

        Returns:
            bool: 如果storage_type为"filesystem"则返回True

        Note:
            文件系统方式将文件存储在本地文件系统，通过base_path指定存储位置
        """
        return self.storage_type == "filesystem"

    def get_display_path(self):
        """获取用于界面显示的路径

        Returns:
            str: Git方式返回仓库URL，文件系统方式返回base_path或自动生成的路径

        Examples:
            Git方式: "https://github.com/user/repo.git"
            文件系统方式: "数据结构/计算机1班/"
        """
        if self.is_git_storage():
            return self.git_url
        return self.base_path or f"{self.course.name}/{self.class_obj.name}/"

    def get_storage_config(self):
        """获取存储配置字典

        用于传递给StorageAdapter创建实例。

        Returns:
            dict: 包含存储类型和相关配置的字典

        Examples:
            Git方式:
            {
                "type": "git",
                "url": "https://github.com/user/repo.git",
                "branch": "main",
                "username": "user",
                "password_encrypted": "encrypted_password"
            }

            文件系统方式:
            {
                "type": "filesystem",
                "base_path": "数据结构/计算机1班/"
            }
        """
        if self.is_git_storage():
            return {
                "type": "git",
                "url": self.git_url,
                "branch": self.git_branch,
                "username": self.git_username,
                "password_encrypted": self.git_password_encrypted,
            }
        else:
            return {
                "type": "filesystem",
                "base_path": self.base_path,
            }

    def validate_git_config(self):
        """验证Git配置完整性

        检查Git存储方式的必填字段是否完整。

        Raises:
            ValueError: 如果git_url未配置

        Note:
            - git_url是必填项，用于指定远程仓库地址
            - git_branch如果未配置，自动设置为"main"
            - git_username和git_password_encrypted是可选的，用于私有仓库认证
        """
        if self.storage_type == "git":
            if not self.git_url:
                raise ValueError("Git存储方式必须提供仓库URL")
            if not self.git_branch:
                self.git_branch = "main"

    def validate_filesystem_config(self):
        """验证文件系统配置完整性

        检查文件系统存储方式的必填字段是否完整。
        如果base_path未配置，自动根据课程和班级名称生成。

        Note:
            自动生成的路径格式: <课程名称>/<班级名称>/
            例如: "数据结构/计算机1班/"

            这确保了不同班级的作业文件存储在独立的目录中，
            实现了班级目录隔离（Requirements 7.3）
        """
        if self.storage_type == "filesystem":
            if not self.base_path:
                # 自动生成基础路径
                # 格式: <课程名称>/<班级名称>/
                course_name = self.course.name if self.course else "未知课程"
                class_name = self.class_obj.name if self.class_obj else "未知班级"
                self.base_path = f"{course_name}/{class_name}/"

    def clean(self):
        """Django模型验证方法

        在保存前自动调用，用于验证模型数据的完整性和一致性。

        Raises:
            ValidationError: 如果验证失败

        Note:
            这个方法会根据storage_type调用相应的验证方法：
            - Git方式: validate_git_config()
            - 文件系统方式: validate_filesystem_config()
        """
        from django.core.exceptions import ValidationError

        # 验证存储配置
        try:
            if self.storage_type == "git":
                self.validate_git_config()
            else:
                self.validate_filesystem_config()
        except ValueError as e:
            raise ValidationError(str(e))

    def save(self, *args, **kwargs):
        """保存模型实例

        重写save方法以在保存前执行完整的模型验证。

        Note:
            调用full_clean()确保所有验证规则都被执行，
            包括字段验证、clean()方法和unique约束检查。
        """
        self.full_clean()
        super().save(*args, **kwargs)


class Homework(models.Model):
    """作业模型 - 管理每次作业"""

    HOMEWORK_TYPE_CHOICES = [
        ("normal", "普通作业"),
        ("lab_report", "实验报告"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="homeworks",
        null=True,
        blank=True,
        help_text="所属租户",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="homeworks", help_text="所属课程"
    )
    class_obj = models.ForeignKey(
        "Class",
        on_delete=models.CASCADE,
        related_name="homeworks",
        null=True,
        blank=True,
        help_text="所属班级",
    )
    title = models.CharField(max_length=200, help_text="作业标题")
    homework_type = models.CharField(
        max_length=20, choices=HOMEWORK_TYPE_CHOICES, default="normal", help_text="作业类型"
    )
    description = models.TextField(blank=True, help_text="作业描述")
    due_date = models.DateTimeField(null=True, blank=True, help_text="截止日期")
    folder_name = models.CharField(
        max_length=200, help_text="作业文件夹名称（用于匹配文件系统中的目录）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_homework"
        verbose_name = "作业"
        verbose_name_plural = "作业"
        ordering = ["course", "-created_at"]
        unique_together = ["course", "folder_name"]
        indexes = [
            models.Index(fields=["course", "folder_name"]),
            models.Index(fields=["tenant", "homework_type"]),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.title} ({self.get_homework_type_display()})"

    def is_lab_report(self):
        """判断是否为实验报告"""
        return self.homework_type == "lab_report"


class CommentTemplate(models.Model):
    """评价模板模型"""

    TEMPLATE_TYPE_CHOICES = [
        ("personal", "个人模板"),
        ("system", "系统模板"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="comment_templates", help_text="所属租户"
    )
    teacher = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="comment_templates",
        blank=True,
        null=True,
        help_text="教师（个人模板有teacher）",
    )
    template_type = models.CharField(
        max_length=20, choices=TEMPLATE_TYPE_CHOICES, help_text="模板类型"
    )
    comment_text = models.TextField(help_text="评价内容")
    usage_count = models.IntegerField(default=0, help_text="使用次数")
    last_used_at = models.DateTimeField(auto_now=True, help_text="最后使用时间")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grading_comment_template"
        verbose_name = "评价模板"
        verbose_name_plural = "评价模板"
        ordering = ["-usage_count", "-last_used_at"]
        indexes = [
            models.Index(fields=["teacher", "template_type", "-usage_count"]),
            models.Index(fields=["tenant", "template_type", "-usage_count"]),
        ]

    def __str__(self):
        if self.teacher:
            return f"{self.teacher.username} - {self.comment_text[:50]}"
        return f"系统模板 - {self.comment_text[:50]}"
