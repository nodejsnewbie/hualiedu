"""
模型测试
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from grading.models import (
    Assignment,
    Class,
    CommentTemplate,
    Course,
    CourseSchedule,
    CourseWeekSchedule,
    GlobalConfig,
    GradeTypeConfig,
    Repository,
    Semester,
    Student,
    Submission,
    Tenant,
    TenantConfig,
    UserProfile,
)

from .base import BaseTestCase


class TenantModelTest(BaseTestCase):
    """租户模型测试"""

    def test_create_tenant(self):
        """测试创建租户"""
        tenant = Tenant.objects.create(name="测试租户", description="这是一个测试租户")
        self.assertEqual(tenant.name, "测试租户")
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.created_at)

    def test_tenant_unique_name(self):
        """测试租户名称唯一性"""
        Tenant.objects.create(name="重复名称")
        with self.assertRaises(IntegrityError):
            Tenant.objects.create(name="重复名称")

    def test_tenant_str_representation(self):
        """测试租户字符串表示"""
        tenant = Tenant.objects.create(name="测试租户")
        self.assertEqual(str(tenant), "测试租户")


class UserProfileModelTest(BaseTestCase):
    """用户配置文件模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")

    def test_create_user_profile(self):
        """测试创建用户配置文件"""
        profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/home/test", is_tenant_admin=True
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.tenant, self.tenant)
        self.assertTrue(profile.is_tenant_admin)

    def test_user_profile_str_representation(self):
        """测试用户配置文件字符串表示"""
        profile = UserProfile.objects.create(user=self.user, tenant=self.tenant)
        expected = f"{self.user.username} - {self.tenant.name}"
        self.assertEqual(str(profile), expected)

    def test_get_repo_base_dir(self):
        """测试获取仓库基础目录"""
        profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/custom/path"
        )
        self.assertEqual(profile.get_repo_base_dir(), "/custom/path")


class GlobalConfigModelTest(BaseTestCase):
    """全局配置模型测试"""

    def test_create_global_config(self):
        """测试创建全局配置"""
        config = GlobalConfig.objects.create(
            key="test_key", value="test_value", description="测试配置"
        )
        self.assertEqual(config.key, "test_key")
        self.assertEqual(config.value, "test_value")

    def test_get_value_existing(self):
        """测试获取存在的配置值"""
        GlobalConfig.objects.create(key="existing_key", value="existing_value")
        value = GlobalConfig.get_value("existing_key")
        self.assertEqual(value, "existing_value")

    def test_get_value_nonexistent(self):
        """测试获取不存在的配置值"""
        value = GlobalConfig.get_value("nonexistent_key", "default")
        self.assertEqual(value, "default")

    def test_set_value_new(self):
        """测试设置新配置值"""
        config = GlobalConfig.set_value("new_key", "new_value", "新配置")
        self.assertEqual(config.key, "new_key")
        self.assertEqual(config.value, "new_value")

    def test_set_value_update(self):
        """测试更新现有配置值"""
        GlobalConfig.objects.create(key="update_key", value="old_value")
        config = GlobalConfig.set_value("update_key", "new_value")
        self.assertEqual(config.value, "new_value")


class StudentModelTest(BaseTestCase):
    """学生模型测试"""

    def test_create_student(self):
        """测试创建学生"""
        student = Student.objects.create(student_id="2024001", name="张三", class_name="计算机1班")
        self.assertEqual(student.student_id, "2024001")
        self.assertEqual(student.name, "张三")

    def test_student_unique_id(self):
        """测试学生ID唯一性"""
        Student.objects.create(student_id="2024001", name="张三", class_name="计算机1班")
        with self.assertRaises(IntegrityError):
            Student.objects.create(student_id="2024001", name="李四", class_name="计算机2班")

    def test_student_str_representation(self):
        """测试学生字符串表示"""
        student = Student.objects.create(student_id="2024001", name="张三", class_name="计算机1班")
        self.assertEqual(str(student), "张三 (2024001)")


class AssignmentModelTest(BaseTestCase):
    """作业模型测试"""

    def test_create_assignment(self):
        """测试创建作业"""
        due_date = timezone.now() + timedelta(days=7)
        assignment = Assignment.objects.create(
            name="Python基础作业", description="完成Python基础练习", due_date=due_date
        )
        self.assertEqual(assignment.name, "Python基础作业")
        self.assertEqual(assignment.due_date, due_date)

    def test_assignment_str_representation(self):
        """测试作业字符串表示"""
        assignment = Assignment.objects.create(
            name="测试作业", description="测试描述", due_date=timezone.now()
        )
        self.assertEqual(str(assignment), "测试作业")


class RepositoryModelTest(BaseTestCase):
    """仓库模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")

    def test_create_repository(self):
        """测试创建仓库"""
        repo = Repository.objects.create(
            tenant=self.tenant, name="测试仓库", path="/path/to/repo", description="测试仓库描述"
        )
        self.assertEqual(repo.name, "测试仓库")
        self.assertEqual(repo.tenant, self.tenant)

    def test_repository_unique_per_tenant(self):
        """测试仓库在租户内唯一"""
        Repository.objects.create(tenant=self.tenant, name="重复名称", path="/path1")
        with self.assertRaises(IntegrityError):
            Repository.objects.create(tenant=self.tenant, name="重复名称", path="/path2")

    def test_get_full_path(self):
        """测试获取完整路径"""
        UserProfile.objects.create(user=self.user, tenant=self.tenant, repo_base_dir="/base")
        repo = Repository.objects.create(tenant=self.tenant, name="测试仓库", path="subdir")
        self.assertEqual(repo.get_full_path(), "/base/subdir")


class SubmissionModelTest(BaseTestCase):
    """提交模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.repository = Repository.objects.create(
            tenant=self.tenant, name="测试仓库", path="/path/to/repo"
        )

    def test_create_submission(self):
        """测试创建提交"""
        submission = Submission.objects.create(
            tenant=self.tenant,
            repository=self.repository,
            file_path="/path/to/file.py",
            file_name="file.py",
            file_size=1024,
        )
        self.assertEqual(submission.file_name, "file.py")
        self.assertEqual(submission.file_size, 1024)

    def test_submission_auto_grade_time(self):
        """测试提交自动设置评分时间"""
        submission = Submission.objects.create(
            tenant=self.tenant,
            repository=self.repository,
            file_path="/path/to/file.py",
            file_name="file.py",
        )
        self.assertIsNone(submission.graded_at)

        submission.grade = "A"
        submission.save()
        self.assertIsNotNone(submission.graded_at)


class GradeTypeConfigModelTest(BaseTestCase):
    """评分类型配置模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")

    def test_create_grade_type_config(self):
        """测试创建评分类型配置"""
        config = GradeTypeConfig.objects.create(
            tenant=self.tenant, class_identifier="计算机1班", grade_type="letter"
        )
        self.assertEqual(config.grade_type, "letter")
        self.assertFalse(config.is_locked)

    def test_lock_grade_type(self):
        """测试锁定评分类型"""
        config = GradeTypeConfig.objects.create(
            tenant=self.tenant, class_identifier="计算机1班", grade_type="letter"
        )
        self.assertTrue(config.can_change_grade_type())

        config.lock_grade_type()
        self.assertFalse(config.can_change_grade_type())

    def test_unique_per_tenant_class(self):
        """测试租户和班级的唯一性"""
        GradeTypeConfig.objects.create(
            tenant=self.tenant, class_identifier="计算机1班", grade_type="letter"
        )
        with self.assertRaises(IntegrityError):
            GradeTypeConfig.objects.create(
                tenant=self.tenant, class_identifier="计算机1班", grade_type="text"
            )


class SemesterModelTest(BaseTestCase):
    """学期模型测试"""

    def test_create_semester(self):
        """测试创建学期"""
        start_date = date(2024, 2, 26)
        end_date = date(2024, 6, 30)
        semester = Semester.objects.create(
            name="2024年春季学期", start_date=start_date, end_date=end_date
        )
        self.assertEqual(semester.name, "2024年春季学期")
        self.assertTrue(semester.is_active)

    def test_get_week_count(self):
        """测试获取学期周数"""
        semester = Semester.objects.create(
            name="测试学期",
            start_date=date(2024, 2, 26),  # 周一
            end_date=date(2024, 3, 10),  # 两周后的周日
        )
        # 2月26日到3月10日，应该是3周
        self.assertEqual(semester.get_week_count(), 3)

    def test_get_week_dates(self):
        """测试获取指定周的日期"""
        semester = Semester.objects.create(
            name="测试学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )
        start, end = semester.get_week_dates(1)
        self.assertEqual(start, date(2024, 2, 26))
        self.assertEqual(end, date(2024, 3, 3))


class CourseModelTest(BaseTestCase):
    """课程模型测试"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )

    def test_create_course(self):
        """测试创建课程"""
        course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            location="A101",
            class_name="计算机1班",
        )
        self.assertEqual(course.name, "Python程序设计")
        self.assertEqual(course.teacher, self.teacher_user)

    def test_course_str_representation(self):
        """测试课程字符串表示"""
        course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            location="A101",
            class_name="计算机1班",
        )
        expected = f"{self.semester.name} - Python程序设计 - 计算机1班"
        self.assertEqual(str(course), expected)


class CourseScheduleModelTest(BaseTestCase):
    """课程安排模型测试"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            location="A101",
        )

    def test_create_course_schedule(self):
        """测试创建课程安排"""
        schedule = CourseSchedule.objects.create(
            course=self.course, weekday=1, period=1, start_week=1, end_week=16  # 周一  # 第一大节
        )
        self.assertEqual(schedule.weekday, 1)
        self.assertEqual(schedule.period, 1)

    def test_is_in_week_basic(self):
        """测试基本周次检查"""
        schedule = CourseSchedule.objects.create(
            course=self.course, weekday=1, period=1, start_week=3, end_week=15
        )
        self.assertFalse(schedule.is_in_week(2))  # 开始前
        self.assertTrue(schedule.is_in_week(5))  # 范围内
        self.assertFalse(schedule.is_in_week(16))  # 结束后

    def test_is_in_week_with_specific_schedule(self):
        """测试带具体周次安排的检查"""
        schedule = CourseSchedule.objects.create(
            course=self.course, weekday=1, period=1, start_week=1, end_week=10
        )

        # 添加具体周次安排
        CourseWeekSchedule.objects.create(
            course_schedule=schedule, week_number=5, is_active=False  # 第5周不上课
        )

        self.assertTrue(schedule.is_in_week(3))  # 没有具体安排，默认上课
        self.assertFalse(schedule.is_in_week(5))  # 具体设置为不上课

    def test_unique_course_weekday_period(self):
        """测试课程、星期、节次的唯一性"""
        CourseSchedule.objects.create(
            course=self.course, weekday=1, period=1, start_week=1, end_week=16
        )
        with self.assertRaises(IntegrityError):
            CourseSchedule.objects.create(
                course=self.course, weekday=1, period=1, start_week=1, end_week=16
            )


class CourseWeekScheduleModelTest(BaseTestCase):
    """课程周次安排模型测试"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            location="A101",
        )
        self.schedule = CourseSchedule.objects.create(
            course=self.course, weekday=1, period=1, start_week=1, end_week=16
        )

    def test_create_week_schedule(self):
        """测试创建周次安排"""
        week_schedule = CourseWeekSchedule.objects.create(
            course_schedule=self.schedule, week_number=5, is_active=False
        )
        self.assertEqual(week_schedule.week_number, 5)
        self.assertFalse(week_schedule.is_active)

    def test_week_schedule_str_representation(self):
        """测试周次安排字符串表示"""
        week_schedule = CourseWeekSchedule.objects.create(
            course_schedule=self.schedule, week_number=5, is_active=False
        )
        self.assertIn("第5周(不上课)", str(week_schedule))

    def test_unique_schedule_week(self):
        """测试课程安排和周次的唯一性"""
        CourseWeekSchedule.objects.create(
            course_schedule=self.schedule, week_number=5, is_active=True
        )
        with self.assertRaises(IntegrityError):
            CourseWeekSchedule.objects.create(
                course_schedule=self.schedule, week_number=5, is_active=False
            )


class CourseModelPropertyTest(BaseTestCase):
    """课程模型属性测试 - Property 1: 课程创建完整性"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )

    def test_course_creation_integrity_all_fields(self):
        """Property 1: 测试课程创建包含所有指定字段
        For any valid course data (name, type, description),
        creating a course should result in a database record
        containing all specified fields with correct values.
        Validates: Requirements 1.1
        """
        # 测试数据
        course_data = {
            "semester": self.semester,
            "teacher": self.teacher_user,
            "name": "数据结构与算法",
            "course_type": "theory",
            "description": "这是一门关于数据结构的课程",
        }

        # 创建课程
        course = Course.objects.create(**course_data)

        # 验证所有字段都正确保存
        self.assertEqual(course.name, course_data["name"])
        self.assertEqual(course.course_type, course_data["course_type"])
        self.assertEqual(course.description, course_data["description"])
        self.assertEqual(course.semester, course_data["semester"])
        self.assertEqual(course.teacher, course_data["teacher"])

        # 验证从数据库重新查询也能获取正确的值
        retrieved_course = Course.objects.get(pk=course.pk)
        self.assertEqual(retrieved_course.name, course_data["name"])
        self.assertEqual(retrieved_course.course_type, course_data["course_type"])
        self.assertEqual(retrieved_course.description, course_data["description"])

    def test_course_creation_integrity_all_types(self):
        """Property 1: 测试所有课程类型的创建完整性"""
        course_types = ["theory", "lab", "practice", "mixed"]

        for course_type in course_types:
            with self.subTest(course_type=course_type):
                course = Course.objects.create(
                    semester=self.semester,
                    teacher=self.teacher_user,
                    name=f"测试课程-{course_type}",
                    course_type=course_type,
                    description=f"测试{course_type}类型课程",
                )

                # 验证课程类型正确保存
                self.assertEqual(course.course_type, course_type)

                # 从数据库重新查询验证
                retrieved = Course.objects.get(pk=course.pk)
                self.assertEqual(retrieved.course_type, course_type)


class ClassModelTest(BaseTestCase):
    """班级模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            course_type="theory",
        )

    def test_create_class(self):
        """测试创建班级"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        self.assertEqual(class_obj.name, "计算机1班")
        self.assertEqual(class_obj.student_count, 30)
        self.assertEqual(class_obj.course, self.course)
        self.assertEqual(class_obj.tenant, self.tenant)

    def test_class_course_association(self):
        """测试班级与课程的关联"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        # 验证班级关联到正确的课程
        self.assertEqual(class_obj.course, self.course)

        # 验证可以通过课程反向查询班级
        classes = self.course.classes.all()
        self.assertIn(class_obj, classes)

    def test_class_str_representation(self):
        """测试班级字符串表示"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        expected = f"{self.course.name} - 计算机1班"
        self.assertEqual(str(class_obj), expected)

    def test_multiple_classes_per_course(self):
        """测试一个课程可以有多个班级"""
        from grading.models import Class

        class1 = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )
        class2 = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机2班", student_count=28
        )

        classes = self.course.classes.all()
        self.assertEqual(classes.count(), 2)
        self.assertIn(class1, classes)
        self.assertIn(class2, classes)


class RepositoryModelExtendedTest(BaseTestCase):
    """仓库模型扩展测试 - 测试两种配置方式"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date=date(2024, 2, 26), end_date=date(2024, 6, 30)
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            course_type="theory",
        )

    def test_create_git_repository(self):
        """测试创建Git仓库配置"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        repo = Repository.objects.create(
            owner=self.teacher_user,
            tenant=self.tenant,
            class_obj=class_obj,
            name="Git仓库",
            repo_type="git",
            git_url="https://github.com/test/repo.git",
            git_branch="main",
            git_username="testuser",
            git_password="testpass",
            description="Git仓库测试",
        )

        self.assertEqual(repo.repo_type, "git")
        self.assertEqual(repo.git_url, "https://github.com/test/repo.git")
        self.assertEqual(repo.git_branch, "main")
        self.assertEqual(repo.git_username, "testuser")
        self.assertEqual(repo.class_obj, class_obj)

    def test_create_filesystem_repository(self):
        """测试创建文件系统仓库配置"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        repo = Repository.objects.create(
            owner=self.teacher_user,
            tenant=self.tenant,
            class_obj=class_obj,
            name="文件系统仓库",
            repo_type="filesystem",
            filesystem_path="/home/teacher/repos/class1",
            allocated_space_mb=2048,
            description="文件系统仓库测试",
        )

        self.assertEqual(repo.repo_type, "filesystem")
        self.assertEqual(repo.filesystem_path, "/home/teacher/repos/class1")
        self.assertEqual(repo.allocated_space_mb, 2048)
        self.assertEqual(repo.class_obj, class_obj)

    def test_repository_type_switching(self):
        """测试仓库类型配置"""
        from grading.models import Class

        class_obj = Class.objects.create(
            tenant=self.tenant, course=self.course, name="计算机1班", student_count=30
        )

        # 创建Git仓库
        repo = Repository.objects.create(
            owner=self.teacher_user,
            tenant=self.tenant,
            class_obj=class_obj,
            name="混合仓库",
            repo_type="git",
            git_url="https://github.com/test/repo.git",
        )

        self.assertEqual(repo.repo_type, "git")

        # 切换到文件系统方式
        repo.repo_type = "filesystem"
        repo.filesystem_path = "/home/teacher/repos/mixed"
        repo.save()

        retrieved = Repository.objects.get(pk=repo.pk)
        self.assertEqual(retrieved.repo_type, "filesystem")
        self.assertEqual(retrieved.filesystem_path, "/home/teacher/repos/mixed")

    def test_repository_is_git_repository(self):
        """测试判断是否为Git仓库"""
        git_repo = Repository.objects.create(
            owner=self.teacher_user,
            tenant=self.tenant,
            name="Git仓库",
            repo_type="git",
            url="https://github.com/test/repo.git",
        )

        fs_repo = Repository.objects.create(
            owner=self.teacher_user,
            tenant=self.tenant,
            name="文件系统仓库",
            repo_type="filesystem",
        )

        self.assertTrue(git_repo.is_git_repository())
        self.assertFalse(fs_repo.is_git_repository())


class CommentTemplateModelTest(BaseTestCase):
    """评价模板模型测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")

    def test_create_personal_template(self):
        """测试创建个人评价模板"""
        from grading.models import CommentTemplate

        template = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="作业完成得很好，继续保持！",
            usage_count=5,
        )

        self.assertEqual(template.template_type, "personal")
        self.assertEqual(template.teacher, self.teacher_user)
        self.assertEqual(template.usage_count, 5)

    def test_create_system_template(self):
        """测试创建系统评价模板"""
        from grading.models import CommentTemplate

        template = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=None,
            template_type="system",
            comment_text="作业格式规范，内容完整。",
            usage_count=10,
        )

        self.assertEqual(template.template_type, "system")
        self.assertIsNone(template.teacher)
        self.assertEqual(template.usage_count, 10)

    def test_template_usage_count_increment(self):
        """测试评价模板使用次数统计"""
        from grading.models import CommentTemplate

        template = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="需要改进代码结构",
            usage_count=0,
        )

        # 模拟使用评价模板
        template.usage_count += 1
        template.save()

        retrieved = CommentTemplate.objects.get(pk=template.pk)
        self.assertEqual(retrieved.usage_count, 1)

        # 再次使用
        template.usage_count += 1
        template.save()

        retrieved = CommentTemplate.objects.get(pk=template.pk)
        self.assertEqual(retrieved.usage_count, 2)

    def test_template_sorting_by_usage_count(self):
        """测试评价模板按使用次数排序"""
        from grading.models import CommentTemplate

        template1 = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="评价1",
            usage_count=3,
        )

        template2 = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="评价2",
            usage_count=10,
        )

        template3 = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="评价3",
            usage_count=5,
        )

        # 查询并验证排序
        templates = CommentTemplate.objects.filter(
            tenant=self.tenant, teacher=self.teacher_user, template_type="personal"
        ).order_by("-usage_count")

        templates_list = list(templates)
        self.assertEqual(templates_list[0], template2)  # usage_count=10
        self.assertEqual(templates_list[1], template3)  # usage_count=5
        self.assertEqual(templates_list[2], template1)  # usage_count=3

    def test_template_limit_top_5(self):
        """测试评价模板限制为前5个"""
        from grading.models import CommentTemplate

        # 创建7个模板
        for i in range(7):
            CommentTemplate.objects.create(
                tenant=self.tenant,
                teacher=self.teacher_user,
                template_type="personal",
                comment_text=f"评价{i}",
                usage_count=i,
            )

        # 查询前5个
        top_5 = CommentTemplate.objects.filter(
            tenant=self.tenant, teacher=self.teacher_user, template_type="personal"
        ).order_by("-usage_count")[:5]

        self.assertEqual(len(list(top_5)), 5)

        # 验证是使用次数最多的5个
        usage_counts = [t.usage_count for t in top_5]
        self.assertEqual(usage_counts, [6, 5, 4, 3, 2])

    def test_template_str_representation(self):
        """测试评价模板字符串表示"""
        from grading.models import CommentTemplate

        template = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher_user,
            template_type="personal",
            comment_text="这是一个很长的评价内容，用于测试字符串表示是否正确截断显示前50个字符",
            usage_count=1,
        )

        str_repr = str(template)
        self.assertIn(self.teacher_user.username, str_repr)
        self.assertTrue(len(str_repr) < 100)  # 应该被截断
