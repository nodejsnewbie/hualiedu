# Generated migration for Assignment model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("grading", "0025_class_grading_cla_course__e2468b_idx_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS grading_assignment;",
            reverse_sql="",
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(help_text="作业名称", max_length=255)),
                ("description", models.TextField(blank=True, help_text="作业描述")),
                (
                    "storage_type",
                    models.CharField(
                        choices=[("git", "Git仓库"), ("filesystem", "文件上传")],
                        default="filesystem",
                        help_text="存储类型",
                        max_length=20,
                    ),
                ),
                ("git_url", models.URLField(blank=True, help_text="Git仓库URL", null=True)),
                (
                    "git_branch",
                    models.CharField(
                        blank=True, default="main", help_text="Git分支", max_length=100
                    ),
                ),
                (
                    "git_username",
                    models.CharField(blank=True, help_text="Git用户名", max_length=100),
                ),
                (
                    "git_password_encrypted",
                    models.CharField(blank=True, help_text="加密的Git密码", max_length=500),
                ),
                (
                    "base_path",
                    models.CharField(blank=True, help_text="文件系统基础路径", max_length=500),
                ),
                ("is_active", models.BooleanField(default=True, help_text="是否激活")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "class_obj",
                    models.ForeignKey(
                        help_text="关联班级",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="grading.class",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        help_text="关联课程",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="grading.course",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="作业创建者（教师）",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        help_text="所属租户",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="grading.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "作业配置",
                "verbose_name_plural": "作业配置",
                "db_table": "grading_assignment",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["owner", "is_active"], name="grading_ass_owner_i_714e27_idx"
                    ),
                    models.Index(
                        fields=["tenant", "is_active"], name="grading_ass_tenant__77c43b_idx"
                    ),
                    models.Index(
                        fields=["course", "class_obj"], name="grading_ass_course__1ebcbe_idx"
                    ),
                    models.Index(
                        fields=["storage_type", "is_active"], name="grading_ass_storage_490789_idx"
                    ),
                ],
                "unique_together": {("owner", "course", "class_obj", "name")},
            },
        ),
    ]
