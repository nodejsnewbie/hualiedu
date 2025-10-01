# Generated manually to add owner field to repository

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("grading", "0010_merge_20250927_1449"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="repository",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="repository",
            name="branch",
            field=models.CharField(default="main", help_text="默认分支", max_length=100),
        ),
        migrations.AddField(
            model_name="repository",
            name="last_sync",
            field=models.DateTimeField(blank=True, help_text="最后同步时间", null=True),
        ),
        migrations.AddField(
            model_name="repository",
            name="owner",
            field=models.ForeignKey(
                help_text="仓库所有者",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="repositories",
                to=settings.AUTH_USER_MODEL,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="repository",
            name="repo_type",
            field=models.CharField(
                choices=[("local", "本地目录"), ("git", "Git仓库")],
                default="local",
                help_text="仓库类型",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="repository",
            name="url",
            field=models.URLField(blank=True, help_text="仓库URL（Git仓库）"),
        ),
        migrations.AlterUniqueTogether(
            name="repository",
            unique_together={("owner", "name")},
        ),
    ]
