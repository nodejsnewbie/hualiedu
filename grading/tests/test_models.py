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
