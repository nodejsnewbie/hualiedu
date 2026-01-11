from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0028_alter_assignment_git_url_to_charfield"),
    ]

    operations = [
        migrations.CreateModel(
            name="FileGradeStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("file_path", models.CharField(help_text="文件相对路径", max_length=500)),
                (
                    "last_graded_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, help_text="上次评分时间"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, help_text="记录更新时间"),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        help_text="所属仓库",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="file_grade_statuses",
                        to="grading.repository",
                    ),
                ),
            ],
            options={
                "verbose_name": "文件评分状态",
                "verbose_name_plural": "文件评分状态",
                "db_table": "grading_file_grade_status",
                "unique_together": {("repository", "file_path")},
                "indexes": [
                    models.Index(fields=["repository", "file_path"], name="grading_fil_repository_4aa07b_idx"),
                    models.Index(fields=["repository", "last_graded_at"], name="grading_fil_repository_8a7923_idx"),
                ],
            },
        ),
    ]
