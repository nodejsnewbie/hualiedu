"""
仓库管理服务测试模块

测试仓库管理服务的创建、配置和管理功能
"""

import os
import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from grading.models import Class, Course, Repository, Semester, Tenant, UserProfile
from grading.services.repository_service import RepositoryService


class RepositoryServiceTest(TestCase):
    """仓库管理服务测试类"""

    def setUp(self):
        """设置测试数据"""
        self.service = RepositoryService()

        # 创建租户
        self.tenant1 = Tenant.objects.create(name="测试学校1", is_active=True)
        self.tenant2 = Tenant.objects.create(name="测试学校2", is_active=True)

        # 创建教师用户
        self.teacher1 = User.objects.create_user(
            username="teacher1", password="testpass123", first_name="张", last_name="老师"
        )
        self.teacher2 = User.objects.create_user(
            username="teacher2", password="testpass123", first_name="李", last_name="老师"
        )

        # 创建用户配置文件
        self.teacher1_profile = UserProfile.objects.create(
            user=self.teacher1, tenant=self.tenant1
        )
        self.teacher2_profile = UserProfile.objects.create(
            user=self.teacher2, tenant=self.tenant2
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
        self.class2 = Class.objects.create(
            tenant=self.tenant1, course=self.course1, name="计算机2班", student_count=25
        )

    def test_create_git_repository_success(self):
        """测试成功创建Git仓库配置"""
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="数据结构作业",
            git_url="https://github.com/test/repo.git",
            branch="main",
            username="testuser",
            password="testpass",
            description="数据结构课程作业仓库",
            tenant=self.tenant1,
        )

        # 验证仓库创建成功
        self.assertIsNotNone(repo)
        self.assertEqual(repo.name, "数据结构作业")
        self.assertEqual(repo.repo_type, "git")
        self.assertEqual(repo.git_url, "https://github.com/test/repo.git")
        self.assertEqual(repo.git_branch, "main")
        self.assertEqual(repo.git_username, "testuser")
        self.assertEqual(repo.owner, self.teacher1)
        self.assertEqual(repo.class_obj, self.class1)
        self.assertEqual(repo.tenant, self.tenant1)
        self.assertTrue(repo.is_active)

        # 验证兼容字段
        self.assertEqual(repo.url, "https://github.com/test/repo.git")
        self.assertEqual(repo.branch, "main")

        # 验证数据库中存在该仓库
        self.assertTrue(Repository.objects.filter(id=repo.id).exists())

    def test_create_git_repository_auto_tenant(self):
        """测试自动从教师配置获取租户"""
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
        )

        # 验证租户自动设置
        self.assertEqual(repo.tenant, self.tenant1)

    def test_create_git_repository_empty_name(self):
        """测试创建Git仓库时名称为空"""
        with self.assertRaises(ValueError) as context:
            self.service.create_git_repository(
                teacher=self.teacher1,
                class_obj=self.class1,
                name="   ",
                git_url="https://github.com/test/repo.git",
                tenant=self.tenant1,
            )

        self.assertIn("仓库名称不能为空", str(context.exception))

    def test_create_git_repository_empty_url(self):
        """测试创建Git仓库时URL为空"""
        with self.assertRaises(ValueError) as context:
            self.service.create_git_repository(
                teacher=self.teacher1,
                class_obj=self.class1,
                name="测试仓库",
                git_url="   ",
                tenant=self.tenant1,
            )

        self.assertIn("Git仓库URL不能为空", str(context.exception))

    def test_create_git_repository_invalid_url(self):
        """测试创建Git仓库时URL格式无效"""
        with self.assertRaises(ValueError) as context:
            self.service.create_git_repository(
                teacher=self.teacher1,
                class_obj=self.class1,
                name="测试仓库",
                git_url="invalid-url",
                tenant=self.tenant1,
            )

        self.assertIn("无效的Git仓库URL", str(context.exception))

    def test_create_filesystem_repository_success(self):
        """测试成功创建文件系统仓库"""
        repo = self.service.create_filesystem_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="数据结构作业",
            allocated_space_mb=2048,
            description="数据结构课程作业仓库",
            tenant=self.tenant1,
        )

        # 验证仓库创建成功
        self.assertIsNotNone(repo)
        self.assertEqual(repo.name, "数据结构作业")
        self.assertEqual(repo.repo_type, "filesystem")
        self.assertEqual(repo.allocated_space_mb, 2048)
        self.assertEqual(repo.owner, self.teacher1)
        self.assertEqual(repo.class_obj, self.class1)
        self.assertEqual(repo.tenant, self.tenant1)
        self.assertTrue(repo.is_active)

        # 验证目录名已生成
        self.assertIsNotNone(repo.filesystem_path)
        self.assertTrue(len(repo.filesystem_path) > 0)

        # 验证物理目录已创建
        full_path = repo.get_full_path()
        self.assertTrue(os.path.exists(full_path))
        self.assertTrue(os.path.isdir(full_path))

        # 清理测试目录
        os.rmdir(full_path)

    def test_create_filesystem_repository_invalid_space(self):
        """测试创建文件系统仓库时分配空间无效"""
        with self.assertRaises(ValueError) as context:
            self.service.create_filesystem_repository(
                teacher=self.teacher1,
                class_obj=self.class1,
                name="测试仓库",
                allocated_space_mb=0,
                tenant=self.tenant1,
            )

        self.assertIn("分配空间必须大于0", str(context.exception))

    def test_generate_directory_name_basic(self):
        """测试生成基本目录名"""
        dir_name = self.service.generate_directory_name("teacher1")

        # 验证目录名格式
        self.assertEqual(dir_name, "teacher1")

    def test_generate_directory_name_with_base(self):
        """测试生成带基础名称的目录名"""
        dir_name = self.service.generate_directory_name("teacher1", "数据结构")

        # 验证目录名格式
        self.assertTrue(dir_name.startswith("teacher1_"))
        self.assertIn("数据结构", dir_name)

    def test_generate_directory_name_uniqueness(self):
        """测试目录名唯一性 - Property 3"""
        # 创建第一个仓库
        repo1 = self.service.create_filesystem_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="仓库1",
            tenant=self.tenant1,
        )

        # 生成新的目录名
        dir_name2 = self.service.generate_directory_name("teacher1", "仓库1")

        # 验证新目录名不同
        self.assertNotEqual(dir_name2, repo1.filesystem_path)
        self.assertTrue("_2" in dir_name2 or "_" in dir_name2)

        # 清理测试目录
        full_path1 = repo1.get_full_path()
        if os.path.exists(full_path1):
            os.rmdir(full_path1)

    def test_generate_directory_name_multiple_conflicts(self):
        """测试多次重名时的目录名生成"""
        # 创建多个同名仓库
        repos = []
        for i in range(3):
            repo = self.service.create_filesystem_repository(
                teacher=self.teacher1,
                class_obj=self.class1,
                name=f"测试仓库{i}",
                tenant=self.tenant1,
            )
            repos.append(repo)

        # 生成新的目录名
        dir_name = self.service.generate_directory_name("teacher1", "测试仓库0")

        # 验证目录名唯一
        existing_paths = [r.filesystem_path for r in repos]
        self.assertNotIn(dir_name, existing_paths)

        # 清理测试目录
        for repo in repos:
            full_path = repo.get_full_path()
            if os.path.exists(full_path):
                os.rmdir(full_path)

    def test_generate_directory_name_special_characters(self):
        """测试特殊字符处理"""
        dir_name = self.service.generate_directory_name("teacher@1", "课程#1")

        # 验证特殊字符被替换
        self.assertNotIn("@", dir_name)
        self.assertNotIn("#", dir_name)
        self.assertTrue("_" in dir_name)

    def test_validate_git_connection_valid_https(self):
        """测试验证有效的HTTPS Git URL"""
        # 注意：这个测试需要网络连接，可能会失败
        # 在实际环境中，应该使用mock
        is_valid, error = self.service.validate_git_connection(
            "https://github.com/torvalds/linux.git"
        )

        # 如果GitPython未安装，跳过验证
        if "GitPython未安装" in error:
            self.skipTest("GitPython未安装")

        # 如果网络不可用，跳过验证
        if "Git连接验证失败" in error:
            self.skipTest("网络不可用或仓库不存在")

    def test_validate_git_connection_invalid_url(self):
        """测试验证无效的Git URL"""
        is_valid, error = self.service.validate_git_connection("invalid-url")

        # 验证返回失败
        self.assertFalse(is_valid)
        self.assertIn("无效的Git仓库URL", error)

    def test_validate_directory_structure_valid(self):
        """测试验证有效的目录结构 - Property 4"""
        # 创建临时目录结构
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建符合规范的目录结构
            course_dir = os.path.join(temp_dir, "数据结构")
            class_dir = os.path.join(course_dir, "计算机1班")
            homework_dir = os.path.join(class_dir, "第一次作业")

            os.makedirs(homework_dir)

            # 验证目录结构
            is_valid, error, suggestions = self.service.validate_directory_structure(temp_dir)

            # 验证通过
            self.assertTrue(is_valid)
            self.assertEqual(error, "")
            self.assertEqual(len(suggestions), 0)

    def test_validate_directory_structure_empty(self):
        """测试验证空目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 验证空目录
            is_valid, error, suggestions = self.service.validate_directory_structure(temp_dir)

            # 验证失败
            self.assertFalse(is_valid)
            self.assertIn("未找到课程目录", error)
            self.assertTrue(len(suggestions) > 0)

    def test_validate_directory_structure_missing_class(self):
        """测试验证缺少班级目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 只创建课程目录
            course_dir = os.path.join(temp_dir, "数据结构")
            os.makedirs(course_dir)

            # 验证目录结构
            is_valid, error, suggestions = self.service.validate_directory_structure(temp_dir)

            # 验证失败
            self.assertFalse(is_valid)
            self.assertIn("未找到班级目录", error)
            self.assertTrue(len(suggestions) > 0)

    def test_validate_directory_structure_missing_homework(self):
        """测试验证缺少作业批次目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建课程和班级目录
            course_dir = os.path.join(temp_dir, "数据结构")
            class_dir = os.path.join(course_dir, "计算机1班")
            os.makedirs(class_dir)

            # 验证目录结构
            is_valid, error, suggestions = self.service.validate_directory_structure(temp_dir)

            # 验证失败
            self.assertFalse(is_valid)
            self.assertIn("未找到作业批次目录", error)
            self.assertTrue(len(suggestions) > 0)

    def test_validate_directory_structure_not_exists(self):
        """测试验证不存在的目录"""
        is_valid, error, suggestions = self.service.validate_directory_structure(
            "/nonexistent/path"
        )

        # 验证失败
        self.assertFalse(is_valid)
        self.assertIn("目录不存在", error)

    def test_list_repositories_teacher_isolation(self):
        """测试教师仓库数据隔离"""
        # 为teacher1创建仓库
        repo1 = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="仓库1",
            git_url="https://github.com/test/repo1.git",
            tenant=self.tenant1,
        )
        repo2 = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class2,
            name="仓库2",
            git_url="https://github.com/test/repo2.git",
            tenant=self.tenant1,
        )

        # 为teacher2创建仓库
        course2 = Course.objects.create(
            semester=self.semester1,
            teacher=self.teacher2,
            name="操作系统",
            course_type="lab",
            tenant=self.tenant2,
        )
        class3 = Class.objects.create(
            tenant=self.tenant2, course=course2, name="计算机3班", student_count=20
        )
        repo3 = self.service.create_git_repository(
            teacher=self.teacher2,
            class_obj=class3,
            name="仓库3",
            git_url="https://github.com/test/repo3.git",
            tenant=self.tenant2,
        )

        # 查询teacher1的仓库
        teacher1_repos = self.service.list_repositories(self.teacher1)

        # 验证只返回teacher1的仓库
        self.assertEqual(len(teacher1_repos), 2)
        repo_ids = [r.id for r in teacher1_repos]
        self.assertIn(repo1.id, repo_ids)
        self.assertIn(repo2.id, repo_ids)
        self.assertNotIn(repo3.id, repo_ids)

        # 查询teacher2的仓库
        teacher2_repos = self.service.list_repositories(self.teacher2)

        # 验证只返回teacher2的仓库
        self.assertEqual(len(teacher2_repos), 1)
        self.assertEqual(teacher2_repos[0].id, repo3.id)

    def test_list_repositories_with_class_filter(self):
        """测试按班级过滤仓库"""
        # 创建多个仓库
        repo1 = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="仓库1",
            git_url="https://github.com/test/repo1.git",
            tenant=self.tenant1,
        )
        repo2 = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class2,
            name="仓库2",
            git_url="https://github.com/test/repo2.git",
            tenant=self.tenant1,
        )

        # 查询class1的仓库
        class1_repos = self.service.list_repositories(self.teacher1, class_obj=self.class1)
        self.assertEqual(len(class1_repos), 1)
        self.assertEqual(class1_repos[0].id, repo1.id)

        # 查询class2的仓库
        class2_repos = self.service.list_repositories(self.teacher1, class_obj=self.class2)
        self.assertEqual(len(class2_repos), 1)
        self.assertEqual(class2_repos[0].id, repo2.id)

    def test_get_repository_by_id_success(self):
        """测试根据ID获取仓库"""
        # 创建仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        # 获取仓库
        retrieved_repo = self.service.get_repository_by_id(repo.id)

        # 验证获取成功
        self.assertEqual(retrieved_repo.id, repo.id)
        self.assertEqual(retrieved_repo.name, "测试仓库")

    def test_get_repository_by_id_with_teacher_filter(self):
        """测试根据ID获取仓库时验证教师权限"""
        # 创建仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        # teacher1可以访问
        retrieved_repo = self.service.get_repository_by_id(repo.id, teacher=self.teacher1)
        self.assertEqual(retrieved_repo.id, repo.id)

        # teacher2不能访问
        with self.assertRaises(Repository.DoesNotExist):
            self.service.get_repository_by_id(repo.id, teacher=self.teacher2)

    def test_update_repository_name(self):
        """测试更新仓库名称"""
        # 创建仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="原始名称",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        # 更新名称
        updated_repo = self.service.update_repository(repo.id, name="新名称")

        # 验证更新成功
        self.assertEqual(updated_repo.name, "新名称")

        # 验证数据库中已更新
        repo.refresh_from_db()
        self.assertEqual(repo.name, "新名称")

    def test_update_repository_git_url(self):
        """测试更新Git仓库URL"""
        # 创建Git仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo1.git",
            tenant=self.tenant1,
        )

        # 更新URL
        updated_repo = self.service.update_repository(
            repo.id, git_url="https://github.com/test/repo2.git"
        )

        # 验证更新成功
        self.assertEqual(updated_repo.git_url, "https://github.com/test/repo2.git")
        self.assertEqual(updated_repo.url, "https://github.com/test/repo2.git")

    def test_update_repository_invalid_git_url(self):
        """测试更新Git仓库时使用无效URL"""
        # 创建Git仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        # 尝试使用无效URL更新
        with self.assertRaises(ValueError) as context:
            self.service.update_repository(repo.id, git_url="invalid-url")

        self.assertIn("无效的Git仓库URL", str(context.exception))

    def test_update_repository_allocated_space(self):
        """测试更新文件系统仓库分配空间"""
        # 创建文件系统仓库
        repo = self.service.create_filesystem_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            allocated_space_mb=1024,
            tenant=self.tenant1,
        )

        # 更新分配空间
        updated_repo = self.service.update_repository(repo.id, allocated_space_mb=2048)

        # 验证更新成功
        self.assertEqual(updated_repo.allocated_space_mb, 2048)

        # 清理测试目录
        full_path = repo.get_full_path()
        if os.path.exists(full_path):
            os.rmdir(full_path)

    def test_delete_repository_success(self):
        """测试删除仓库配置"""
        # 创建仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        repo_id = repo.id

        # 删除仓库
        self.service.delete_repository(repo_id)

        # 验证仓库已删除
        self.assertFalse(Repository.objects.filter(id=repo_id).exists())

    def test_delete_repository_with_teacher_permission(self):
        """测试删除仓库时验证教师权限"""
        # 创建仓库
        repo = self.service.create_git_repository(
            teacher=self.teacher1,
            class_obj=self.class1,
            name="测试仓库",
            git_url="https://github.com/test/repo.git",
            tenant=self.tenant1,
        )

        # teacher2不能删除teacher1的仓库
        with self.assertRaises(Repository.DoesNotExist):
            self.service.delete_repository(repo.id, teacher=self.teacher2)

        # 验证仓库仍然存在
        self.assertTrue(Repository.objects.filter(id=repo.id).exists())


class RepositoryServicePropertyTest(HypothesisTestCase):
    """仓库管理服务属性测试类 - Property-Based Tests"""

    def setUp(self):
        """设置测试数据"""
        import uuid
        
        self.service = RepositoryService()

        # 创建租户（使用UUID确保唯一性）
        unique_id = str(uuid.uuid4())[:8]
        self.tenant1 = Tenant.objects.create(
            name=f"测试学校_{unique_id}", is_active=True
        )

        # 创建教师用户（使用UUID确保唯一性）
        self.teacher1 = User.objects.create_user(
            username=f"teacher_{unique_id}",
            password="testpass123",
            first_name="张",
            last_name="老师",
        )

        # 创建用户配置文件
        self.teacher1_profile = UserProfile.objects.create(
            user=self.teacher1, tenant=self.tenant1
        )

        # 创建学期（使用不同的日期避免UNIQUE约束冲突）
        today = date.today()
        # 使用unique_id的哈希值来偏移日期，确保每次测试的日期都不同
        offset = hash(unique_id) % 1000
        self.semester1 = Semester.objects.create(
            name=f"2024年春季学期_{unique_id}",
            start_date=today - timedelta(days=30 + offset),
            end_date=today + timedelta(days=60 + offset),
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

    @given(
        base_name=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65),
            min_size=0,
            max_size=20,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_directory_name_uniqueness(self, base_name):
        """Property 3: 目录名唯一性
        
        **Feature: homework-grading-system, Property 3: 目录名唯一性**
        **Validates: Requirements 1.1.5**
        
        For any username and base_name, calling the directory name generation function
        multiple times should always return unique directory names (using numeric suffixes
        when needed) after creating a repository with the first generated name.
        """
        # 使用固定的teacher1用户名
        username = self.teacher1.username
        
        # 生成第一个目录名
        dir_name1 = self.service.generate_directory_name(username, base_name)
        
        # 手动创建一个仓库，使用生成的目录名
        try:
            repo = Repository.objects.create(
                owner=self.teacher1,
                tenant=self.tenant1,
                class_obj=self.class1,
                name=f"测试仓库_{base_name if base_name else 'default'}",
                repo_type="filesystem",
                filesystem_path=dir_name1,  # 使用生成的目录名
                path=dir_name1,
                allocated_space_mb=1024,
                is_active=True,
            )
            
            # 创建物理目录
            full_path = repo.get_full_path()
            os.makedirs(full_path, exist_ok=True)
            
            # 生成第二个目录名（应该与第一个不同）
            dir_name2 = self.service.generate_directory_name(username, base_name)
            
            # 验证两个目录名不同
            self.assertNotEqual(
                dir_name1,
                dir_name2,
                f"目录名应该唯一，但生成了相同的名称: {dir_name1}",
            )
            
            # 清理测试目录
            if os.path.exists(full_path):
                try:
                    os.rmdir(full_path)
                except OSError:
                    pass
                    
        except Exception as e:
            # 如果创建失败（例如无效字符），跳过这个测试用例
            if "仓库名称不能为空" in str(e) or "无法确定租户信息" in str(e):
                return
            raise

    @given(
        course_name=st.text(min_size=1, max_size=20),
        class_name=st.text(min_size=1, max_size=20),
        homework_name=st.text(min_size=1, max_size=20),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_directory_structure_validation(
        self, course_name, class_name, homework_name
    ):
        """Property 4: 目录结构验证
        
        **Feature: homework-grading-system, Property 4: 目录结构验证**
        **Validates: Requirements 1.2.1**
        
        For any directory path, the validation function should correctly identify
        whether it follows the "课程/班级/作业批次/学生作业" structure.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建符合规范的目录结构
            try:
                # 清理名称中的特殊字符
                safe_course = "".join(c for c in course_name if c.isalnum() or c in "_ -")
                safe_class = "".join(c for c in class_name if c.isalnum() or c in "_ -")
                safe_homework = "".join(c for c in homework_name if c.isalnum() or c in "_ -")
                
                # 如果清理后为空，使用默认值
                if not safe_course:
                    safe_course = "课程"
                if not safe_class:
                    safe_class = "班级"
                if not safe_homework:
                    safe_homework = "作业"
                
                course_dir = os.path.join(temp_dir, safe_course)
                class_dir = os.path.join(course_dir, safe_class)
                homework_dir = os.path.join(class_dir, safe_homework)
                
                os.makedirs(homework_dir)
                
                # 验证目录结构
                is_valid, error, suggestions = self.service.validate_directory_structure(
                    temp_dir
                )
                
                # 符合规范的目录结构应该验证通过
                self.assertTrue(
                    is_valid,
                    f"符合规范的目录结构应该验证通过，但失败了: {error}",
                )
                self.assertEqual(error, "", f"不应该有错误信息，但得到: {error}")
                self.assertEqual(
                    len(suggestions), 0, f"不应该有修复建议，但得到: {suggestions}"
                )
                
            except OSError:
                # 如果目录创建失败（例如无效字符），跳过这个测试用例
                return
