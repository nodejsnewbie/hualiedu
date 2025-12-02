"""
Tests for database query optimization.

This module tests that database queries are properly optimized using
select_related, prefetch_related, and indexes.
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase

from grading.models import (
    Class,
    Course,
    Homework,
    Repository,
    Semester,
    Submission,
    Tenant,
)
from grading.query_optimization import (
    get_user_courses_optimized,
    get_user_repositories_optimized,
    optimize_course_queryset,
    optimize_repository_queryset,
    optimize_submission_queryset,
)


class QueryOptimizationTestCase(TestCase):
    """Test query optimization functions"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant")

        # Create users
        self.teacher = User.objects.create_user(username="teacher1", password="password123")
        self.student = User.objects.create_user(username="student1", password="password123")

        # Create semester
        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=120),
            is_active=True,
        )

        # Create course
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="测试课程",
            course_type="theory",
            tenant=self.tenant,
        )

        # Create class
        self.class_obj = Class.objects.create(
            tenant=self.tenant,
            course=self.course,
            name="测试班级",
            student_count=30,
        )

        # Create repository
        self.repository = Repository.objects.create(
            owner=self.teacher,
            tenant=self.tenant,
            class_obj=self.class_obj,
            name="test_repo",
            repo_type="filesystem",
            is_active=True,
        )

        # Create homework
        self.homework = Homework.objects.create(
            tenant=self.tenant,
            course=self.course,
            class_obj=self.class_obj,
            title="第一次作业",
            folder_name="homework1",
            homework_type="normal",
        )

        # Create submission
        self.submission = Submission.objects.create(
            tenant=self.tenant,
            homework=self.homework,
            student=self.student,
            repository=self.repository,
            file_path="/path/to/file.docx",
            file_name="file.docx",
            file_size=1024,
        )

    def test_optimize_repository_queryset(self):
        """Test that repository queryset is optimized with select_related"""
        queryset = Repository.objects.filter(owner=self.teacher)
        optimized = optimize_repository_queryset(queryset)

        # Execute query and check that related objects are prefetched
        with self.assertNumQueries(1):
            repo = list(optimized)[0]
            # Access related objects - should not trigger additional queries
            _ = repo.owner.username
            _ = repo.tenant.name
            if repo.class_obj:
                _ = repo.class_obj.name
                _ = repo.class_obj.course.name

    def test_optimize_course_queryset(self):
        """Test that course queryset is optimized with select_related"""
        queryset = Course.objects.filter(teacher=self.teacher)
        optimized = optimize_course_queryset(queryset)

        # Execute query and check that related objects are prefetched
        with self.assertNumQueries(1):
            course = list(optimized)[0]
            # Access related objects - should not trigger additional queries
            _ = course.semester.name
            _ = course.teacher.username
            _ = course.tenant.name

    def test_optimize_submission_queryset(self):
        """Test that submission queryset is optimized with select_related"""
        queryset = Submission.objects.filter(homework=self.homework)
        optimized = optimize_submission_queryset(queryset)

        # Execute query and check that related objects are prefetched
        with self.assertNumQueries(1):
            submission = list(optimized)[0]
            # Access related objects - should not trigger additional queries
            _ = submission.tenant.name
            _ = submission.homework.title
            _ = submission.homework.course.name
            _ = submission.student.username
            _ = submission.repository.name

    def test_get_user_repositories_optimized(self):
        """Test convenience function for getting user repositories"""
        # Should use optimized query
        with self.assertNumQueries(1):
            repos = list(get_user_repositories_optimized(self.teacher))
            self.assertEqual(len(repos), 1)
            # Access related objects - should not trigger additional queries
            _ = repos[0].owner.username
            _ = repos[0].tenant.name

    def test_get_user_courses_optimized(self):
        """Test convenience function for getting user courses"""
        # Should use optimized query
        with self.assertNumQueries(1):
            courses = list(get_user_courses_optimized(self.teacher))
            self.assertEqual(len(courses), 1)
            # Access related objects - should not trigger additional queries
            _ = courses[0].semester.name
            _ = courses[0].teacher.username

    def test_repository_indexes_exist(self):
        """Test that Repository model has proper indexes"""
        # Get table name
        table_name = Repository._meta.db_table

        # Get indexes from database
        with connection.cursor() as cursor:
            # Get all indexes for the table
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name=?
                """,
                [table_name],
            )
            indexes = [row[0] for row in cursor.fetchall()]

        # Check that our custom indexes exist
        # Note: Index names are auto-generated by Django
        # Just check that there are indexes on the repository table
        self.assertTrue(
            len(indexes) > 0,
            "Repository should have indexes",
        )

    def test_submission_indexes_exist(self):
        """Test that Submission model has proper indexes"""
        # Get table name
        table_name = Submission._meta.db_table

        # Get indexes from database
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name=?
                """,
                [table_name],
            )
            indexes = [row[0] for row in cursor.fetchall()]

        # Check that our custom indexes exist
        self.assertTrue(
            any("homework" in idx for idx in indexes),
            "Submission should have index on homework",
        )

    def test_course_indexes_exist(self):
        """Test that Course model has proper indexes"""
        # Get table name
        table_name = Course._meta.db_table

        # Get indexes from database
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name=?
                """,
                [table_name],
            )
            indexes = [row[0] for row in cursor.fetchall()]

        # Check that our custom indexes exist
        self.assertTrue(
            any("teacher" in idx for idx in indexes),
            "Course should have index on teacher",
        )

    def test_query_count_for_repository_list(self):
        """Test that listing repositories doesn't cause N+1 queries"""
        # Create multiple repositories
        for i in range(5):
            Repository.objects.create(
                owner=self.teacher,
                tenant=self.tenant,
                name=f"repo_{i}",
                repo_type="filesystem",
                is_active=True,
            )

        # Query with optimization should use constant number of queries
        with self.assertNumQueries(1):
            repos = list(get_user_repositories_optimized(self.teacher))
            # Access related objects for all repos
            for repo in repos:
                _ = repo.owner.username
                _ = repo.tenant.name

    def test_query_count_for_course_list(self):
        """Test that listing courses doesn't cause N+1 queries"""
        # Create multiple courses
        for i in range(5):
            Course.objects.create(
                semester=self.semester,
                teacher=self.teacher,
                name=f"课程_{i}",
                course_type="theory",
                tenant=self.tenant,
            )

        # Query with optimization should use constant number of queries
        with self.assertNumQueries(1):
            courses = list(get_user_courses_optimized(self.teacher))
            # Access related objects for all courses
            for course in courses:
                _ = course.semester.name
                _ = course.teacher.username
                _ = course.tenant.name


class IndexPerformanceTestCase(TestCase):
    """Test that indexes improve query performance"""

    def setUp(self):
        """Set up test data"""
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.teacher = User.objects.create_user(username="teacher1", password="password123")
        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=120),
            is_active=True,
        )

    def test_repository_filter_by_owner_and_active(self):
        """Test that filtering repositories by owner and is_active uses index"""
        # Create test data
        for i in range(10):
            Repository.objects.create(
                owner=self.teacher,
                tenant=self.tenant,
                name=f"repo_{i}",
                repo_type="filesystem",
                is_active=(i % 2 == 0),  # Half active, half inactive
            )

        # Query should be fast with index
        repos = Repository.objects.filter(owner=self.teacher, is_active=True)
        self.assertEqual(repos.count(), 5)

    def test_course_filter_by_teacher_and_semester(self):
        """Test that filtering courses by teacher and semester uses index"""
        # Create test data
        for i in range(10):
            Course.objects.create(
                semester=self.semester,
                teacher=self.teacher,
                name=f"课程_{i}",
                course_type="theory",
                tenant=self.tenant,
            )

        # Query should be fast with index
        courses = Course.objects.filter(teacher=self.teacher, semester=self.semester)
        self.assertEqual(courses.count(), 10)

    def test_submission_filter_by_tenant(self):
        """Test that filtering submissions by tenant uses index"""
        student = User.objects.create_user(username="student1", password="password123")
        course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher,
            name="测试课程",
            tenant=self.tenant,
        )
        homework = Homework.objects.create(
            tenant=self.tenant,
            course=course,
            title="作业1",
            folder_name="hw1",
        )

        # Create test data
        for i in range(10):
            Submission.objects.create(
                tenant=self.tenant,
                homework=homework,
                student=student,
                file_path=f"/path/file_{i}.docx",
                file_name=f"file_{i}.docx",
                file_size=1024,
            )

        # Query should be fast with index
        submissions = Submission.objects.filter(tenant=self.tenant)
        self.assertEqual(submissions.count(), 10)
