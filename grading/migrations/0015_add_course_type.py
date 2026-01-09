# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0014_merge_20251108_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='course_type',
            field=models.CharField(
                choices=[
                    ('theory', '理论课'),
                    ('lab', '实验课'),
                    ('practice', '实践课'),
                    ('mixed', '理论+实验')
                ],
                default='theory',
                help_text='课程类型',
                max_length=20
            ),
        ),
    ]
