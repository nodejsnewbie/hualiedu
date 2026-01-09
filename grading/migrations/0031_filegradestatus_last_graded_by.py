from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0030_filegradestatus_last_graded_commit"),
    ]

    operations = [
        migrations.AddField(
            model_name="filegradestatus",
            name="last_graded_by",
            field=models.CharField(
                blank=True,
                help_text="上次评分教师",
                max_length=200,
                null=True,
            ),
        ),
    ]
