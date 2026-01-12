from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("grading", "0032_alter_assignment_course_class_nullable"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignmentSetting",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, help_text="作业设置名称")),
                ("repo_type", models.CharField(choices=[("git", "Git仓库"), ("filesystem", "文件上传")], default="filesystem", max_length=20, help_text="存储类型")),
                ("git_url", models.CharField(blank=True, null=True, max_length=500, help_text="Git仓库URL（支持 http://, https://, git://, ssh://, git@ 格式）")),
                ("git_branch", models.CharField(blank=True, default="main", max_length=100, help_text="Git分支")),
                ("git_username", models.CharField(blank=True, max_length=100, help_text="Git用户名")),
                ("git_password_encrypted", models.CharField(blank=True, max_length=500, help_text="加密的Git密码")),
                ("filesystem_path", models.CharField(blank=True, max_length=500, help_text="作业提交根目录")),
                ("description", models.TextField(blank=True, help_text="作业设置描述")),
                ("is_active", models.BooleanField(default=True, help_text="是否激活")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_settings", to=settings.AUTH_USER_MODEL, help_text="作业设置创建者（教师）")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_settings", to="grading.tenant", help_text="所属租户")),
            ],
            options={
                "verbose_name": "作业设置",
                "verbose_name_plural": "作业设置",
                "ordering": ["-created_at"],
                "db_table": "grading_assignment_setting",
                "unique_together": {("owner", "name")},
            },
        ),
        migrations.AddIndex(
            model_name="assignmentsetting",
            index=models.Index(fields=["owner", "is_active"], name="grading_ass_owner_i_eaf7b8_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentsetting",
            index=models.Index(fields=["tenant", "is_active"], name="grading_ass_tenant__d48c7f_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentsetting",
            index=models.Index(fields=["repo_type", "is_active"], name="grading_ass_repo_ty_8c0c10_idx"),
        ),
    ]
