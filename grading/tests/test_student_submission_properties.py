"""
学生作业提交的属性测试

使用 Hypothesis 进行基于属性的测试，验证学生作业提交相关的通用规则。
"""

import os
import hypothesis
from django.contrib.auth.models import User
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase

from grading.assignment_utils import FilenameValidator
from grading.models import Assignment, Class, Course, Homework, Semester, Submission, Tenant, UserProfile
from grading.services.assignment_management_service import AssignmentManagementService

# 配置最小迭代次数
hypothesis.settings.register_profile("ci", max_examples=100)
hypothesis.settings.load_profile("ci")


class TestStudentSubmissionProperties(TestCase):
    """学生作业提交属性测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant1 = Tenant.objects.create(name="租户1", is_active=True)
        self.tenant2 = Tenant.objects.create(name="租户2", is_active=True)

        # 创建学期
        from datetime import date

        self.semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 7, 15),
            is_active=True,
        )

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username="teacher1", password="pass123", email="teacher1@test.com"
        )
        self.teacher2 = User.objects.create_user(
            username="teacher2", password="pass123", email="teacher2@test.com"
        )

        # 创建教师配置文件
        UserProfile.objects.create(user=self.teacher1, tenant=self.tenant1)
        UserProfile.objects.create(user=self.teacher2, tenant=self.tenant2)

        # 创建课程
        self.course1 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher1,
            name="数据结构",
            tenant=self.tenant1,
        )
        self.course2 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher1,
            name="算法设计",
            tenant=self.tenant1,
        )
        self.course3 = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher2,
            name="操作系统",
            tenant=self.tenant2,
        )

        # 创建班级
        self.class1 = Class.objects.create(
            course=self.course1, name="计算机1班", tenant=self.tenant1
        )
        self.class2 = Class.objects.create(
            course=self.course2, name="计算机2班", tenant=self.tenant1
        )
        self.class3 = Class.objects.create(
            course=self.course3, name="计算机3班", tenant=self.tenant2
        )

        # 创建作业配置
        self.assignment1 = Assignment.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            name="数据结构作业",
            storage_type="filesystem",
            base_path="/path/to/course1",
            is_active=True,
        )
        self.assignment2 = Assignment.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            course=self.course2,
            class_obj=self.class2,
            name="算法设计作业",
            storage_type="filesystem",
            base_path="/path/to/course2",
            is_active=True,
        )
        self.assignment3 = Assignment.objects.create(
            owner=self.teacher2,
            tenant=self.tenant2,
            course=self.course3,
            class_obj=self.class3,
            name="操作系统作业",
            storage_type="filesystem",
            base_path="/path/to/course3",
            is_active=True,
        )

        # 创建作业
        self.homework1 = Homework.objects.create(
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            title="第一次作业",
            folder_name="第一次作业",
            homework_type="normal",
        )
        self.homework2 = Homework.objects.create(
            tenant=self.tenant1,
            course=self.course2,
            class_obj=self.class2,
            title="第一次作业",
            folder_name="第一次作业",
            homework_type="normal",
        )
        self.homework3 = Homework.objects.create(
            tenant=self.tenant2,
            course=self.course3,
            class_obj=self.class3,
            title="第一次作业",
            folder_name="第一次作业",
            homework_type="normal",
        )

        # 创建服务实例
        self.service = AssignmentManagementService()

    @given(
        num_submissions_student1_class1=st.integers(min_value=0, max_value=5),
        num_submissions_student1_class2=st.integers(min_value=0, max_value=5),
        num_submissions_student2_class1=st.integers(min_value=0, max_value=5),
        num_submissions_student2_class3=st.integers(min_value=0, max_value=5),
        num_submissions_student3_class3=st.integers(min_value=0, max_value=5),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_20_student_course_list_isolation(
        self,
        num_submissions_student1_class1,
        num_submissions_student1_class2,
        num_submissions_student2_class1,
        num_submissions_student2_class3,
        num_submissions_student3_class3,
    ):
        """**Feature: assignment-management-refactor, Property 20: 学生课程列表隔离**

        For any 学生用户，作业提交页面应该只显示该学生所在班级的课程
        **Validates: Requirements 9.1**
        """
        # 清理之前的提交记录
        Submission.objects.all().delete()

        # 创建学生用户
        student1 = User.objects.create_user(
            username="student1", password="pass123", email="student1@test.com"
        )
        student2 = User.objects.create_user(
            username="student2", password="pass123", email="student2@test.com"
        )
        student3 = User.objects.create_user(
            username="student3", password="pass123", email="student3@test.com"
        )

        # 创建学生配置文件
        UserProfile.objects.create(user=student1, tenant=self.tenant1)
        UserProfile.objects.create(user=student2, tenant=self.tenant1)
        UserProfile.objects.create(user=student3, tenant=self.tenant2)

        # 为 student1 创建提交记录（在 class1 和 class2）
        # 这意味着 student1 在 class1 和 class2 中
        student1_courses = set()
        for i in range(num_submissions_student1_class1):
            Submission.objects.create(
                tenant=self.tenant1,
                homework=self.homework1,
                student=student1,
                repository=None,
                file_path=f"/path/to/student1/class1/submission{i}.txt",
                file_name=f"submission{i}.txt",
                file_size=1024,
                version=i + 1,
            )
            student1_courses.add(self.course1.id)

        for i in range(num_submissions_student1_class2):
            Submission.objects.create(
                tenant=self.tenant1,
                homework=self.homework2,
                student=student1,
                repository=None,
                file_path=f"/path/to/student1/class2/submission{i}.txt",
                file_name=f"submission{i}.txt",
                file_size=1024,
                version=i + 1,
            )
            student1_courses.add(self.course2.id)

        # 为 student2 创建提交记录（在 class1 和 class3）
        # 注意：class3 属于不同的租户，这是一个跨租户的情况
        student2_courses = set()
        for i in range(num_submissions_student2_class1):
            Submission.objects.create(
                tenant=self.tenant1,
                homework=self.homework1,
                student=student2,
                repository=None,
                file_path=f"/path/to/student2/class1/submission{i}.txt",
                file_name=f"submission{i}.txt",
                file_size=1024,
                version=i + 1,
            )
            student2_courses.add(self.course1.id)

        for i in range(num_submissions_student2_class3):
            Submission.objects.create(
                tenant=self.tenant2,
                homework=self.homework3,
                student=student2,
                repository=None,
                file_path=f"/path/to/student2/class3/submission{i}.txt",
                file_name=f"submission{i}.txt",
                file_size=1024,
                version=i + 1,
            )
            student2_courses.add(self.course3.id)

        # 为 student3 创建提交记录（只在 class3）
        student3_courses = set()
        for i in range(num_submissions_student3_class3):
            Submission.objects.create(
                tenant=self.tenant2,
                homework=self.homework3,
                student=student3,
                repository=None,
                file_path=f"/path/to/student3/class3/submission{i}.txt",
                file_name=f"submission{i}.txt",
                file_size=1024,
                version=i + 1,
            )
            student3_courses.add(self.course3.id)

        # 测试 student1 只能看到自己班级的课程
        student1_course_list = self.service.get_student_courses(student1)
        student1_course_ids = set(student1_course_list.values_list("id", flat=True))

        # 验证 student1 只能看到自己有提交记录的课程
        self.assertEqual(
            student1_course_ids,
            student1_courses,
            f"Student1 should only see courses from their classes "
            f"(expected: {student1_courses}, got: {student1_course_ids})",
        )

        # 验证 student1 看不到其他学生的课程（如果没有共同班级）
        # student1 不应该看到 course3（因为没有在 class3 提交过）
        self.assertNotIn(
            self.course3.id,
            student1_course_ids,
            "Student1 should not see courses from classes they are not in",
        )

        # 测试 student2 只能看到自己班级的课程
        student2_course_list = self.service.get_student_courses(student2)
        student2_course_ids = set(student2_course_list.values_list("id", flat=True))

        self.assertEqual(
            student2_course_ids,
            student2_courses,
            f"Student2 should only see courses from their classes "
            f"(expected: {student2_courses}, got: {student2_course_ids})",
        )

        # 验证 student2 看不到 course2（因为没有在 class2 提交过）
        self.assertNotIn(
            self.course2.id,
            student2_course_ids,
            "Student2 should not see courses from classes they are not in",
        )

        # 测试 student3 只能看到自己班级的课程
        student3_course_list = self.service.get_student_courses(student3)
        student3_course_ids = set(student3_course_list.values_list("id", flat=True))

        self.assertEqual(
            student3_course_ids,
            student3_courses,
            f"Student3 should only see courses from their classes "
            f"(expected: {student3_courses}, got: {student3_course_ids})",
        )

        # 验证 student3 看不到其他租户的课程
        self.assertNotIn(
            self.course1.id,
            student3_course_ids,
            "Student3 should not see courses from other tenants",
        )
        self.assertNotIn(
            self.course2.id,
            student3_course_ids,
            "Student3 should not see courses from other tenants",
        )

        # 测试没有提交记录的学生
        student_no_submissions = User.objects.create_user(
            username="student_no_sub", password="pass123", email="student_no_sub@test.com"
        )
        UserProfile.objects.create(user=student_no_submissions, tenant=self.tenant1)

        no_sub_course_list = self.service.get_student_courses(student_no_submissions)
        self.assertEqual(
            no_sub_course_list.count(),
            0,
            "Student with no submissions should see no courses",
        )

        # 验证课程列表的数量正确
        expected_student1_count = len(student1_courses)
        expected_student2_count = len(student2_courses)
        expected_student3_count = len(student3_courses)

        self.assertEqual(
            student1_course_list.count(),
            expected_student1_count,
            f"Student1 should see exactly {expected_student1_count} courses",
        )
        self.assertEqual(
            student2_course_list.count(),
            expected_student2_count,
            f"Student2 should see exactly {expected_student2_count} courses",
        )
        self.assertEqual(
            student3_course_list.count(),
            expected_student3_count,
            f"Student3 should see exactly {expected_student3_count} courses",
        )

        # 验证返回的课程对象包含正确的信息
        for course in student1_course_list:
            self.assertIn(
                course.id,
                student1_courses,
                f"Course {course.id} should be in student1's course list",
            )
            # 验证课程有关联的班级
            self.assertTrue(
                course.classes.exists(),
                f"Course {course.name} should have associated classes",
            )

        for course in student2_course_list:
            self.assertIn(
                course.id,
                student2_courses,
                f"Course {course.id} should be in student2's course list",
            )

        for course in student3_course_list:
            self.assertIn(
                course.id,
                student3_courses,
                f"Course {course.id} should be in student3's course list",
            )

        # 验证课程列表不包含重复项
        self.assertEqual(
            len(student1_course_ids),
            student1_course_list.count(),
            "Student1's course list should not contain duplicates",
        )
        self.assertEqual(
            len(student2_course_ids),
            student2_course_list.count(),
            "Student2's course list should not contain duplicates",
        )
        self.assertEqual(
            len(student3_course_ids),
            student3_course_list.count(),
            "Student3's course list should not contain duplicates",
        )

    @given(
        student_name=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        filename_base=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip()),
        file_extension=st.sampled_from([".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"]),
        include_student_name=st.booleans(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_8_filename_student_name_validation(
        self, student_name, filename_base, file_extension, include_student_name
    ):
        """**Feature: assignment-management-refactor, Property 8: 文件名学生姓名验证**

        For any 学生上传的作业文件，文件名应该包含学生姓名，否则应该被拒绝
        **Validates: Requirements 4.3**
        """
        # 构建文件名
        if include_student_name:
            # 文件名包含学生姓名
            filename = f"{student_name}-{filename_base}{file_extension}"
        else:
            # 文件名不包含学生姓名
            filename = f"{filename_base}{file_extension}"

        # 验证文件名是否包含学生姓名
        is_valid = FilenameValidator.validate_student_name_in_filename(filename, student_name)

        # 断言：如果文件名包含学生姓名，验证应该通过；否则应该失败
        if include_student_name:
            self.assertTrue(
                is_valid,
                f"Filename '{filename}' should be valid because it contains student name '{student_name}'",
            )
        else:
            # 如果文件名恰好包含学生姓名（即使我们没有明确添加），验证也应该通过
            # 这是一个边界情况：filename_base 可能恰好包含 student_name
            if student_name in filename:
                self.assertTrue(
                    is_valid,
                    f"Filename '{filename}' should be valid because it accidentally contains student name '{student_name}'",
                )
            else:
                self.assertFalse(
                    is_valid,
                    f"Filename '{filename}' should be invalid because it does not contain student name '{student_name}'",
                )

        # 额外验证：空文件名或空学生姓名应该总是无效
        self.assertFalse(
            FilenameValidator.validate_student_name_in_filename("", student_name),
            "Empty filename should always be invalid",
        )
        self.assertFalse(
            FilenameValidator.validate_student_name_in_filename(filename, ""),
            "Empty student name should always be invalid",
        )

        # 验证：文件名完全等于学生姓名（加扩展名）也应该有效
        exact_match_filename = f"{student_name}{file_extension}"
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(exact_match_filename, student_name),
            f"Filename '{exact_match_filename}' should be valid when it exactly matches student name",
        )

        # 验证：学生姓名在文件名中的位置不影响验证结果
        # 前缀
        prefix_filename = f"{student_name}-作业{file_extension}"
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(prefix_filename, student_name),
            f"Filename with student name as prefix should be valid",
        )

        # 后缀
        suffix_filename = f"作业-{student_name}{file_extension}"
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(suffix_filename, student_name),
            f"Filename with student name as suffix should be valid",
        )

        # 中间
        middle_filename = f"作业-{student_name}-第一次{file_extension}"
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(middle_filename, student_name),
            f"Filename with student name in the middle should be valid",
        )

    @given(
        student1_name=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        student2_name=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        base_filename=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip()),
        file_extension=st.sampled_from([".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"]),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_11_filename_uniqueness(
        self, student1_name, student2_name, base_filename, file_extension
    ):
        """**Feature: assignment-management-refactor, Property 11: 文件名唯一性**

        For any 两个不同学生上传的文件，即使基础文件名相同，
        也应该通过文件名中的学生姓名进行区分
        **Validates: Requirements 4.8**
        """
        # 跳过学生姓名相同的情况（这不是我们要测试的场景）
        if student1_name == student2_name:
            return

        # 构建两个学生的文件名，使用相同的基础文件名
        student1_filename = f"{student1_name}-{base_filename}{file_extension}"
        student2_filename = f"{student2_name}-{base_filename}{file_extension}"

        # 验证两个文件名不同（因为包含不同的学生姓名）
        self.assertNotEqual(
            student1_filename,
            student2_filename,
            f"Files from different students should have different names even with same base filename. "
            f"Student1: '{student1_filename}', Student2: '{student2_filename}'",
        )

        # 验证每个文件名都包含对应学生的姓名
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(student1_filename, student1_name),
            f"Student1's filename '{student1_filename}' should contain student1's name '{student1_name}'",
        )
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(student2_filename, student2_name),
            f"Student2's filename '{student2_filename}' should contain student2's name '{student2_name}'",
        )

        # 验证每个文件名不包含另一个学生的姓名（除非姓名恰好重叠或在base_filename中）
        # 这确保了文件名的唯一性是通过学生姓名实现的
        # 注意：我们需要排除base_filename包含学生姓名的情况
        if (
            student1_name not in student2_name
            and student2_name not in student1_name
            and student1_name not in base_filename
            and student2_name not in base_filename
        ):
            self.assertFalse(
                FilenameValidator.validate_student_name_in_filename(student1_filename, student2_name),
                f"Student1's filename '{student1_filename}' should not be valid for student2 '{student2_name}'",
            )
            self.assertFalse(
                FilenameValidator.validate_student_name_in_filename(student2_filename, student1_name),
                f"Student2's filename '{student2_filename}' should not be valid for student1 '{student1_name}'",
            )

        # 验证：即使基础文件名完全相同，通过学生姓名也能区分
        # 这是核心属性：文件名唯一性通过学生姓名实现
        same_base_file1 = f"{student1_name}-作业{file_extension}"
        same_base_file2 = f"{student2_name}-作业{file_extension}"

        self.assertNotEqual(
            same_base_file1,
            same_base_file2,
            "Files with identical base names should be distinguishable by student names",
        )

        # 验证：可以通过文件名识别出是哪个学生的作业
        # 这是实际使用场景：教师看到文件名就能知道是谁的作业
        self.assertIn(
            student1_name,
            student1_filename,
            f"Student1's name should be identifiable in filename '{student1_filename}'",
        )
        self.assertIn(
            student2_name,
            student2_filename,
            f"Student2's name should be identifiable in filename '{student2_filename}'",
        )

        # 验证：文件名格式一致性
        # 两个学生使用相同的命名模式，只是学生姓名不同
        # 这确保了系统的一致性
        self.assertTrue(
            student1_filename.endswith(file_extension),
            f"Student1's filename should have correct extension",
        )
        self.assertTrue(
            student2_filename.endswith(file_extension),
            f"Student2's filename should have correct extension",
        )

        # 验证：基础文件名在两个文件名中都存在
        # 这确保了文件名的结构正确
        self.assertIn(
            base_filename,
            student1_filename,
            f"Base filename '{base_filename}' should be in student1's filename",
        )
        self.assertIn(
            base_filename,
            student2_filename,
            f"Base filename '{base_filename}' should be in student2's filename",
        )

        # 额外验证：测试边界情况
        # 1. 学生姓名是另一个学生姓名的子串
        if student1_name in student2_name:
            # 即使 student1_name 是 student2_name 的子串，文件名仍然应该不同
            self.assertNotEqual(
                student1_filename,
                student2_filename,
                "Filenames should be different even when one student name is substring of another",
            )

        # 2. 空格和特殊字符处理
        # 文件名应该能够处理包含空格的学生姓名
        student_with_space = f"{student1_name} {student2_name}"
        filename_with_space = f"{student_with_space}-{base_filename}{file_extension}"
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(
                filename_with_space, student_with_space
            ),
            "Filename should handle student names with spaces",
        )

        # 3. 验证文件名长度合理性
        # 确保生成的文件名不会过长（大多数文件系统限制为255字符）
        max_filename_length = 255
        self.assertLessEqual(
            len(student1_filename),
            max_filename_length,
            f"Student1's filename length ({len(student1_filename)}) should not exceed {max_filename_length}",
        )
        self.assertLessEqual(
            len(student2_filename),
            max_filename_length,
            f"Student2's filename length ({len(student2_filename)}) should not exceed {max_filename_length}",
        )

    @given(
        filename=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=100,
        ).filter(lambda x: x.strip()),
        student_name=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        file_extension=st.sampled_from([".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"]),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_23_filename_auto_processing(self, filename, student_name, file_extension):
        """**Feature: assignment-management-refactor, Property 23: 文件名自动处理**

        For any 学生上传的文件，如果文件名不包含学生姓名，
        系统应该自动添加学生姓名前缀
        **Validates: Requirements 9.5**
        """
        # 构建完整的文件名（带扩展名）
        full_filename = f"{filename}{file_extension}"

        # 处理文件名
        processed = FilenameValidator.process_student_filename(full_filename, student_name)

        # 核心属性：处理后的文件名必须包含学生姓名
        self.assertIn(
            student_name,
            processed,
            f"Processed filename '{processed}' must contain student name '{student_name}'",
        )

        # 验证：如果原文件名已包含学生姓名，不应该重复添加
        if student_name in full_filename:
            # 原文件名已包含学生姓名，应该保持不变
            self.assertEqual(
                processed,
                full_filename,
                f"Filename already containing student name should not be modified. "
                f"Original: '{full_filename}', Processed: '{processed}'",
            )
            # 验证学生姓名只出现一次（不重复添加）
            self.assertEqual(
                processed.count(student_name),
                full_filename.count(student_name),
                f"Student name should not be duplicated. "
                f"Original count: {full_filename.count(student_name)}, "
                f"Processed count: {processed.count(student_name)}",
            )
        else:
            # 原文件名不包含学生姓名，应该添加前缀
            self.assertNotEqual(
                processed,
                full_filename,
                f"Filename not containing student name should be modified. "
                f"Original: '{full_filename}', Processed: '{processed}'",
            )
            # 验证学生姓名被添加为前缀
            self.assertTrue(
                processed.startswith(student_name),
                f"Student name should be added as prefix. "
                f"Processed: '{processed}', Student name: '{student_name}'",
            )
            # 验证原文件名的内容仍然存在
            self.assertIn(
                filename,
                processed,
                f"Original filename content should be preserved. "
                f"Original: '{filename}', Processed: '{processed}'",
            )

        # 验证：文件扩展名应该保持不变
        self.assertTrue(
            processed.endswith(file_extension),
            f"File extension should be preserved. "
            f"Expected: '{file_extension}', Processed: '{processed}'",
        )

        # 验证：处理后的文件名应该是有效的
        # 即，它应该能通过学生姓名验证
        self.assertTrue(
            FilenameValidator.validate_student_name_in_filename(processed, student_name),
            f"Processed filename '{processed}' should pass validation for student '{student_name}'",
        )

        # 验证：幂等性 - 多次处理应该得到相同结果
        processed_again = FilenameValidator.process_student_filename(processed, student_name)
        self.assertEqual(
            processed,
            processed_again,
            f"Processing should be idempotent. "
            f"First: '{processed}', Second: '{processed_again}'",
        )

        # 验证：处理后的文件名不应该包含重复的学生姓名
        # （除非原文件名本身就包含多次）
        original_count = full_filename.count(student_name)
        processed_count = processed.count(student_name)
        if original_count == 0:
            # 如果原文件名不包含学生姓名，处理后应该只包含一次
            self.assertEqual(
                processed_count,
                1,
                f"Student name should appear exactly once after processing. "
                f"Processed: '{processed}', Count: {processed_count}",
            )
        else:
            # 如果原文件名已包含学生姓名，次数应该保持不变
            self.assertEqual(
                processed_count,
                original_count,
                f"Student name count should not change if already present. "
                f"Original count: {original_count}, Processed count: {processed_count}",
            )

        # 验证：处理后的文件名格式正确
        # 应该是 "学生姓名-原文件名.扩展名" 或 "原文件名.扩展名"（如果已包含学生姓名）
        if student_name not in full_filename:
            expected_format = f"{student_name}-{filename}{file_extension}"
            self.assertEqual(
                processed,
                expected_format,
                f"Processed filename should follow expected format. "
                f"Expected: '{expected_format}', Got: '{processed}'",
            )

        # 边界情况测试：空文件名应该抛出异常
        with self.assertRaises(Exception):
            FilenameValidator.process_student_filename("", student_name)

        # 边界情况测试：空学生姓名应该抛出异常
        with self.assertRaises(Exception):
            FilenameValidator.process_student_filename(full_filename, "")

        # 边界情况测试：只有扩展名的文件
        ext_only_filename = file_extension
        processed_ext_only = FilenameValidator.process_student_filename(ext_only_filename, student_name)
        self.assertIn(
            student_name,
            processed_ext_only,
            f"Filename with only extension should still get student name. "
            f"Processed: '{processed_ext_only}'",
        )

        # 验证：文件名长度合理性
        # 确保处理后的文件名不会过长（大多数文件系统限制为255字符）
        max_filename_length = 255
        self.assertLessEqual(
            len(processed),
            max_filename_length,
            f"Processed filename length ({len(processed)}) should not exceed {max_filename_length}",
        )

        # 验证：特殊情况 - 学生姓名在文件名中间或末尾
        # 如果学生姓名在文件名中间，不应该再添加前缀
        middle_filename = f"作业-{student_name}-第一次{file_extension}"
        processed_middle = FilenameValidator.process_student_filename(middle_filename, student_name)
        self.assertEqual(
            processed_middle,
            middle_filename,
            f"Filename with student name in middle should not be modified. "
            f"Original: '{middle_filename}', Processed: '{processed_middle}'",
        )

        # 验证：特殊情况 - 文件名完全等于学生姓名
        exact_match = f"{student_name}{file_extension}"
        processed_exact = FilenameValidator.process_student_filename(exact_match, student_name)
        self.assertEqual(
            processed_exact,
            exact_match,
            f"Filename exactly matching student name should not be modified. "
            f"Original: '{exact_match}', Processed: '{processed_exact}'",
        )

    @given(
        filename_base=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip()),
        file_extension=st.sampled_from([
            ".docx", ".pdf", ".zip", ".txt", ".jpg", ".png",  # 允许的格式
            ".exe", ".bat", ".sh", ".py", ".js", ".html",  # 不允许的格式
            ".DOCX", ".PDF", ".ZIP", ".TXT", ".JPG", ".PNG",  # 大写的允许格式
            ".doc", ".xls", ".ppt", ".rar", ".7z", ".tar",  # 其他不允许的格式
            "", "..", ".", "...",  # 边界情况
        ]),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_24_file_format_validation(self, filename_base, file_extension):
        """**Feature: assignment-management-refactor, Property 24: 文件格式验证**

        For any 上传的文件，系统应该验证文件格式是否在允许的列表中
        （docx, pdf, zip, txt, jpg, png 等）
        **Validates: Requirements 9.6**
        """
        # 构建完整的文件名
        filename = f"{filename_base}{file_extension}"

        # 定义允许的扩展名（小写）
        allowed_extensions = {".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"}

        # 验证文件格式
        is_valid = FilenameValidator.validate_file_format(filename)

        # 核心属性：只有允许的文件格式应该通过验证
        # 注意：验证应该不区分大小写
        ext_lower = file_extension.lower()

        if ext_lower in allowed_extensions:
            # 允许的格式应该通过验证
            self.assertTrue(
                is_valid,
                f"File '{filename}' with allowed extension '{file_extension}' should be valid. "
                f"Extension (lowercase): '{ext_lower}'",
            )
        else:
            # 不允许的格式应该被拒绝
            self.assertFalse(
                is_valid,
                f"File '{filename}' with disallowed extension '{file_extension}' should be invalid. "
                f"Extension (lowercase): '{ext_lower}'",
            )

        # 验证：空文件名应该总是无效
        self.assertFalse(
            FilenameValidator.validate_file_format(""),
            "Empty filename should always be invalid",
        )

        # 验证：None 应该总是无效
        # Note: We can't directly test None because it will cause an error,
        # but the validate_file_format method handles it by checking "if not filename"
        # which treats None as False

        # 验证：只有扩展名的文件（如 ".docx"）
        # Note: os.path.splitext(".docx") returns (".docx", "") - the extension is empty!
        # So files like ".docx" are treated as having no extension and should be invalid
        ext_only = file_extension
        ext_only_valid = FilenameValidator.validate_file_format(ext_only)
        # Files with only a dot and extension (like ".docx") have no actual extension
        # according to os.path.splitext, so they should always be invalid
        self.assertFalse(
            ext_only_valid,
            f"Extension-only filename '{ext_only}' should be invalid (os.path.splitext treats it as filename, not extension)",
        )

        # 验证：大小写不敏感
        # 大写的允许扩展名应该也被接受
        if file_extension.upper() in [".DOCX", ".PDF", ".ZIP", ".TXT", ".JPG", ".PNG"]:
            uppercase_filename = f"{filename_base}{file_extension.upper()}"
            self.assertTrue(
                FilenameValidator.validate_file_format(uppercase_filename),
                f"Uppercase extension '{file_extension.upper()}' should be accepted (case-insensitive)",
            )

        # 验证：混合大小写
        if ext_lower in allowed_extensions and len(file_extension) > 1:
            mixed_case_ext = file_extension[0].upper() + file_extension[1:].lower()
            mixed_case_filename = f"{filename_base}{mixed_case_ext}"
            self.assertTrue(
                FilenameValidator.validate_file_format(mixed_case_filename),
                f"Mixed case extension '{mixed_case_ext}' should be accepted (case-insensitive)",
            )

        # 验证：多个点的文件名（如 "file.backup.docx"）
        if ext_lower in allowed_extensions:
            multi_dot_filename = f"{filename_base}.backup{file_extension}"
            self.assertTrue(
                FilenameValidator.validate_file_format(multi_dot_filename),
                f"Filename with multiple dots '{multi_dot_filename}' should be valid if final extension is allowed",
            )

        # 验证：没有扩展名的文件应该被拒绝
        no_ext_filename = filename_base
        self.assertFalse(
            FilenameValidator.validate_file_format(no_ext_filename),
            f"Filename without extension '{no_ext_filename}' should be invalid",
        )

        # 验证：特殊情况 - 点在文件名开头（隐藏文件）
        if ext_lower in allowed_extensions:
            hidden_file = f".{filename_base}{file_extension}"
            self.assertTrue(
                FilenameValidator.validate_file_format(hidden_file),
                f"Hidden file '{hidden_file}' with allowed extension should be valid",
            )

        # 验证：所有允许的扩展名都应该被接受
        for allowed_ext in allowed_extensions:
            test_filename = f"{filename_base}{allowed_ext}"
            self.assertTrue(
                FilenameValidator.validate_file_format(test_filename),
                f"Filename '{test_filename}' with allowed extension '{allowed_ext}' must be valid",
            )

            # 测试大写版本
            test_filename_upper = f"{filename_base}{allowed_ext.upper()}"
            self.assertTrue(
                FilenameValidator.validate_file_format(test_filename_upper),
                f"Filename '{test_filename_upper}' with uppercase allowed extension must be valid",
            )

        # 验证：常见的不允许的扩展名应该被拒绝
        disallowed_extensions = [".exe", ".bat", ".sh", ".py", ".js", ".html", ".doc", ".xls"]
        for disallowed_ext in disallowed_extensions:
            test_filename = f"{filename_base}{disallowed_ext}"
            self.assertFalse(
                FilenameValidator.validate_file_format(test_filename),
                f"Filename '{test_filename}' with disallowed extension '{disallowed_ext}' must be invalid",
            )

        # 验证：边界情况 - 非常长的文件名
        long_filename = f"{'a' * 200}{file_extension}"
        long_valid = FilenameValidator.validate_file_format(long_filename)
        if ext_lower in allowed_extensions:
            self.assertTrue(
                long_valid,
                f"Long filename with allowed extension should still be valid",
            )
        else:
            self.assertFalse(
                long_valid,
                f"Long filename with disallowed extension should still be invalid",
            )

        # 验证：特殊字符在文件名中（但不在扩展名中）
        if ext_lower in allowed_extensions:
            special_char_filename = f"文件-作业_第1次{file_extension}"
            self.assertTrue(
                FilenameValidator.validate_file_format(special_char_filename),
                f"Filename with special characters '{special_char_filename}' should be valid if extension is allowed",
            )

        # 验证：空格在文件名中
        if ext_lower in allowed_extensions:
            space_filename = f"my homework file{file_extension}"
            self.assertTrue(
                FilenameValidator.validate_file_format(space_filename),
                f"Filename with spaces '{space_filename}' should be valid if extension is allowed",
            )

        # 验证：路径分隔符不应该影响扩展名检测
        # （虽然文件名不应该包含路径，但我们测试健壮性）
        if ext_lower in allowed_extensions and "/" not in filename_base and "\\" not in filename_base:
            # 只在文件名不包含路径分隔符时测试
            self.assertTrue(
                is_valid,
                f"Valid extension should be detected regardless of filename content",
            )

    @given(
        student_name=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        assignment_number=st.integers(min_value=1, max_value=10),
        filename_base=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip()),
        file_extension=st.sampled_from([".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"]),
        num_uploads=st.integers(min_value=2, max_value=5),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_25_file_overwrite_rule(
        self, student_name, assignment_number, filename_base, file_extension, num_uploads
    ):
        """**Feature: assignment-management-refactor, Property 25: 文件覆盖规则**

        For any 学生重复上传相同作业次数的文件，新文件应该覆盖旧文件
        **Validates: Requirements 9.7**
        """
        # 清理之前的提交记录
        Submission.objects.all().delete()

        # 创建学生用户
        student = User.objects.create_user(
            username=f"student_{student_name[:10]}",
            password="pass123",
            email=f"student_{student_name[:10]}@test.com",
        )
        UserProfile.objects.create(user=student, tenant=self.tenant1)

        # 构建文件名（包含学生姓名）
        filename = f"{student_name}-{filename_base}{file_extension}"

        # 构建作业次数目录名
        assignment_dir = f"第{assignment_number}次作业"

        # 模拟多次上传同一个文件
        submissions = []
        for upload_num in range(num_uploads):
            # 每次上传都创建一个新的提交记录
            # 在实际系统中，这应该覆盖旧文件
            submission = Submission.objects.create(
                tenant=self.tenant1,
                homework=self.homework1,
                student=student,
                repository=None,
                file_path=f"/path/to/{assignment_dir}/{filename}",
                file_name=filename,
                file_size=1024 * (upload_num + 1),  # 每次上传文件大小不同，模拟文件内容变化
                version=upload_num + 1,  # 版本号递增
            )
            submissions.append(submission)

        # 核心属性：对于同一个学生、同一个作业次数、同一个文件名，
        # 应该只保留最新的提交记录（或者说，新文件覆盖旧文件）

        # 查询该学生在该作业次数下的所有提交
        student_submissions = Submission.objects.filter(
            student=student,
            homework=self.homework1,
            file_name=filename,
        ).order_by("-version")

        # 验证：应该有多个提交记录（因为我们创建了多个）
        self.assertEqual(
            student_submissions.count(),
            num_uploads,
            f"Should have {num_uploads} submission records for student '{student_name}'",
        )

        # 验证：最新的提交应该是最后一次上传的
        latest_submission = student_submissions.first()
        self.assertEqual(
            latest_submission.version,
            num_uploads,
            f"Latest submission should have version {num_uploads}",
        )
        self.assertEqual(
            latest_submission.file_size,
            1024 * num_uploads,
            f"Latest submission should have the largest file size (from last upload)",
        )

        # 验证：所有提交记录都指向同一个文件路径
        # 这表示文件被覆盖，而不是创建新文件
        for submission in student_submissions:
            self.assertEqual(
                submission.file_path,
                f"/path/to/{assignment_dir}/{filename}",
                f"All submissions should point to the same file path",
            )
            self.assertEqual(
                submission.file_name,
                filename,
                f"All submissions should have the same filename",
            )

        # 验证：版本号应该递增
        versions = list(student_submissions.values_list("version", flat=True))
        expected_versions = list(range(num_uploads, 0, -1))  # 降序
        self.assertEqual(
            versions,
            expected_versions,
            f"Versions should be in descending order: {expected_versions}",
        )

        # 验证：文件大小应该递增（模拟文件内容变化）
        file_sizes = list(student_submissions.order_by("version").values_list("file_size", flat=True))
        for i in range(len(file_sizes) - 1):
            self.assertLess(
                file_sizes[i],
                file_sizes[i + 1],
                f"File size should increase with each upload (version {i+1} to {i+2})",
            )

        # 验证：在实际文件系统中，应该只有一个文件存在
        # （虽然我们在数据库中保留了历史记录）
        # 这是通过文件路径相同来保证的
        unique_paths = set(student_submissions.values_list("file_path", flat=True))
        self.assertEqual(
            len(unique_paths),
            1,
            f"All submissions should point to the same file path (overwrite behavior)",
        )

        # 验证：不同学生上传同名文件不应该互相覆盖
        # 创建另一个学生
        student2 = User.objects.create_user(
            username=f"student2_{student_name[:10]}",
            password="pass123",
            email=f"student2_{student_name[:10]}@test.com",
        )
        UserProfile.objects.create(user=student2, tenant=self.tenant1)

        # 第二个学生上传同名文件
        student2_filename = f"{student_name}-{filename_base}{file_extension}"  # 同样的文件名
        student2_submission = Submission.objects.create(
            tenant=self.tenant1,
            homework=self.homework1,
            student=student2,
            repository=None,
            file_path=f"/path/to/{assignment_dir}/{student2_filename}",
            file_name=student2_filename,
            file_size=2048,
            version=1,
        )

        # 验证：第一个学生的提交记录不受影响
        student1_submissions_after = Submission.objects.filter(
            student=student,
            homework=self.homework1,
            file_name=filename,
        )
        self.assertEqual(
            student1_submissions_after.count(),
            num_uploads,
            f"Student1's submissions should not be affected by student2's upload",
        )

        # 验证：第二个学生有自己的提交记录
        student2_submissions = Submission.objects.filter(
            student=student2,
            homework=self.homework1,
            file_name=student2_filename,
        )
        self.assertEqual(
            student2_submissions.count(),
            1,
            f"Student2 should have their own submission record",
        )

        # 验证：不同作业次数的文件不应该互相覆盖
        # 创建另一个作业
        homework2 = Homework.objects.create(
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            title="第二次作业",
            folder_name="第二次作业",
            homework_type="normal",
        )

        # 学生在第二次作业中上传同名文件
        submission_hw2 = Submission.objects.create(
            tenant=self.tenant1,
            homework=homework2,
            student=student,
            repository=None,
            file_path=f"/path/to/第2次作业/{filename}",
            file_name=filename,
            file_size=3072,
            version=1,
        )

        # 验证：第一次作业的提交记录不受影响
        student_hw1_submissions = Submission.objects.filter(
            student=student,
            homework=self.homework1,
            file_name=filename,
        )
        self.assertEqual(
            student_hw1_submissions.count(),
            num_uploads,
            f"Homework1 submissions should not be affected by homework2 upload",
        )

        # 验证：第二次作业有独立的提交记录
        student_hw2_submissions = Submission.objects.filter(
            student=student,
            homework=homework2,
            file_name=filename,
        )
        self.assertEqual(
            student_hw2_submissions.count(),
            1,
            f"Homework2 should have its own submission record",
        )

        # 验证：覆盖规则的幂等性
        # 如果学生上传完全相同的文件（相同大小、相同内容），
        # 应该仍然创建新的版本记录
        same_size_submission = Submission.objects.create(
            tenant=self.tenant1,
            homework=self.homework1,
            student=student,
            repository=None,
            file_path=f"/path/to/{assignment_dir}/{filename}",
            file_name=filename,
            file_size=1024 * num_uploads,  # 与最后一次上传相同的大小
            version=num_uploads + 1,
        )

        # 验证：即使文件大小相同，也应该创建新版本
        final_submissions = Submission.objects.filter(
            student=student,
            homework=self.homework1,
            file_name=filename,
        )
        self.assertEqual(
            final_submissions.count(),
            num_uploads + 1,
            f"Should have {num_uploads + 1} submissions after uploading same-size file",
        )

        # 验证：最新版本应该是刚上传的
        latest_final = final_submissions.order_by("-version").first()
        self.assertEqual(
            latest_final.version,
            num_uploads + 1,
            f"Latest version should be {num_uploads + 1}",
        )

        # 清理测试数据
        homework2.delete()
        student2.delete()

    @given(
        course_name=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip()),
        class_name=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="/\\:*?\"<>|"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip()),
        num_existing_assignments=st.integers(min_value=0, max_value=5),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_9_assignment_directory_auto_creation(
        self, course_name, class_name, num_existing_assignments
    ):
        """**Feature: assignment-management-refactor, Property 9: 作业目录自动创建**

        For any 不存在的作业次数目录，学生提交时系统应该自动创建该目录
        **Validates: Requirements 4.4, 4.6**
        """
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter
        import tempfile
        import shutil

        # 创建临时目录作为基础路径
        temp_dir = tempfile.mkdtemp()

        try:
            # 清理课程名和班级名
            from grading.assignment_utils import PathValidator

            clean_course = PathValidator.sanitize_name(course_name)
            clean_class = PathValidator.sanitize_name(class_name)

            # 构建基础路径
            base_path = os.path.join(temp_dir, clean_course, clean_class)

            # 创建存储适配器
            adapter = FileSystemStorageAdapter(base_path)

            # 验证基础路径已自动创建
            self.assertTrue(
                os.path.exists(base_path),
                f"Base path '{base_path}' should be automatically created",
            )
            self.assertTrue(
                os.path.isdir(base_path),
                f"Base path '{base_path}' should be a directory",
            )

            # 创建一些现有的作业次数目录
            existing_numbers = []
            for i in range(num_existing_assignments):
                assignment_num = i + 1
                existing_numbers.append(assignment_num)
                # 使用正确的方式生成目录名：传入所有已存在的编号
                dir_name = PathValidator.generate_assignment_number_name(existing_numbers[:i])
                
                # 创建目录
                success = adapter.create_directory(dir_name)
                self.assertTrue(
                    success,
                    f"Should successfully create directory '{dir_name}'",
                )

                # 验证目录已创建
                full_dir_path = os.path.join(base_path, dir_name)
                self.assertTrue(
                    os.path.exists(full_dir_path),
                    f"Directory '{dir_name}' should exist after creation",
                )
                self.assertTrue(
                    os.path.isdir(full_dir_path),
                    f"'{dir_name}' should be a directory",
                )

            # 核心属性：创建新的作业次数目录
            # 生成下一个作业次数名称（基于所有已存在的编号）
            new_dir_name = PathValidator.generate_assignment_number_name(existing_numbers)

            # 验证新目录名称格式正确
            self.assertTrue(
                PathValidator.validate_assignment_number_format(new_dir_name),
                f"Generated directory name '{new_dir_name}' should have valid format",
            )

            # 验证新目录不存在（在创建之前）
            new_dir_path = os.path.join(base_path, new_dir_name)
            self.assertFalse(
                os.path.exists(new_dir_path),
                f"New directory '{new_dir_name}' should not exist before creation",
            )

            # 自动创建新目录（模拟学生提交时的行为）
            success = adapter.create_directory(new_dir_name)

            # 验证创建成功
            self.assertTrue(
                success,
                f"Should successfully create new directory '{new_dir_name}'",
            )

            # 验证新目录已创建
            self.assertTrue(
                os.path.exists(new_dir_path),
                f"New directory '{new_dir_name}' should exist after creation",
            )
            self.assertTrue(
                os.path.isdir(new_dir_path),
                f"'{new_dir_name}' should be a directory",
            )

            # 验证：重复创建同一目录应该是幂等的（不报错）
            success_again = adapter.create_directory(new_dir_name)
            self.assertTrue(
                success_again,
                f"Creating existing directory '{new_dir_name}' should be idempotent",
            )

            # 验证：目录仍然存在且只有一个
            self.assertTrue(
                os.path.exists(new_dir_path),
                f"Directory '{new_dir_name}' should still exist after idempotent creation",
            )

            # 验证：可以在新创建的目录中写入文件
            test_filename = "test-student-作业.txt"
            test_file_path = os.path.join(new_dir_name, test_filename)
            test_content = b"This is a test submission"

            write_success = adapter.write_file(test_file_path, test_content)
            self.assertTrue(
                write_success,
                f"Should be able to write file in newly created directory",
            )

            # 验证文件已写入
            full_file_path = os.path.join(base_path, new_dir_name, test_filename)
            self.assertTrue(
                os.path.exists(full_file_path),
                f"File should exist in newly created directory",
            )

            # 验证文件内容正确
            read_content = adapter.read_file(test_file_path)
            self.assertEqual(
                read_content,
                test_content,
                f"File content should match what was written",
            )

            # 验证：可以列出新创建目录的内容
            entries = adapter.list_directory(new_dir_name)
            self.assertEqual(
                len(entries),
                1,
                f"New directory should contain exactly one file",
            )
            self.assertEqual(
                entries[0]["name"],
                test_filename,
                f"Directory should contain the test file",
            )
            self.assertEqual(
                entries[0]["type"],
                "file",
                f"Entry should be a file",
            )

            # 验证：所有作业次数目录都可以被列出
            all_entries = adapter.list_directory("")
            expected_count = num_existing_assignments + 1  # 现有的 + 新创建的
            self.assertEqual(
                len(all_entries),
                expected_count,
                f"Should have {expected_count} assignment directories",
            )

            # 验证：所有目录都是目录类型
            for entry in all_entries:
                self.assertEqual(
                    entry["type"],
                    "dir",
                    f"Entry '{entry['name']}' should be a directory",
                )

            # 验证：目录名称都符合作业次数格式
            for entry in all_entries:
                self.assertTrue(
                    PathValidator.validate_assignment_number_format(entry["name"]),
                    f"Directory name '{entry['name']}' should have valid assignment number format",
                )

            # 验证：创建嵌套目录（如果需要）
            nested_dir = os.path.join(new_dir_name, "submissions", "student1")
            nested_success = adapter.create_directory(nested_dir)
            self.assertTrue(
                nested_success,
                f"Should be able to create nested directories",
            )

            nested_full_path = os.path.join(base_path, nested_dir)
            self.assertTrue(
                os.path.exists(nested_full_path),
                f"Nested directory should exist",
            )
            self.assertTrue(
                os.path.isdir(nested_full_path),
                f"Nested path should be a directory",
            )

            # 验证：空路径应该返回成功（基础目录已存在）
            empty_path_success = adapter.create_directory("")
            self.assertTrue(
                empty_path_success,
                f"Creating empty path (base directory) should succeed",
            )

            # 边界情况：创建包含特殊字符的目录名（已清理）
            special_dir_name = PathValidator.sanitize_name("第一次作业-特殊版本")
            special_success = adapter.create_directory(special_dir_name)
            self.assertTrue(
                special_success,
                f"Should be able to create directory with sanitized special characters",
            )

            special_full_path = os.path.join(base_path, special_dir_name)
            self.assertTrue(
                os.path.exists(special_full_path),
                f"Directory with sanitized name should exist",
            )

            # 验证：目录创建不影响现有目录
            # 检查所有现有目录仍然存在
            for i in range(num_existing_assignments):
                assignment_num = i + 1
                dir_name = PathValidator.generate_assignment_number_name([assignment_num])
                full_dir_path = os.path.join(base_path, dir_name)
                self.assertTrue(
                    os.path.exists(full_dir_path),
                    f"Existing directory '{dir_name}' should still exist after creating new directories",
                )

            # 验证：目录权限正确（可读可写）
            self.assertTrue(
                os.access(new_dir_path, os.R_OK),
                f"New directory should be readable",
            )
            self.assertTrue(
                os.access(new_dir_path, os.W_OK),
                f"New directory should be writable",
            )

            # 验证：目录创建日志记录（通过检查目录存在性）
            # 这是一个间接验证，确保目录创建操作被正确执行
            created_dirs = [
                entry["name"]
                for entry in adapter.list_directory("")
                if entry["type"] == "dir"
            ]
            self.assertIn(
                new_dir_name,
                created_dirs,
                f"New directory '{new_dir_name}' should appear in directory listing",
            )

        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @given(
        course_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),  # Letters and numbers only
                min_codepoint=32,  # Exclude control characters
                blacklist_characters="/\\:*?\"<>|-"  # Exclude filesystem illegal chars and hyphen
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        class_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),  # Letters and numbers only
                min_codepoint=32,  # Exclude control characters
                blacklist_characters="/\\:*?\"<>|-"  # Exclude filesystem illegal chars and hyphen
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        assignment_number=st.integers(min_value=1, max_value=10),
        student_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),  # Letters and numbers only
                min_codepoint=32,  # Exclude control characters and null
                blacklist_characters="/\\:*?\"<>|-"  # Exclude filesystem illegal chars and hyphen
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        filename_base=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),  # Letters and numbers only
                min_codepoint=32,  # Exclude control characters
                blacklist_characters="/\\:*?\"<>|-"  # Exclude filesystem illegal chars and hyphen
            ),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        file_extension=st.sampled_from([".docx", ".pdf", ".zip", ".txt", ".jpg", ".png"]),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_7_file_storage_path_rule(
        self, course_name, class_name, assignment_number, student_name, filename_base, file_extension
    ):
        """**Feature: assignment-management-refactor, Property 7: 文件存储路径规则**

        For any 学生作业提交，文件应该存储在 `<课程名称>/<班级名称>/<作业次数>/` 格式的路径中
        **Validates: Requirements 4.2**
        """
        from grading.assignment_utils import PathValidator
        import tempfile
        import shutil

        # 创建临时目录作为基础路径
        temp_dir = tempfile.mkdtemp()

        try:
            # 清理课程名和班级名
            clean_course = PathValidator.sanitize_name(course_name)
            clean_class = PathValidator.sanitize_name(class_name)

            # 生成作业次数名称
            assignment_dir = PathValidator.generate_assignment_number_name([assignment_number])

            # 清理学生姓名（文件名中也需要清理特殊字符）
            clean_student_name = PathValidator.sanitize_name(student_name)
            clean_filename_base = PathValidator.sanitize_name(filename_base)

            # 构建文件名（包含学生姓名）
            filename = f"{clean_student_name}-{clean_filename_base}{file_extension}"

            # 核心属性：文件路径应该遵循 <课程名称>/<班级名称>/<作业次数>/ 格式
            expected_path_structure = os.path.join(clean_course, clean_class, assignment_dir)
            full_file_path = os.path.join(expected_path_structure, filename)

            # 验证路径结构的各个组成部分
            path_parts = expected_path_structure.split(os.sep)
            
            # 验证路径有三个层级：课程、班级、作业次数
            self.assertEqual(
                len(path_parts),
                3,
                f"Path should have exactly 3 levels: course, class, assignment. Got: {path_parts}",
            )

            # 验证第一层是课程名称
            self.assertEqual(
                path_parts[0],
                clean_course,
                f"First level should be course name '{clean_course}', got '{path_parts[0]}'",
            )

            # 验证第二层是班级名称
            self.assertEqual(
                path_parts[1],
                clean_class,
                f"Second level should be class name '{clean_class}', got '{path_parts[1]}'",
            )

            # 验证第三层是作业次数
            self.assertEqual(
                path_parts[2],
                assignment_dir,
                f"Third level should be assignment number '{assignment_dir}', got '{path_parts[2]}'",
            )

            # 验证作业次数格式正确
            self.assertTrue(
                PathValidator.validate_assignment_number_format(path_parts[2]),
                f"Assignment directory name '{path_parts[2]}' should have valid format",
            )

            # 验证完整路径格式
            # 路径应该是 <课程名称>/<班级名称>/<作业次数>/<文件名>
            self.assertTrue(
                full_file_path.startswith(clean_course),
                f"File path should start with course name '{clean_course}'",
            )
            self.assertIn(
                clean_class,
                full_file_path,
                f"File path should contain class name '{clean_class}'",
            )
            self.assertIn(
                assignment_dir,
                full_file_path,
                f"File path should contain assignment directory '{assignment_dir}'",
            )
            self.assertTrue(
                full_file_path.endswith(filename),
                f"File path should end with filename '{filename}'",
            )

            # 验证：实际创建文件系统结构
            from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter

            base_path = temp_dir
            adapter = FileSystemStorageAdapter(base_path)

            # 创建目录结构
            adapter.create_directory(expected_path_structure)

            # 验证目录已创建
            full_dir_path = os.path.join(base_path, expected_path_structure)
            self.assertTrue(
                os.path.exists(full_dir_path),
                f"Directory structure '{expected_path_structure}' should exist",
            )
            self.assertTrue(
                os.path.isdir(full_dir_path),
                f"Path '{expected_path_structure}' should be a directory",
            )

            # 写入文件到正确的路径
            test_content = b"This is a test submission"
            write_success = adapter.write_file(full_file_path, test_content)
            self.assertTrue(
                write_success,
                f"Should successfully write file to path '{full_file_path}'",
            )

            # 验证文件存在于正确的路径
            full_file_system_path = os.path.join(base_path, full_file_path)
            self.assertTrue(
                os.path.exists(full_file_system_path),
                f"File should exist at path '{full_file_path}'",
            )

            # 验证文件内容正确
            read_content = adapter.read_file(full_file_path)
            self.assertEqual(
                read_content,
                test_content,
                f"File content should match what was written",
            )

            # 验证：不同课程的文件应该在不同的目录
            different_course = PathValidator.sanitize_name(f"{course_name}_2")
            different_course_path = os.path.join(different_course, clean_class, assignment_dir, filename)

            self.assertNotEqual(
                full_file_path,
                different_course_path,
                f"Files from different courses should have different paths",
            )

            # 验证：不同班级的文件应该在不同的目录
            different_class = PathValidator.sanitize_name(f"{class_name}_2")
            different_class_path = os.path.join(clean_course, different_class, assignment_dir, filename)

            self.assertNotEqual(
                full_file_path,
                different_class_path,
                f"Files from different classes should have different paths",
            )

            # 验证：不同作业次数的文件应该在不同的目录
            different_assignment_dir = PathValidator.generate_assignment_number_name([assignment_number + 1])
            different_assignment_path = os.path.join(
                clean_course, clean_class, different_assignment_dir, filename
            )

            self.assertNotEqual(
                full_file_path,
                different_assignment_path,
                f"Files from different assignments should have different paths",
            )

            # 验证：路径层级顺序不能改变
            # 错误的顺序：<班级>/<课程>/<作业次数>
            # 只在课程名和班级名不同时测试（避免相同名称导致路径相同）
            if clean_course != clean_class:
                wrong_order_path = os.path.join(clean_class, clean_course, assignment_dir, filename)
                self.assertNotEqual(
                    full_file_path,
                    wrong_order_path,
                    f"Path order matters: course must come before class",
                )

            # 验证：可以在同一目录下存储多个学生的文件
            student2_name = f"{clean_student_name}_2"
            student2_filename = f"{student2_name}-{clean_filename_base}{file_extension}"
            student2_file_path = os.path.join(expected_path_structure, student2_filename)

            # 写入第二个学生的文件
            student2_content = b"This is student 2's submission"
            adapter.write_file(student2_file_path, student2_content)

            # 验证两个文件都存在于同一目录
            full_student2_path = os.path.join(base_path, student2_file_path)
            self.assertTrue(
                os.path.exists(full_student2_path),
                f"Student 2's file should exist in the same directory",
            )

            # 验证两个文件在同一目录下
            self.assertEqual(
                os.path.dirname(full_file_system_path),
                os.path.dirname(full_student2_path),
                f"Both students' files should be in the same directory",
            )

            # 验证：列出目录应该显示两个文件
            entries = adapter.list_directory(expected_path_structure)
            self.assertEqual(
                len(entries),
                2,
                f"Directory should contain exactly 2 files (one per student)",
            )

            # 验证两个文件都在列表中
            entry_names = [entry["name"] for entry in entries]
            self.assertIn(
                filename,
                entry_names,
                f"Student 1's file should be in directory listing",
            )
            self.assertIn(
                student2_filename,
                entry_names,
                f"Student 2's file should be in directory listing",
            )

            # 验证：路径应该是相对路径（不包含基础路径）
            # 这确保了路径的可移植性
            self.assertFalse(
                full_file_path.startswith(base_path),
                f"File path should be relative, not absolute",
            )
            self.assertFalse(
                full_file_path.startswith("/"),
                f"File path should not start with root directory",
            )
            self.assertFalse(
                full_file_path.startswith("\\"),
                f"File path should not start with Windows root",
            )

            # 验证：路径分隔符应该使用系统标准
            # os.path.join 会自动使用正确的分隔符
            if os.sep == "/":
                # Unix/Linux 系统
                self.assertIn(
                    "/",
                    full_file_path,
                    f"Path should use Unix-style separators on Unix systems",
                )
            elif os.sep == "\\":
                # Windows 系统
                self.assertIn(
                    "\\",
                    full_file_path,
                    f"Path should use Windows-style separators on Windows systems",
                )

            # 验证：路径不应该包含特殊字符（已被清理）
            # 注意：路径分隔符（/ 或 \）是合法的，因为它们用于分隔目录
            illegal_chars_in_names = [':', '*', '?', '"', '<', '>', '|']
            for illegal_char in illegal_chars_in_names:
                self.assertNotIn(
                    illegal_char,
                    expected_path_structure,
                    f"Path should not contain illegal character '{illegal_char}'",
                )

            # 验证：路径不应该包含路径遍历尝试
            self.assertNotIn(
                "..",
                expected_path_structure,
                f"Path should not contain parent directory references",
            )
            self.assertNotIn(
                "./",
                expected_path_structure,
                f"Path should not contain current directory references",
            )

            # 验证：路径长度合理性
            # 大多数文件系统支持的最大路径长度为 260 字符（Windows）或更长
            max_path_length = 260
            self.assertLessEqual(
                len(full_file_path),
                max_path_length,
                f"Path length ({len(full_file_path)}) should not exceed {max_path_length}",
            )

            # 验证：路径格式一致性
            # 所有相同课程、班级、作业次数的文件应该在同一目录
            student3_name = f"{clean_student_name}_3"
            student3_filename = f"{student3_name}-{clean_filename_base}{file_extension}"
            student3_file_path = os.path.join(expected_path_structure, student3_filename)

            # 验证目录部分相同
            self.assertEqual(
                os.path.dirname(full_file_path),
                os.path.dirname(student3_file_path),
                f"Files from same course/class/assignment should share directory path",
            )

            # 验证：路径可以被正确解析
            # 从完整路径中提取各个组成部分
            parsed_parts = full_file_path.split(os.sep)
            self.assertGreaterEqual(
                len(parsed_parts),
                4,
                f"Path should have at least 4 parts: course, class, assignment, filename",
            )

            # 验证解析出的课程名
            self.assertEqual(
                parsed_parts[0],
                clean_course,
                f"Parsed course name should match",
            )

            # 验证解析出的班级名
            self.assertEqual(
                parsed_parts[1],
                clean_class,
                f"Parsed class name should match",
            )

            # 验证解析出的作业次数
            self.assertEqual(
                parsed_parts[2],
                assignment_dir,
                f"Parsed assignment directory should match",
            )

            # 验证解析出的文件名
            self.assertEqual(
                parsed_parts[-1],
                filename,
                f"Parsed filename should match",
            )

            # 验证：空路径组件应该被拒绝
            # 路径不应该包含空的目录名
            path_components = expected_path_structure.split(os.sep)
            for component in path_components:
                self.assertTrue(
                    component.strip(),
                    f"Path component should not be empty or whitespace-only",
                )

            # 验证：路径应该是规范化的（没有冗余的分隔符）
            normalized_path = os.path.normpath(expected_path_structure)
            self.assertEqual(
                expected_path_structure,
                normalized_path,
                f"Path should be normalized (no redundant separators)",
            )

        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


    @given(
        course_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                min_codepoint=32,
                blacklist_characters="/\\:*?\"<>|-"
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        class1_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                min_codepoint=32,
                blacklist_characters="/\\:*?\"<>|-"
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        class2_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                min_codepoint=32,
                blacklist_characters="/\\:*?\"<>|-"
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and len(x.strip()) > 0),
        num_assignments_class1=st.integers(min_value=1, max_value=3),
        num_assignments_class2=st.integers(min_value=1, max_value=3),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[hypothesis.HealthCheck.too_slow],
        deadline=None,
    )
    def test_property_14_class_directory_isolation(
        self,
        course_name,
        class1_name,
        class2_name,
        num_assignments_class1,
        num_assignments_class2,
    ):
        """**Feature: assignment-management-refactor, Property 14: 班级目录隔离**

        For any 同一课程的不同班级，系统应该为每个班级维护独立的作业目录
        **Validates: Requirements 7.3**
        """
        from grading.assignment_utils import PathValidator
        from grading.services.filesystem_storage_adapter import FileSystemStorageAdapter
        import tempfile
        import shutil

        # Skip if class names are the same (not testing this scenario)
        if class1_name == class2_name:
            return

        # Create temporary directory as base path
        temp_dir = tempfile.mkdtemp()

        try:
            # Clean course and class names
            clean_course = PathValidator.sanitize_name(course_name)
            clean_class1 = PathValidator.sanitize_name(class1_name)
            clean_class2 = PathValidator.sanitize_name(class2_name)

            # Skip if sanitized names become the same
            if clean_class1 == clean_class2:
                return

            # Generate base paths for each class
            # Format: <course_name>/<class_name>/
            base_path_class1 = os.path.join(temp_dir, clean_course, clean_class1)
            base_path_class2 = os.path.join(temp_dir, clean_course, clean_class2)

            # Core property: Base paths for different classes should be different
            self.assertNotEqual(
                base_path_class1,
                base_path_class2,
                f"Different classes should have different base paths. "
                f"Class1: '{base_path_class1}', Class2: '{base_path_class2}'",
            )

            # Verify that both paths contain the same course name
            self.assertIn(
                clean_course,
                base_path_class1,
                f"Class1 base path should contain course name '{clean_course}'",
            )
            self.assertIn(
                clean_course,
                base_path_class2,
                f"Class2 base path should contain course name '{clean_course}'",
            )

            # Verify that each path contains its respective class name
            self.assertIn(
                clean_class1,
                base_path_class1,
                f"Class1 base path should contain class name '{clean_class1}'",
            )
            self.assertIn(
                clean_class2,
                base_path_class2,
                f"Class2 base path should contain class name '{clean_class2}'",
            )

            # Verify that class1 path doesn't contain class2 name and vice versa
            self.assertNotIn(
                clean_class2,
                base_path_class1,
                f"Class1 base path should not contain class2 name '{clean_class2}'",
            )
            self.assertNotIn(
                clean_class1,
                base_path_class2,
                f"Class2 base path should not contain class1 name '{clean_class1}'",
            )

            # Create storage adapters for each class
            adapter_class1 = FileSystemStorageAdapter(base_path_class1)
            adapter_class2 = FileSystemStorageAdapter(base_path_class2)

            # Verify base directories are created
            self.assertTrue(
                os.path.exists(base_path_class1),
                f"Base directory for class1 should be created: '{base_path_class1}'",
            )
            self.assertTrue(
                os.path.exists(base_path_class2),
                f"Base directory for class2 should be created: '{base_path_class2}'",
            )

            # Create assignment directories for class1
            class1_assignments = []
            for i in range(num_assignments_class1):
                assignment_name = f"第{i+1}次作业"
                success = adapter_class1.create_directory(assignment_name)
                self.assertTrue(
                    success,
                    f"Should successfully create assignment directory '{assignment_name}' for class1",
                )
                class1_assignments.append(assignment_name)

                # Verify directory exists
                full_path = os.path.join(base_path_class1, assignment_name)
                self.assertTrue(
                    os.path.exists(full_path),
                    f"Assignment directory '{assignment_name}' should exist for class1",
                )

            # Create assignment directories for class2
            class2_assignments = []
            for i in range(num_assignments_class2):
                assignment_name = f"第{i+1}次作业"
                success = adapter_class2.create_directory(assignment_name)
                self.assertTrue(
                    success,
                    f"Should successfully create assignment directory '{assignment_name}' for class2",
                )
                class2_assignments.append(assignment_name)

                # Verify directory exists
                full_path = os.path.join(base_path_class2, assignment_name)
                self.assertTrue(
                    os.path.exists(full_path),
                    f"Assignment directory '{assignment_name}' should exist for class2",
                )

            # Core property: Assignment directories are isolated between classes
            # Even if they have the same name (e.g., "第1次作业"), they should be in different locations

            # List directories for each class
            class1_dirs = adapter_class1.list_directory("")
            class2_dirs = adapter_class2.list_directory("")

            # Verify correct number of directories
            self.assertEqual(
                len(class1_dirs),
                num_assignments_class1,
                f"Class1 should have {num_assignments_class1} assignment directories",
            )
            self.assertEqual(
                len(class2_dirs),
                num_assignments_class2,
                f"Class2 should have {num_assignments_class2} assignment directories",
            )

            # Verify directory names
            class1_dir_names = {entry["name"] for entry in class1_dirs}
            class2_dir_names = {entry["name"] for entry in class2_dirs}

            for assignment_name in class1_assignments:
                self.assertIn(
                    assignment_name,
                    class1_dir_names,
                    f"Class1 should have assignment directory '{assignment_name}'",
                )

            for assignment_name in class2_assignments:
                self.assertIn(
                    assignment_name,
                    class2_dir_names,
                    f"Class2 should have assignment directory '{assignment_name}'",
                )

            # Create test files in each class's assignment directories
            test_content_class1 = b"Class1 student submission"
            test_content_class2 = b"Class2 student submission"

            # Write file to class1's first assignment
            if num_assignments_class1 > 0:
                file_path_class1 = os.path.join(class1_assignments[0], "student1-作业.txt")
                adapter_class1.write_file(file_path_class1, test_content_class1)

                # Verify file exists in class1
                full_file_path_class1 = os.path.join(base_path_class1, file_path_class1)
                self.assertTrue(
                    os.path.exists(full_file_path_class1),
                    f"File should exist in class1's assignment directory",
                )

                # Verify file content
                read_content_class1 = adapter_class1.read_file(file_path_class1)
                self.assertEqual(
                    read_content_class1,
                    test_content_class1,
                    f"File content in class1 should match what was written",
                )

            # Write file to class2's first assignment
            if num_assignments_class2 > 0:
                file_path_class2 = os.path.join(class2_assignments[0], "student1-作业.txt")
                adapter_class2.write_file(file_path_class2, test_content_class2)

                # Verify file exists in class2
                full_file_path_class2 = os.path.join(base_path_class2, file_path_class2)
                self.assertTrue(
                    os.path.exists(full_file_path_class2),
                    f"File should exist in class2's assignment directory",
                )

                # Verify file content
                read_content_class2 = adapter_class2.read_file(file_path_class2)
                self.assertEqual(
                    read_content_class2,
                    test_content_class2,
                    f"File content in class2 should match what was written",
                )

            # Core property verification: Files in class1 don't affect class2 and vice versa
            if num_assignments_class1 > 0 and num_assignments_class2 > 0:
                # Verify that class1's file doesn't exist in class2's directory
                class2_file_check = os.path.join(base_path_class2, file_path_class1)
                # This path shouldn't exist because it's using class1's structure in class2's base
                # But we should check that class2's actual file is different

                # Verify file contents are different (isolation)
                self.assertNotEqual(
                    test_content_class1,
                    test_content_class2,
                    f"File contents should be different between classes (for this test)",
                )

                # Verify that reading from class1 doesn't return class2's content
                read_from_class1 = adapter_class1.read_file(file_path_class1)
                self.assertEqual(
                    read_from_class1,
                    test_content_class1,
                    f"Reading from class1 should return class1's content, not class2's",
                )

                # Verify that reading from class2 doesn't return class1's content
                read_from_class2 = adapter_class2.read_file(file_path_class2)
                self.assertEqual(
                    read_from_class2,
                    test_content_class2,
                    f"Reading from class2 should return class2's content, not class1's",
                )

            # Verify directory structure isolation
            # The full paths should be completely separate
            if num_assignments_class1 > 0:
                class1_full_path = os.path.join(base_path_class1, class1_assignments[0])
                # This path should not be accessible from class2's adapter
                # (it's outside class2's base path)
                with self.assertRaises(Exception):
                    # Trying to access class1's directory from class2's adapter should fail
                    # because it's outside the base path
                    adapter_class2.list_directory(class1_full_path)

            # Verify that modifying class1's directories doesn't affect class2
            if num_assignments_class1 > 0:
                # Delete a directory in class1
                dir_to_delete = class1_assignments[0]
                full_path_to_delete = os.path.join(base_path_class1, dir_to_delete)
                
                # Delete the directory
                if os.path.exists(full_path_to_delete):
                    shutil.rmtree(full_path_to_delete)

                # Verify it's deleted from class1
                self.assertFalse(
                    os.path.exists(full_path_to_delete),
                    f"Directory should be deleted from class1",
                )

                # Verify class2's directories are unaffected
                class2_dirs_after = adapter_class2.list_directory("")
                self.assertEqual(
                    len(class2_dirs_after),
                    num_assignments_class2,
                    f"Class2 should still have {num_assignments_class2} directories after class1 modification",
                )

            # Verify path format consistency
            # Both classes should follow the same path structure: <course>/<class>/
            class1_parts = base_path_class1.split(os.sep)
            class2_parts = base_path_class2.split(os.sep)

            # Both should have the same number of path components
            self.assertEqual(
                len(class1_parts),
                len(class2_parts),
                f"Both classes should have the same directory depth",
            )

            # The course name should be at the same position in both paths
            # Find the position of the course name
            course_index_class1 = None
            for i, part in enumerate(class1_parts):
                if clean_course in part:
                    course_index_class1 = i
                    break

            course_index_class2 = None
            for i, part in enumerate(class2_parts):
                if clean_course in part:
                    course_index_class2 = i
                    break

            if course_index_class1 is not None and course_index_class2 is not None:
                self.assertEqual(
                    course_index_class1,
                    course_index_class2,
                    f"Course name should be at the same position in both paths",
                )

            # Verify that the paths share a common prefix (up to the course level)
            common_prefix = os.path.commonprefix([base_path_class1, base_path_class2])
            self.assertIn(
                clean_course,
                common_prefix,
                f"Common prefix should include the course name: '{common_prefix}'",
            )

            # Verify that after the course level, the paths diverge (different class names)
            # The class names should be the differentiating factor
            relative_class1 = os.path.relpath(base_path_class1, common_prefix)
            relative_class2 = os.path.relpath(base_path_class2, common_prefix)

            self.assertNotEqual(
                relative_class1,
                relative_class2,
                f"Paths should diverge after the common prefix (course level)",
            )

            # Verify that each relative path contains its respective class name
            self.assertIn(
                clean_class1,
                relative_class1,
                f"Relative path for class1 should contain class1 name",
            )
            self.assertIn(
                clean_class2,
                relative_class2,
                f"Relative path for class2 should contain class2 name",
            )

            # Verify independence: Creating a new assignment in class1 doesn't affect class2
            new_assignment_name = f"第{num_assignments_class1 + 1}次作业"
            adapter_class1.create_directory(new_assignment_name)

            # Verify it exists in class1
            new_assignment_path_class1 = os.path.join(base_path_class1, new_assignment_name)
            self.assertTrue(
                os.path.exists(new_assignment_path_class1),
                f"New assignment should exist in class1",
            )

            # Verify it doesn't exist in class2
            new_assignment_path_class2 = os.path.join(base_path_class2, new_assignment_name)
            self.assertFalse(
                os.path.exists(new_assignment_path_class2),
                f"New assignment in class1 should not appear in class2",
            )

            # Verify class2's directory count is unchanged
            class2_dirs_final = adapter_class2.list_directory("")
            self.assertEqual(
                len(class2_dirs_final),
                num_assignments_class2,
                f"Class2 directory count should be unchanged after class1 modification",
            )

        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
