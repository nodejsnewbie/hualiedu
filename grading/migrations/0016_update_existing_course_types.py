# Generated manually - Update existing course types based on course names

from django.db import migrations


def update_course_types(apps, schema_editor):
    """根据课程名称自动更新课程类型"""
    Course = apps.get_model('grading', 'Course')
    
    # 定义关键词映射
    lab_keywords = ['实验', 'lab', 'experiment', '实训', 'practice']
    
    updated_count = 0
    for course in Course.objects.all():
        course_name_lower = course.name.lower()
        
        # 检查是否包含实验相关关键词
        is_lab = any(keyword in course_name_lower for keyword in lab_keywords)
        
        if is_lab and course.course_type == 'theory':
            course.course_type = 'lab'
            course.save()
            updated_count += 1
            print(f"更新课程: {course.name} -> lab")
    
    print(f"共更新了 {updated_count} 个课程的类型")


def reverse_update(apps, schema_editor):
    """回滚操作：将所有课程类型改回theory"""
    Course = apps.get_model('grading', 'Course')
    Course.objects.all().update(course_type='theory')


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0015_add_course_type'),
    ]

    operations = [
        migrations.RunPython(update_course_types, reverse_update),
    ]
