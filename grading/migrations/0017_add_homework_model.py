# Generated manually - Add Homework model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0016_update_existing_course_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='Homework',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='作业标题', max_length=200)),
                ('homework_type', models.CharField(
                    choices=[('normal', '普通作业'), ('lab_report', '实验报告')],
                    default='normal',
                    help_text='作业类型',
                    max_length=20
                )),
                ('description', models.TextField(blank=True, help_text='作业描述')),
                ('due_date', models.DateTimeField(blank=True, help_text='截止日期', null=True)),
                ('folder_name', models.CharField(help_text='作业文件夹名称（用于匹配文件系统中的目录）', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(
                    help_text='所属课程',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='homeworks',
                    to='grading.course'
                )),
            ],
            options={
                'verbose_name': '作业',
                'verbose_name_plural': '作业',
                'db_table': 'grading_homework',
                'ordering': ['course', '-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='homework',
            unique_together={('course', 'folder_name')},
        ),
    ]
