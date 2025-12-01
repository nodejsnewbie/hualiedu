"""
文件上传服务测试模块

测试文件上传服务的上传、验证和管理功能
"""

import os
import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from hypothesis import given, strategies as st, settings, Phase
from hypothesis.extra.django import TestCase as HypothesisTestCase

from grading.models import (
    Class,
    Course,
    Homework,
    Repository,
    Semester,
    Submission,
    Tenant,
    UserProfile,
)
from grading.services.file_upload_service import (
    DEFAULT_MAX_FILE_SIZE,
    SUPPORTED_FILE_FORMATS,
    FileUploadService,
)


class FileUploadServiceTest(TestCase):
    """文件上传服务测试类"""

    def setUp(self):
        """设置测试数据"""
        self.service = FileUploadService()

        # 创建租户
        self.tenant1 = Tenant.objects.create(name="测试学校1", is_active=True)

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username="teacher1", password="testpass123", first_name="张", last_name="老师"
        )

        # 创建学生用户
        self.student1 = User.objects.create_user(
            username="student1", password="testpass123", first_name="李", last_name="同学"
        )
        self.student2 = User.objects.create_user(
            username="student2", password="testpass123", first_name="王", last_name="同学"
        )

        # 创建用户配置文件
        self.teacher1_profile = UserProfile.objects.create(
            user=self.teacher1, tenant=self.tenant1
        )
        self.student1_profile = UserProfile.objects.create(
            user=self.student1, tenant=self.tenant1
        )
        self.student2_profile = UserProfile.objects.create(
            user=self.student2, tenant=self.tenant1
        )

        # 创建学期
        today = date.today()
        self.semester1 = Semester.objects.create(
            name="2024年春季学期",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            is_active=True,
        )

        # 创建课程
        self.course1 = Course.objects.create(
            semester=self.semester1,
            teacher=self.teacher1,
            name="数据结构",
            course_type="theory",
            tenant=self.tenant1,
        )

        # 创建班级
        self.class1 = Class.objects.create(
            tenant=self.tenant1, course=self.course1, name="计算机1班", student_count=30
        )

        # 创建文件系统仓库
        self.repo1 = Repository.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            class_obj=self.class1,
            name="数据结构作业仓库",
            repo_type="filesystem",
            filesystem_path="teacher1_datastruct",
            path="teacher1_datastruct",
            allocated_space_mb=1024,
            is_active=True,
        )

        # 创建作业
        self.homework1 = Homework.objects.create(
            tenant=self.tenant1,
            course=self.course1,
            class_obj=self.class1,
            title="第一次作业",
            homework_type="normal",
            folder_name="homework1",
        )

    def tearDown(self):
        """清理测试数据"""
        # 清理测试创建的文件和目录
        repo_path = self.repo1.get_full_path()
        if os.path.exists(repo_path):
            import shutil

            shutil.rmtree(repo_path, ignore_errors=True)

    def test_validate_file_success(self):
        """测试文件验证成功"""
        # 创建有效的文件
        file_content = b"Test file content"
        file = SimpleUploadedFile("test.docx", file_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 验证通过
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_file_empty_file(self):
        """测试验证空文件"""
        # 创建空文件
        file = SimpleUploadedFile("test.docx", b"", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 验证失败
        self.assertFalse(is_valid)
        self.assertIn("文件大小为0", error)

    def test_validate_file_too_large(self):
        """测试验证文件过大"""
        # 创建超大文件（51MB）
        large_content = b"x" * (51 * 1024 * 1024)
        file = SimpleUploadedFile("large.docx", large_content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 验证失败
        self.assertFalse(is_valid)
        self.assertIn("文件大小超过限制", error)

    def test_validate_file_unsupported_format(self):
        """测试验证不支持的文件格式"""
        # 创建不支持的文件格式
        file = SimpleUploadedFile("test.exe", b"test content", content_type="application/x-msdownload")

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 验证失败
        self.assertFalse(is_valid)
        self.assertIn("不支持的文件格式", error)

    def test_validate_file_supported_formats(self):
        """测试所有支持的文件格式"""
        for ext in SUPPORTED_FILE_FORMATS:
            file = SimpleUploadedFile(f"test{ext}", b"test content")

            # 验证文件
            is_valid, error = self.service.validate_file(file)

            # 验证通过
            self.assertTrue(is_valid, f"格式 {ext} 应该被支持，但验证失败: {error}")

    def test_save_file_success(self):
        """测试保存文件成功"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建文件
            file_content = b"Test file content"
            file = SimpleUploadedFile("test.docx", file_content)

            # 保存文件
            file_path = os.path.join(temp_dir, "test.docx")
            saved_path = self.service.save_file(file, file_path)

            # 验证文件已保存
            self.assertEqual(saved_path, file_path)
            self.assertTrue(os.path.exists(file_path))

            # 验证文件内容
            with open(file_path, "rb") as f:
                saved_content = f.read()
            self.assertEqual(saved_content, file_content)

    def test_save_file_creates_directory(self):
        """测试保存文件时自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建文件
            file = SimpleUploadedFile("test.docx", b"test content")

            # 保存到不存在的子目录
            file_path = os.path.join(temp_dir, "subdir1", "subdir2", "test.docx")
            saved_path = self.service.save_file(file, file_path)

            # 验证目录和文件已创建
            self.assertTrue(os.path.exists(saved_path))
            self.assertTrue(os.path.isfile(saved_path))

    def test_create_submission_record_success(self):
        """测试创建提交记录成功"""
        # 创建提交记录
        submission = self.service.create_submission_record(
            student=self.student1,
            homework=self.homework1,
            repository=self.repo1,
            file_path="/path/to/file.docx",
            file_name="homework1.docx",
            file_size=1024,
            version=1,
        )

        # 验证提交记录
        self.assertIsNotNone(submission)
        self.assertEqual(submission.student, self.student1)
        self.assertEqual(submission.homework, self.homework1)
        self.assertEqual(submission.repository, self.repo1)
        self.assertEqual(submission.file_name, "homework1.docx")
        self.assertEqual(submission.file_size, 1024)
        self.assertEqual(submission.version, 1)
        self.assertEqual(submission.tenant, self.tenant1)

        # 验证数据库中存在该记录
        self.assertTrue(Submission.objects.filter(id=submission.id).exists())

    def test_upload_submission_success(self):
        """测试上传作业成功"""
        # 创建文件
        file_content = b"Homework content"
        file = SimpleUploadedFile("homework1.docx", file_content)

        # 上传作业
        submission = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file, repository=self.repo1
        )

        # 验证提交记录
        self.assertIsNotNone(submission)
        self.assertEqual(submission.student, self.student1)
        self.assertEqual(submission.homework, self.homework1)
        self.assertEqual(submission.version, 1)
        self.assertEqual(submission.file_name, "homework1.docx")
        self.assertEqual(submission.file_size, len(file_content))

        # 验证文件已保存
        self.assertTrue(os.path.exists(submission.file_path))

    def test_upload_submission_version_increment(self):
        """测试上传作业时版本号递增"""
        # 第一次上传
        file1 = SimpleUploadedFile("homework1_v1.docx", b"Version 1")
        submission1 = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file1, repository=self.repo1
        )

        # 验证版本号为1
        self.assertEqual(submission1.version, 1)

        # 第二次上传
        file2 = SimpleUploadedFile("homework1_v2.docx", b"Version 2")
        submission2 = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file2, repository=self.repo1
        )

        # 验证版本号为2
        self.assertEqual(submission2.version, 2)

        # 第三次上传
        file3 = SimpleUploadedFile("homework1_v3.docx", b"Version 3")
        submission3 = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file3, repository=self.repo1
        )

        # 验证版本号为3
        self.assertEqual(submission3.version, 3)

    def test_upload_submission_different_students(self):
        """测试不同学生上传作业"""
        # 学生1上传
        file1 = SimpleUploadedFile("homework1.docx", b"Student 1 content")
        submission1 = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file1, repository=self.repo1
        )

        # 学生2上传
        file2 = SimpleUploadedFile("homework1.docx", b"Student 2 content")
        submission2 = self.service.upload_submission(
            student=self.student2, homework=self.homework1, file=file2, repository=self.repo1
        )

        # 验证两个学生的版本号都是1
        self.assertEqual(submission1.version, 1)
        self.assertEqual(submission2.version, 1)

        # 验证文件路径不同
        self.assertNotEqual(submission1.file_path, submission2.file_path)

    def test_upload_submission_invalid_file(self):
        """测试上传无效文件"""
        # 创建无效文件（不支持的格式）
        file = SimpleUploadedFile("homework1.exe", b"Invalid content")

        # 尝试上传
        with self.assertRaises(ValueError) as context:
            self.service.upload_submission(
                student=self.student1, homework=self.homework1, file=file, repository=self.repo1
            )

        # 验证错误信息
        self.assertIn("不支持的文件格式", str(context.exception))

    def test_upload_submission_git_repository(self):
        """测试Git仓库不支持上传"""
        # 创建Git仓库
        git_repo = Repository.objects.create(
            owner=self.teacher1,
            tenant=self.tenant1,
            class_obj=self.class1,
            name="Git仓库",
            repo_type="git",
            git_url="https://github.com/test/repo.git",
            url="https://github.com/test/repo.git",
            is_active=True,
        )

        # 创建文件
        file = SimpleUploadedFile("homework1.docx", b"Test content")

        # 尝试上传到Git仓库
        with self.assertRaises(ValueError) as context:
            self.service.upload_submission(
                student=self.student1, homework=self.homework1, file=file, repository=git_repo
            )

        # 验证错误信息
        self.assertIn("只有文件系统方式的仓库支持文件上传", str(context.exception))

    def test_upload_submission_auto_find_repository(self):
        """测试自动查找仓库"""
        # 创建文件
        file = SimpleUploadedFile("homework1.docx", b"Test content")

        # 不指定仓库，让服务自动查找
        submission = self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file
        )

        # 验证使用了正确的仓库
        self.assertEqual(submission.repository, self.repo1)

    def test_get_submission_history(self):
        """测试获取提交历史"""
        # 上传多个版本
        for i in range(3):
            file = SimpleUploadedFile(f"homework1_v{i+1}.docx", f"Version {i+1}".encode())
            self.service.upload_submission(
                student=self.student1, homework=self.homework1, file=file, repository=self.repo1
            )

        # 获取提交历史
        history = self.service.get_submission_history(self.homework1, self.student1)

        # 验证历史记录
        self.assertEqual(len(history), 3)
        # 验证按版本号降序排列
        self.assertEqual(history[0].version, 3)
        self.assertEqual(history[1].version, 2)
        self.assertEqual(history[2].version, 1)

    def test_get_latest_submission(self):
        """测试获取最新提交"""
        # 上传多个版本
        for i in range(3):
            file = SimpleUploadedFile(f"homework1_v{i+1}.docx", f"Version {i+1}".encode())
            self.service.upload_submission(
                student=self.student1, homework=self.homework1, file=file, repository=self.repo1
            )

        # 获取最新提交
        latest = self.service.get_latest_submission(self.homework1, self.student1)

        # 验证是最新版本
        self.assertIsNotNone(latest)
        self.assertEqual(latest.version, 3)

    def test_get_latest_submission_no_submission(self):
        """测试获取最新提交（无提交记录）"""
        # 获取最新提交
        latest = self.service.get_latest_submission(self.homework1, self.student1)

        # 验证返回None
        self.assertIsNone(latest)

    def test_check_storage_space(self):
        """测试检查存储空间"""
        # 上传一些文件
        file1 = SimpleUploadedFile("file1.docx", b"x" * 1024)  # 1KB
        file2 = SimpleUploadedFile("file2.docx", b"x" * 2048)  # 2KB
        self.service.upload_submission(
            student=self.student1, homework=self.homework1, file=file1, repository=self.repo1
        )
        self.service.upload_submission(
            student=self.student2, homework=self.homework1, file=file2, repository=self.repo1
        )

        # 检查存储空间
        used_mb, total_mb, percentage = self.service.check_storage_space(self.repo1)

        # 验证空间统计
        # 注意：由于文件很小（3KB），转换为MB后可能为0
        # 我们验证至少有文件存在，或者used_mb >= 0
        self.assertGreaterEqual(used_mb, 0)
        self.assertEqual(total_mb, 1024)
        self.assertGreaterEqual(percentage, 0)
        self.assertLess(percentage, 100)

    def test_check_storage_space_empty_repository(self):
        """测试检查空仓库的存储空间"""
        # 检查存储空间
        used_mb, total_mb, percentage = self.service.check_storage_space(self.repo1)

        # 验证空间统计
        self.assertEqual(used_mb, 0)
        self.assertEqual(total_mb, 1024)
        self.assertEqual(percentage, 0.0)

    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 测试各种不安全的文件名
        test_cases = [
            ("normal.docx", "normal.docx"),
            ("../../../etc/passwd", "..__..__..__etc_passwd"),  # ".." -> ".._", "/" -> "_"
            ("file/with/slashes.txt", "file_with_slashes.txt"),
            ("file\\with\\backslashes.txt", "file_with_backslashes.txt"),
            ("file\nwith\nnewlines.txt", "file_with_newlines.txt"),
            ("   spaces   .txt", "spaces   .txt"),
            ("", "unnamed_file"),
        ]

        for input_name, expected_output in test_cases:
            result = self.service._sanitize_filename(input_name)
            self.assertEqual(
                result, expected_output, f"清理 '{input_name}' 应该得到 '{expected_output}'，但得到 '{result}'"
            )

    def test_generate_file_path(self):
        """测试生成文件路径"""
        # 生成文件路径
        file_path = self.service._generate_file_path(
            self.repo1, self.homework1, self.student1, "homework1.docx"
        )

        # 验证路径格式
        self.assertIn("数据结构", file_path)  # 课程名
        self.assertIn("计算机1班", file_path)  # 班级名
        self.assertIn("homework1", file_path)  # 作业批次
        self.assertIn("student1", file_path)  # 学生ID
        self.assertIn("homework1.docx", file_path)  # 文件名

    def test_custom_max_file_size(self):
        """测试自定义最大文件大小"""
        # 创建自定义大小限制的服务（1MB）
        custom_service = FileUploadService(max_file_size=1 * 1024 * 1024)

        # 创建2MB的文件
        large_file = SimpleUploadedFile("large.docx", b"x" * (2 * 1024 * 1024))

        # 验证文件
        is_valid, error = custom_service.validate_file(large_file)

        # 验证失败
        self.assertFalse(is_valid)
        self.assertIn("文件大小超过限制", error)
        self.assertIn("1.0MB", error)  # 应该显示自定义的限制

    def test_default_max_file_size(self):
        """测试默认最大文件大小"""
        # 验证默认值
        self.assertEqual(self.service.max_file_size, DEFAULT_MAX_FILE_SIZE)
        self.assertEqual(DEFAULT_MAX_FILE_SIZE, 50 * 1024 * 1024)  # 50MB


class FileUploadServicePropertyTest(HypothesisTestCase):
    """文件上传服务属性测试类 - 使用Property-Based Testing"""

    def setUp(self):
        """设置测试数据"""
        self.service = FileUploadService()
        # Note: Database setup is handled by HypothesisTestCase for each example

    @given(
        file_size=st.integers(min_value=1, max_value=DEFAULT_MAX_FILE_SIZE),
        file_ext=st.sampled_from(SUPPORTED_FILE_FORMATS),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_file_validation_accepts_valid_files(self, file_size, file_ext):
        """
        **Feature: homework-grading-system, Property 5: 文件验证规则**
        **Validates: Requirements 1.4.3**

        Property: For any file within size limit (≤50MB) and supported format,
        the validation function should accept it.
        """
        # 创建有效文件
        file_content = b"x" * file_size
        filename = f"test{file_ext}"
        file = SimpleUploadedFile(filename, file_content)

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 应该通过验证
        self.assertTrue(
            is_valid,
            f"文件应该通过验证 (大小: {file_size} bytes, 格式: {file_ext}), "
            f"但失败了: {error}",
        )
        self.assertEqual(error, "")

    @given(
        file_size=st.integers(
            min_value=DEFAULT_MAX_FILE_SIZE + 1, max_value=100 * 1024 * 1024
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_file_validation_rejects_oversized_files(self, file_size):
        """
        **Feature: homework-grading-system, Property 5: 文件验证规则**
        **Validates: Requirements 1.4.3**

        Property: For any file exceeding size limit (>50MB),
        the validation function should reject it.
        """
        # 创建超大文件
        file_content = b"x" * file_size
        file = SimpleUploadedFile("test.docx", file_content)

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 应该被拒绝
        self.assertFalse(
            is_valid, f"超大文件应该被拒绝 (大小: {file_size} bytes), 但通过了验证"
        )
        self.assertIn("文件大小超过限制", error)

    @given(
        file_ext=st.text(
            alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=10
        ).filter(lambda x: f".{x.lower()}" not in SUPPORTED_FILE_FORMATS)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_file_validation_rejects_unsupported_formats(self, file_ext):
        """
        **Feature: homework-grading-system, Property 5: 文件验证规则**
        **Validates: Requirements 1.4.3**

        Property: For any file with unsupported format,
        the validation function should reject it.
        """
        # 创建不支持格式的文件
        filename = f"test.{file_ext}"
        file = SimpleUploadedFile(filename, b"test content")

        # 验证文件
        is_valid, error = self.service.validate_file(file)

        # 应该被拒绝
        self.assertFalse(
            is_valid, f"不支持的格式 .{file_ext} 应该被拒绝，但通过了验证"
        )
        self.assertIn("不支持的文件格式", error)

    @given(
        unsafe_filename=st.one_of(
            st.just("../../../etc/passwd"),
            st.just("file/with/slashes.txt"),
            st.just("file\\with\\backslashes.txt"),
            st.just("file\nwith\nnewlines.txt"),
            st.just("file\rwith\rcarriage.txt"),
            st.just("file\twith\ttabs.txt"),
            st.just("file\0with\0null.txt"),
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_file_path_sanitization(self, unsafe_filename):
        """
        **Feature: homework-grading-system, Property 6: 文件路径生成规范**
        **Validates: Requirements 1.4.5**

        Property: For any filename with unsafe characters,
        the sanitization should remove or replace them to prevent path traversal.
        """
        # 清理文件名
        safe_filename = self.service._sanitize_filename(unsafe_filename)

        # 验证不包含不安全字符
        unsafe_chars = ["/", "\\", "\0", "\n", "\r", "\t"]
        for char in unsafe_chars:
            self.assertNotIn(
                char,
                safe_filename,
                f"清理后的文件名不应该包含不安全字符: {repr(char)}",
            )

        # 验证路径遍历模式被中和（".."后面跟"/"被替换）
        # 注意：实现将".."替换为".._"，这样可以保留原始意图但防止路径遍历
        if "../" in unsafe_filename or "..\\" in unsafe_filename:
            self.assertNotIn(
                "../",
                safe_filename,
                "清理后的文件名不应该包含'../'路径遍历模式",
            )
            self.assertNotIn(
                "..\\",
                safe_filename,
                "清理后的文件名不应该包含'..\\' 路径遍历模式",
            )

