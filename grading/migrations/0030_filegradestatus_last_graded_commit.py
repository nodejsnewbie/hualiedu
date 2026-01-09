from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0029_filegradestatus"),
    ]

    operations = [
        migrations.AddField(
            model_name="filegradestatus",
            name="last_graded_commit",
            field=models.CharField(
                blank=True,
                help_text="上次评分时的仓库提交",
                max_length=64,
                null=True,
            ),
        ),
    ]
