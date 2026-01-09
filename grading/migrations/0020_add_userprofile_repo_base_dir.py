# Generated manually to add back repo_base_dir field to UserProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0019_alter_repository_owner_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="repo_base_dir",
            field=models.CharField(
                max_length=500,
                blank=True,
                help_text="用户基础仓库目录",
                default=""
            ),
        ),
    ]
