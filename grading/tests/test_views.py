"""
视图测试
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.test import Client, TestCase
from django.urls import reverse

from grading.models import (
    Course,
    CourseSchedule,
    GradeTypeConfig,
    Homework,
    Repository,
    Semester,
    Tenant,
    UserProfile,
)

from .base import APITestCase, BaseTestCase, MockTestCase


class IndexViewTest(BaseTestCase):
    """首页视图测试"""

    def test_index_view_get(self):
        """测试首页GET请求"""
        response = self.client.get(reverse("grading:index"))
        self.assertResponseOK(response)
        self.assertContains(response, "华立教育")

    def test_index_view_with_semester(self):
        """测试带学期数据的首页"""
        semester = Semester.objects.create(
            name="2024年春季学期", start_date="2024-02-26", end_date="2024-06-30"
        )
        response = self.client.get(reverse("grading:index"))
        self.assertResponseOK(response)
        self.assertContains(response, semester.name)


class AuthenticationViewTest(BaseTestCase):
    """认证相关视图测试"""

    def test_login_required_views(self):
        """测试需要登录的视图"""
        protected_urls = [
            reverse("grading:grading_page"),
            reverse("grading:batch_grade_page"),
            reverse("grading:calendar_view"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            # 应该重定向到登录页面
            self.assertResponseRedirect(response)

    def test_staff_required_views(self):
        """测试需要管理员权限的视图"""
        self.login_user()

        staff_urls = [
            reverse("grading:grade_type_management"),
        ]

        for url in staff_urls:
            response = self.client.get(url)
            # 普通用户应该被拒绝访问
            self.assertResponseForbidden(response)

    def test_staff_views_with_staff_user(self):
        """测试管理员用户访问管理员视图"""
        self.login_user(self.admin_user)

        response = self.client.get(reverse("grading:grade_type_management"))
        self.assertResponseOK(response)


class GradingViewTest(MockTestCase):
    """评分视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/base"
        )
        self.repository = Repository.objects.create(
            tenant=self.tenant, name="测试仓库", path="test_repo"
        )

    def test_grading_page_get(self):
        """测试评分页面GET请求"""
        self.login_user()
        response = self.client.get(reverse("grading:grading_page"))
        self.assertResponseOK(response)

    def test_grading_page_post_with_valid_data(self):
        """测试评分页面POST请求（有效数据）"""
        self.login_user()

        with patch("grading.views.os.path.exists", return_value=True):
            with patch("grading.views.os.listdir", return_value=["file1.txt", "file2.txt"]):
                response = self.client.post(
                    reverse("grading:grading_page"), {"base_dir": "/test/path"}
                )
                self.assertResponseOK(response)

    @patch("grading.views.volcengine_score_homework")
    def test_ai_score_view(self, mock_ai_score):
        """测试AI评分视图"""
        mock_ai_score.return_value = (85, "评分：85分。内容充实。")

        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("builtins.open", mock_open(read_data="测试内容")):
                response = self.client.post(reverse("grading:ai_score"), {"path": "test_file.txt"})

                self.assertResponseOK(response)
                data = response.json()
                self.assertEqual(data["score"], 85)
                self.assertIn("评分", data["comment"])

    def test_save_grade_view(self):
        """测试保存评分视图"""
        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.path.exists", return_value=True):
                with patch("builtins.open", mock_open()):
                    response = self.client.post(
                        reverse("grading:save_grade"),
                        {"file_path": "test_file.txt", "grade": "A", "comment": "优秀作业"},
                    )

                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertTrue(data["success"])


class FileOperationViewTest(MockTestCase):
    """文件操作视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/base"
        )

    def test_get_file_content_view(self):
        """测试获取文件内容视图"""
        self.login_user()

        test_content = "这是测试文件内容"
        with patch("grading.views.validate_file_path", return_value=True):
            with patch("builtins.open", mock_open(read_data=test_content)):
                response = self.client.post(
                    reverse("grading:get_file_content"), {"file_path": "test_file.txt"}
                )

                self.assertResponseOK(response)
                data = response.json()
                self.assertEqual(data["content"], test_content)

    def test_create_directory_view(self):
        """测试创建目录视图"""
        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.makedirs") as mock_makedirs:
                with patch("grading.views.os.path.exists", return_value=False):
                    response = self.client.post(
                        reverse("grading:create_directory"), {"directory_path": "/test/new_dir"}
                    )

                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertTrue(data["success"])
                    mock_makedirs.assert_called_once()

    def test_serve_file_view(self):
        """测试文件服务视图"""
        test_content = b"test file content"

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.path.exists", return_value=True):
                with patch("grading.views.os.path.getsize", return_value=len(test_content)):
                    with patch("builtins.open", mock_open(read_data=test_content)):
                        response = self.client.get(
                            reverse("grading:serve_file", args=["test_file.txt"])
                        )

                        self.assertResponseOK(response)
                        self.assertEqual(response.content, test_content)


class BatchOperationViewTest(MockTestCase):
    """批量操作视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/base"
        )

    def test_batch_grade_page_view(self):
        """测试批量登分页面"""
        self.login_user()
        response = self.client.get(reverse("grading:batch_grade_page"))
        self.assertResponseOK(response)
        self.assertContains(response, "批量登分")

    def test_batch_ai_score_page_view(self):
        """测试批量AI评分页面"""
        self.login_user()
        response = self.client.get(reverse("grading:batch_ai_score_page"))
        self.assertResponseOK(response)
        self.assertContains(response, "批量AI评分")

    @patch("grading.views.volcengine_score_homework")
    def test_batch_ai_score_view(self, mock_ai_score):
        """测试批量AI评分功能"""
        mock_ai_score.return_value = (85, "评分：85分")

        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.path.exists", return_value=True):
                with patch("grading.views.os.listdir", return_value=["file1.txt", "file2.txt"]):
                    with patch("builtins.open", mock_open(read_data="测试内容")):
                        response = self.client.post(
                            reverse("grading:batch_ai_score"), {"directory_path": "/test/batch_dir"}
                        )

                        self.assertEqual(response.status_code, 200)
                        data = response.json()
                        self.assertTrue(data["success"])


class CalendarViewTest(BaseTestCase):
    """校历视图测试"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date="2024-02-26", end_date="2024-06-30"
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.teacher_user,
            name="Python程序设计",
            location="A101",
        )

    def test_calendar_view_get(self):
        """测试校历视图GET请求"""
        self.login_user()
        response = self.client.get(reverse("grading:calendar_view"))
        self.assertResponseOK(response)
        self.assertContains(response, "校历")

    def test_semester_management_view(self):
        """测试学期管理视图"""
        self.login_user()
        response = self.client.get(reverse("grading:semester_management"))
        self.assertResponseOK(response)
        self.assertContains(response, self.semester.name)

    def test_course_management_view(self):
        """测试课程管理视图"""
        self.login_user()
        response = self.client.get(reverse("grading:course_management"))
        self.assertResponseOK(response)

    def test_add_course_view(self):
        """测试添加课程视图"""
        self.login_user()

        response = self.client.post(
            reverse("grading:add_course"),
            {
                "semester_id": self.semester.id,
                "name": "新课程",
                "location": "B202",
                "class_name": "计算机2班",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # 验证课程已创建
        self.assertTrue(Course.objects.filter(name="新课程").exists())


class GradeTypeManagementViewTest(BaseTestCase):
    """评分类型管理视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.admin_user, tenant=self.tenant, is_tenant_admin=True
        )

    def test_grade_type_management_view(self):
        """测试评分类型管理页面"""
        self.login_user(self.admin_user)
        response = self.client.get(reverse("grading:grade_type_management"))
        self.assertResponseOK(response)
        self.assertContains(response, "评分类型管理")

    def test_change_grade_type_view(self):
        """测试更改评分类型"""
        self.login_user(self.admin_user)

        response = self.client.post(
            reverse("grading:change_grade_type"),
            {"class_identifier": "计算机1班", "grade_type": "letter"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # 验证配置已创建
        config = GradeTypeConfig.objects.get(tenant=self.tenant, class_identifier="计算机1班")
        self.assertEqual(config.grade_type, "letter")

    def test_get_grade_type_config_view(self):
        """测试获取评分类型配置"""
        # 创建测试配置
        GradeTypeConfig.objects.create(
            tenant=self.tenant, class_identifier="计算机1班", grade_type="text"
        )

        self.login_user(self.admin_user)

        response = self.client.get(
            reverse("grading:get_grade_type_config"), {"class_identifier": "计算机1班"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["grade_type"], "text")


class APIViewTest(APITestCase):
    """API视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(
            user=self.user, tenant=self.tenant, repo_base_dir="/test/base"
        )

    def test_get_directory_tree_api(self):
        """测试获取目录树API"""
        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.path.exists", return_value=True):
                with patch("grading.views.os.listdir", return_value=["dir1", "file1.txt"]):
                    with patch("grading.views.os.path.isdir", side_effect=lambda x: "dir1" in x):
                        response = self.api_get(
                            reverse("grading:get_directory_tree"), {"path": "/test/path"}
                        )

                        self.assertResponseOK(response)
                        data = response.json()
                        self.assertIn("children", data)

    def test_get_file_grade_info_api(self):
        """测试获取文件评分信息API"""
        self.login_user()

        test_content = "文件内容\n评分：A\n评语：优秀"
        with patch("grading.views.validate_file_path", return_value=True):
            with patch("builtins.open", mock_open(read_data=test_content)):
                response = self.api_get(
                    reverse("grading:get_file_grade_info"), {"file_path": "test_file.txt"}
                )

                self.assertResponseOK(response)
                data = response.json()
                self.assertEqual(data["grade"], "A")
                self.assertEqual(data["comment"], "优秀")


class ErrorHandlingViewTest(MockTestCase):
    """错误处理视图测试"""

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="测试租户")
        self.user_profile = UserProfile.objects.create(user=self.user, tenant=self.tenant)

    def test_invalid_file_path(self):
        """测试无效文件路径处理"""
        self.login_user()

        with patch("grading.views.validate_file_path", return_value=False):
            response = self.client.post(
                reverse("grading:get_file_content"), {"file_path": "../../../etc/passwd"}
            )

            self.assertResponseForbidden(response)

    def test_file_not_found(self):
        """测试文件不存在处理"""
        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.os.path.exists", return_value=False):
                response = self.client.post(
                    reverse("grading:get_file_content"), {"file_path": "nonexistent_file.txt"}
                )

                self.assertEqual(response.status_code, 404)

    @patch("grading.views.volcengine_score_homework")
    def test_ai_api_error(self, mock_ai_score):
        """测试AI API错误处理"""
        mock_ai_score.side_effect = Exception("API错误")

        self.login_user()

        with patch("grading.views.validate_file_path", return_value=True):
            with patch("builtins.open", mock_open(read_data="测试内容")):
                response = self.client.post(reverse("grading:ai_score"), {"path": "test_file.txt"})

                self.assertEqual(response.status_code, 500)
                data = response.json()
                self.assertFalse(data["success"])
                self.assertIn("错误", data["error"])


class PermissionViewTest(BaseTestCase):
    """权限测试"""

    def setUp(self):
        super().setUp()
        self.tenant1 = Tenant.objects.create(name="租户1")
        self.tenant2 = Tenant.objects.create(name="租户2")

        self.user1_profile = UserProfile.objects.create(user=self.user, tenant=self.tenant1)

        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user2_profile = UserProfile.objects.create(user=self.user2, tenant=self.tenant2)

    def test_cross_tenant_access_denied(self):
        """测试跨租户访问被拒绝"""
        self.login_user()  # 登录租户1的用户

        # 尝试访问租户2的资源
        with patch("grading.views.validate_file_path", return_value=True):
            with patch("grading.views.get_user_tenant", return_value=self.tenant2):
                response = self.client.post(
                    reverse("grading:get_file_content"), {"file_path": "tenant2_file.txt"}
                )

                # 应该被拒绝访问
                self.assertIn(response.status_code, [403, 404])

    def test_tenant_admin_permissions(self):
        """测试租户管理员权限"""
        # 设置用户为租户管理员
        self.user1_profile.is_tenant_admin = True
        self.user1_profile.save()

        self.login_user()

        # 租户管理员应该能访问管理功能
        response = self.client.get(reverse("grading:grade_type_management"))
        self.assertResponseOK(response)


class BatchGradeToRegistryFallbackTest(BaseTestCase):
    """批量登分目录解析回退逻辑测试"""

    def setUp(self):
        super().setUp()
        self.semester = Semester.objects.create(
            name="2024年春季学期", start_date="2024-02-26", end_date="2024-06-30"
        )
        self.course = Course.objects.create(
            semester=self.semester,
            teacher=self.user,
            name="Python程序设计",
            course_type="theory",
            description="",
            location="A101",
            class_name="计科1班",
        )
        self.homework = Homework.objects.create(
            course=self.course, title="第一次作业", folder_name="第一次作业"
        )
        self.repository = Repository.objects.create(
            owner=self.user, name="测试仓库", path="repo", is_active=True
        )

    @patch("grading.views.GradeRegistryWriterService")
    def test_batch_grade_uses_fallback_directory(self, mock_service):
        """当目录结构不匹配时，应该通过回退搜索找到作业目录"""
        mock_instance = mock_service.return_value
        mock_instance.process_grading_system_scenario.return_value = {
            "success": True,
            "homework_number": 1,
            "statistics": {"total": 1, "success": 1, "failed": 0, "skipped": 0},
            "processed_files": [],
            "failed_files": [],
            "skipped_files": [],
            "registry_path": "/tmp/registry.xlsx",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            class_dir = os.path.join(temp_dir, "任意目录")
            homework_dir = os.path.join(class_dir, self.homework.folder_name)
            os.makedirs(homework_dir)

            self.login_user(self.user)
            with patch.object(Repository, "get_full_path", return_value=temp_dir):
                response = self.client.post(
                    reverse("grading:batch_grade_to_registry", args=[self.homework.id])
                )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        mock_instance.process_grading_system_scenario.assert_called_once()
        called_kwargs = mock_instance.process_grading_system_scenario.call_args.kwargs
        self.assertEqual(called_kwargs["homework_dir"], homework_dir)
        self.assertEqual(called_kwargs["class_dir"], class_dir)

    @patch("grading.views.GradeRegistryWriterService")
    def test_batch_grade_multiple_fallback_matches(self, mock_service):
        """存在多个同名目录时应返回冲突错误"""
        with tempfile.TemporaryDirectory() as temp_dir:
            class_a = os.path.join(temp_dir, "A班", self.homework.folder_name)
            class_b = os.path.join(temp_dir, "B班", self.homework.folder_name)
            os.makedirs(class_a)
            os.makedirs(class_b)

            self.login_user(self.user)
            with patch.object(Repository, "get_full_path", return_value=temp_dir):
                response = self.client.post(
                    reverse("grading:batch_grade_to_registry", args=[self.homework.id])
                )

        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("多个同名作业目录", data["message"])
        mock_service.return_value.process_grading_system_scenario.assert_not_called()

    @patch("grading.views.GradeRegistryWriterService")
    def test_batch_grade_manual_relative_path_resolves_conflict(self, mock_service):
        """用户选择具体目录时，应优先使用该路径避免同名冲突"""
        mock_instance = mock_service.return_value
        mock_instance.process_grading_system_scenario.return_value = {
            "success": True,
            "homework_number": 1,
            "statistics": {"total": 1, "success": 1, "failed": 0, "skipped": 0},
            "processed_files": [],
            "failed_files": [],
            "skipped_files": [],
            "registry_path": "/tmp/registry.xlsx",
        }

        # 模拟课程未配置班级名称的场景
        self.course.class_name = ""
        self.course.save(update_fields=["class_name"])

        with tempfile.TemporaryDirectory() as temp_dir:
            course_root = os.path.join(temp_dir, self.course.name)
            class_a_dir = os.path.join(course_root, "A班")
            class_b_dir = os.path.join(course_root, "B班")
            homework_dir_a = os.path.join(class_a_dir, self.homework.folder_name)
            homework_dir_b = os.path.join(class_b_dir, self.homework.folder_name)
            os.makedirs(homework_dir_a)
            os.makedirs(homework_dir_b)

            relative_path = f"{self.course.name}/A班/{self.homework.folder_name}"

            self.login_user(self.user)
            with patch.object(Repository, "get_full_path", return_value=temp_dir):
                response = self.client.post(
                    reverse("grading:batch_grade_to_registry", args=[self.homework.id]),
                    {"relative_path": relative_path},
                )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["class_name"], "A班")

        mock_instance.process_grading_system_scenario.assert_called_once()
        called_kwargs = mock_instance.process_grading_system_scenario.call_args.kwargs
        self.assertEqual(called_kwargs["homework_dir"], homework_dir_a)
        self.assertEqual(called_kwargs["class_dir"], class_a_dir)
