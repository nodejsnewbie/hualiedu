from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("grading", "0031_filegradestatus_last_graded_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assignment",
            name="course",
            field=models.ForeignKey(
                blank=True,
                help_text="关联课程（可选）",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="grading.course",
            ),
        ),
        migrations.AlterField(
            model_name="assignment",
            name="class_obj",
            field=models.ForeignKey(
                blank=True,
                help_text="关联班级（可选）",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="grading.class",
            ),
        ),
    ]
