"""
测试数据固件
提供测试用的示例数据
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from grading.models import (
    Assignment,
    Course,
    CourseSchedule,
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


class TestDataFixtures:
    """测试数据固件类"""

    @staticmethod
    def create_test_users():
        """创建测试用户"""
        users = {}

        # 普通用户
        users["student"] = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            first_name="测试",
            last_name="学生",
        )

        # 教师用户
        users["teacher"] = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="testpass123",
            first_name="测试",
            last_name="教师",
        )

        # 管理员用户
        users["admin"] = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            first_name="系统",
            last_name="管理员",
        )

        return users

    @staticmethod
    def create_test_tenants():
        """创建测试租户"""
        tenants = {}

        tenants["school1"] = Tenant.objects.create(
            name="华立学院", description="华立学院租户", is_active=True
        )

        tenants["school2"] = Tenant.objects.create(
            name="测试学校", description="测试用学校租户", is_active=True
        )

        return tenants

    @staticmethod
    def create_test_user_profiles(users, tenants):
        """创建测试用户配置文件"""
        profiles = {}

        profiles["student"] = UserProfile.objects.create(
            user=users["student"],
            tenant=tenants["school1"],
            repo_base_dir="/home/student/repos",
            is_tenant_admin=False,
        )

        profiles["teacher"] = UserProfile.objects.create(
            user=users["teacher"],
            tenant=tenants["school1"],
            repo_base_dir="/home/teacher/repos",
            is_tenant_admin=True,
        )

        profiles["admin"] = UserProfile.objects.create(
            user=users["admin"],
            tenant=tenants["school1"],
            repo_base_dir="/home/admin/repos",
            is_tenant_admin=True,
        )

        return profiles

    @staticmethod
    def create_test_students():
        """创建测试学生"""
        students = []

        for i in range(1, 6):
            student = Student.objects.create(
                student_id=f"2024{i:03d}", name=f"学生{i}", class_name="计算机科学1班"
            )
            students.append(student)

        return students

    @staticmethod
    def create_test_assignments():
        """创建测试作业"""
        assignments = []

        # 当前作业
        assignment1 = Assignment.objects.create(
            name="Python基础练习",
            description="完成Python基础语法练习",
            due_date=timezone.now() + timedelta(days=7),
        )
        assignments.append(assignment1)

        # 过期作业
        assignment2 = Assignment.objects.create(
            name="数据结构作业",
            description="实现链表和栈",
            due_date=timezone.now() - timedelta(days=3),
        )
        assignments.append(assignment2)

        return assignments

    @staticmethod
    def create_test_repositories(tenants):
        """创建测试仓库"""
        repositories = []

        repo1 = Repository.objects.create(
            tenant=tenants["school1"],
            name="python-exercises",
            path="exercises/python",
            description="Python练习仓库",
            is_active=True,
        )
        repositories.append(repo1)

        repo2 = Repository.objects.create(
            tenant=tenants["school1"],
            name="data-structures",
            path="courses/data-structures",
            description="数据结构课程仓库",
            is_active=True,
        )
        repositories.append(repo2)

        return repositories

    @staticmethod
    def create_test_submissions(tenants, repositories):
        """创建测试提交"""
        submissions = []

        submission1 = Submission.objects.create(
            tenant=tenants["school1"],
            repository=repositories[0],
            file_path="student1/homework1.py",
            file_name="homework1.py",
            file_size=1024,
            grade="A",
            comment="优秀的作业",
        )
        submissions.append(submission1)

        submission2 = Submission.objects.create(
            tenant=tenants["school1"],
            repository=repositories[0],
            file_path="student2/homework1.py",
            file_name="homework1.py",
            file_size=2048,
            # 未评分
        )
        submissions.append(submission2)

        return submissions

    @staticmethod
    def create_test_semesters():
        """创建测试学期"""
        semesters = []

        # 当前学期
        current_semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date(2024, 2, 26),
            end_date=date(2024, 6, 30),
            is_active=True,
        )
        semesters.append(current_semester)

        # 下学期
        next_semester = Semester.objects.create(
            name="2024年秋季学期",
            start_date=date(2024, 9, 2),
            end_date=date(2025, 1, 15),
            is_active=False,
        )
        semesters.append(next_semester)

        return semesters

    @staticmethod
    def create_test_courses(semesters, users):
        """创建测试课程"""
        courses = []

        course1 = Course.objects.create(
            semester=semesters[0],
            teacher=users["teacher"],
            name="Python程序设计",
            description="Python编程基础课程",
            location="A101",
            class_name="计算机科学1班",
        )
        courses.append(course1)

        course2 = Course.objects.create(
            semester=semesters[0],
            teacher=users["teacher"],
            name="数据结构与算法",
            description="数据结构和算法设计",
            location="B202",
            class_name="计算机科学1班",
        )
        courses.append(course2)

        return courses

    @staticmethod
    def create_test_course_schedules(courses):
        """创建测试课程安排"""
        schedules = []

        # Python课程：周一第一大节，第1-16周
        schedule1 = CourseSchedule.objects.create(
            course=courses[0], weekday=1, period=1, start_week=1, end_week=16  # 周一  # 第一大节
        )
        schedules.append(schedule1)

        # 数据结构课程：周三第二大节，第1-16周
        schedule2 = CourseSchedule.objects.create(
            course=courses[1], weekday=3, period=2, start_week=1, end_week=16  # 周三  # 第二大节
        )
        schedules.append(schedule2)

        return schedules

    @staticmethod
    def create_test_grade_type_configs(tenants):
        """创建测试评分类型配置"""
        configs = []

        config1 = GradeTypeConfig.objects.create(
            tenant=tenants["school1"],
            class_identifier="计算机科学1班",
            grade_type="letter",
            is_locked=False,
        )
        configs.append(config1)

        config2 = GradeTypeConfig.objects.create(
            tenant=tenants["school1"],
            class_identifier="计算机科学2班",
            grade_type="text",
            is_locked=True,
        )
        configs.append(config2)

        return configs

    @staticmethod
    def create_test_global_configs():
        """创建测试全局配置"""
        configs = []

        config1 = GlobalConfig.objects.create(
            key="default_repo_base_dir", value="~/jobs", description="默认仓库基础目录"
        )
        configs.append(config1)

        config2 = GlobalConfig.objects.create(
            key="max_file_size", value="10485760", description="最大文件大小（字节）"
        )
        configs.append(config2)

        return configs

    @classmethod
    def create_full_test_data(cls):
        """创建完整的测试数据集"""
        data = {}

        # 创建用户
        data["users"] = cls.create_test_users()

        # 创建租户
        data["tenants"] = cls.create_test_tenants()

        # 创建用户配置文件
        data["profiles"] = cls.create_test_user_profiles(data["users"], data["tenants"])

        # 创建学生
        data["students"] = cls.create_test_students()

        # 创建作业
        data["assignments"] = cls.create_test_assignments()

        # 创建仓库
        data["repositories"] = cls.create_test_repositories(data["tenants"])

        # 创建提交
        data["submissions"] = cls.create_test_submissions(data["tenants"], data["repositories"])

        # 创建学期
        data["semesters"] = cls.create_test_semesters()

        # 创建课程
        data["courses"] = cls.create_test_courses(data["semesters"], data["users"])

        # 创建课程安排
        data["schedules"] = cls.create_test_course_schedules(data["courses"])

        # 创建评分类型配置
        data["grade_configs"] = cls.create_test_grade_type_configs(data["tenants"])

        # 创建全局配置
        data["global_configs"] = cls.create_test_global_configs()

        return data
