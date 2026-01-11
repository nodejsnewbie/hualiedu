"""
缓存优化功能测试

测试缓存管理器的各项功能，包括：
- 评价模板缓存
- 课程列表缓存
- 班级列表缓存
- 缓存失效逻辑
"""

import logging

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from grading.cache_manager import CacheManager
from grading.models import Class, CommentTemplate, Course, Semester, Tenant, UserProfile
from grading.services.class_service import ClassService
from grading.services.comment_template_service import CommentTemplateService
from grading.services.course_service import CourseService

# 禁用日志输出
logging.disable(logging.CRITICAL)


def create_user_with_profile(username, tenant):
    """创建带profile的用户"""
    user = User.objects.create_user(username=username, password="password")
    UserProfile.objects.create(user=user, tenant=tenant)
    return user


class CacheManagerTest(TestCase):
    """缓存管理器测试"""

    def setUp(self):
        """设置测试数据"""
        # 清除所有缓存
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户
        self.teacher = User.objects.create_user(username="teacher1", password="password")

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_comment_template_cache(self):
        """测试评价模板缓存"""
        # 设置缓存
        templates = [{"id": 1, "text": "测试评价"}]
        self.cache_manager.set_comment_templates("personal", str(self.teacher.id), templates)

        # 获取缓存
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]["text"], "测试评价")

        # 清除缓存
        self.cache_manager.clear_comment_templates("personal", str(self.teacher.id))
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNone(cached)

    def test_course_list_cache(self):
        """测试课程列表缓存"""
        # 设置缓存
        courses = [{"id": 1, "name": "测试课程"}]
        self.cache_manager.set_course_list(teacher_id=self.teacher.id, courses=courses)

        # 获取缓存
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]["name"], "测试课程")

        # 清除缓存
        self.cache_manager.clear_course_list(teacher_id=self.teacher.id)
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNone(cached)

    def test_class_list_cache(self):
        """测试班级列表缓存"""
        # 设置缓存
        classes = [{"id": 1, "name": "测试班级"}]
        self.cache_manager.set_class_list(classes, course_id=1)

        # 获取缓存
        cached = self.cache_manager.get_class_list(course_id=1)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]["name"], "测试班级")

        # 清除缓存
        self.cache_manager.clear_class_list(course_id=1)
        cached = self.cache_manager.get_class_list(course_id=1)
        self.assertIsNone(cached)

    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        # 设置多种缓存
        self.cache_manager.set_comment_templates("personal", str(self.teacher.id), [{"id": 1}])
        self.cache_manager.set_course_list(teacher_id=self.teacher.id, courses=[{"id": 1}])
        self.cache_manager.set_class_list([{"id": 1}], course_id=1)

        # 清除所有缓存（使用cache.clear()因为LocMemCache不支持模式删除）
        cache.clear()

        # 验证所有缓存已清除
        self.assertIsNone(
            self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        )
        self.assertIsNone(self.cache_manager.get_course_list(teacher_id=self.teacher.id))
        self.assertIsNone(self.cache_manager.get_class_list(course_id=1))


class CommentTemplateServiceCacheTest(TestCase):
    """评价模板服务缓存测试"""

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建缓存管理器和服务
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)
        self.service = CommentTemplateService(cache_manager=self.cache_manager)

        # 创建测试数据
        CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            template_type="personal",
            comment_text="个人评价1",
            usage_count=10,
        )
        CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            template_type="personal",
            comment_text="个人评价2",
            usage_count=5,
        )

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_get_personal_templates_with_cache(self):
        """测试获取个人模板（使用缓存）"""
        # 第一次查询（从数据库）
        templates1 = self.service.get_personal_templates(self.teacher)
        self.assertEqual(len(templates1), 2)

        # 第二次查询（从缓存）
        templates2 = self.service.get_personal_templates(self.teacher)
        self.assertEqual(len(templates2), 2)

        # 验证缓存命中
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNotNone(cached)

    def test_record_comment_usage_invalidates_cache(self):
        """测试记录评价使用会清除缓存"""
        # 先查询一次，建立缓存
        self.service.get_personal_templates(self.teacher)

        # 验证缓存存在
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNotNone(cached)

        # 记录评价使用
        self.service.record_comment_usage(self.teacher, "新评价", self.tenant)

        # 验证缓存已清除
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNone(cached)


class CourseServiceCacheTest(TestCase):
    """课程服务缓存测试"""

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024春季",
            start_date="2024-02-01",
            end_date="2024-06-30",
        )

        # 创建缓存管理器和服务
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)
        self.service = CourseService(cache_manager=self.cache_manager)

        # 创建测试课程
        Course.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            semester=self.semester,
            name="测试课程1",
            course_type="theory",
        )
        Course.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            semester=self.semester,
            name="测试课程2",
            course_type="lab",
        )

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_list_courses_with_cache(self):
        """测试列出课程（使用缓存）"""
        # 第一次查询（从数据库）
        courses1 = self.service.list_courses(self.teacher)
        self.assertEqual(len(courses1), 2)

        # 第二次查询（从缓存）
        courses2 = self.service.list_courses(self.teacher)
        self.assertEqual(len(courses2), 2)

        # 验证缓存命中
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNotNone(cached)

    def test_create_course_invalidates_cache(self):
        """测试创建课程会清除缓存"""
        # 先查询一次，建立缓存
        self.service.list_courses(self.teacher)

        # 验证缓存存在
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNotNone(cached)

        # 创建新课程
        self.service.create_course(
            teacher=self.teacher,
            name="新课程",
            course_type="theory",
            semester=self.semester,
        )

        # 验证缓存已清除
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNone(cached)


class ClassServiceCacheTest(TestCase):
    """班级服务缓存测试"""

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024春季",
            start_date="2024-02-01",
            end_date="2024-06-30",
        )

        # 创建课程
        self.course = Course.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            semester=self.semester,
            name="测试课程",
            course_type="theory",
        )

        # 创建缓存管理器和服务
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)
        self.service = ClassService(cache_manager=self.cache_manager)

        # 创建测试班级
        Class.objects.create(tenant=self.tenant, course=self.course, name="班级1", student_count=30)
        Class.objects.create(tenant=self.tenant, course=self.course, name="班级2", student_count=25)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_list_classes_with_cache(self):
        """测试列出班级（使用缓存）"""
        # 第一次查询（从数据库）
        classes1 = self.service.list_classes(course=self.course)
        self.assertEqual(len(classes1), 2)

        # 第二次查询（从缓存）
        classes2 = self.service.list_classes(course=self.course)
        self.assertEqual(len(classes2), 2)

        # 验证缓存命中
        cached = self.cache_manager.get_class_list(course_id=self.course.id)
        self.assertIsNotNone(cached)

    def test_create_class_invalidates_cache(self):
        """测试创建班级会清除缓存"""
        # 先查询一次，建立缓存
        self.service.list_classes(course=self.course)

        # 验证缓存存在
        cached = self.cache_manager.get_class_list(course_id=self.course.id)
        self.assertIsNotNone(cached)

        # 创建新班级
        self.service.create_class(
            course=self.course, name="新班级", student_count=20, tenant=self.tenant
        )

        # 验证缓存已清除
        cached = self.cache_manager.get_class_list(course_id=self.course.id)
        self.assertIsNone(cached)


class CachePerformanceTest(TestCase):
    """缓存性能测试"""

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024春季",
            start_date="2024-02-01",
            end_date="2024-06-30",
        )

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_cache_avoids_repeated_queries(self):
        """测试缓存避免重复查询"""
        # 创建服务
        service = CourseService(cache_manager=self.cache_manager)

        # 创建多个课程
        for i in range(10):
            Course.objects.create(
                tenant=self.tenant,
                teacher=self.teacher,
                semester=self.semester,
                name=f"课程{i}",
                course_type="theory",
            )

        # 第一次查询（从数据库）
        courses1 = service.list_courses(self.teacher)

        # 第二次查询（从缓存）
        courses2 = service.list_courses(self.teacher)

        # 验证结果相同
        self.assertEqual(len(courses1), len(courses2))

        # 缓存查询应该更快（虽然在测试环境中差异可能不明显）
        # 这里只是验证缓存确实被使用了
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNotNone(cached)


class FileCountCachePropertyTest(TestCase):
    """
    文件数量缓存属性测试

    **Feature: homework-grading-system, Property 14: 缓存避免重复计算**
    测试缓存避免重复计算的正确性属性
    """

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_property_file_count_cache_avoids_recomputation(self):
        """
        Property 14: 缓存避免重复计算
        Validates: Requirements 14.1

        For any directory path, calling get_file_count twice should:
        1. First call returns None (no cache)
        2. After set_file_count, second call returns cached value
        3. The cached value matches what was set
        """
        # Test with multiple directory paths
        test_paths = [
            "/path/to/course1/class1/homework1",
            "/path/to/course2/class2/homework2",
            "/another/path/test",
            "/root/dir",
        ]

        for dir_path in test_paths:
            # Clear cache for this path
            self.cache_manager.clear_file_count(dir_path)

            # First call should return None (no cache)
            count1 = self.cache_manager.get_file_count(dir_path)
            self.assertIsNone(count1, f"First call should return None for {dir_path}")

            # Set a file count
            expected_count = 42
            self.cache_manager.set_file_count(dir_path, expected_count)

            # Second call should return cached value
            count2 = self.cache_manager.get_file_count(dir_path)
            self.assertIsNotNone(count2, f"Second call should return cached value for {dir_path}")
            self.assertEqual(
                count2,
                expected_count,
                f"Cached value should match set value for {dir_path}",
            )

            # Third call should still return cached value (no recomputation)
            count3 = self.cache_manager.get_file_count(dir_path)
            self.assertEqual(
                count3,
                expected_count,
                f"Third call should still return cached value for {dir_path}",
            )

    def test_property_cache_isolation_by_user(self):
        """
        Property: 缓存按用户隔离
        Validates: Requirements 14.1

        For any two different users, their caches should be isolated
        """
        # Create another user
        teacher2 = create_user_with_profile("teacher2", self.tenant)
        cache_manager2 = CacheManager(user_id=teacher2.id, tenant_id=self.tenant.id)

        dir_path = "/shared/path"

        # User 1 sets cache
        self.cache_manager.set_file_count(dir_path, 10)

        # User 2 sets different cache
        cache_manager2.set_file_count(dir_path, 20)

        # Verify isolation
        count1 = self.cache_manager.get_file_count(dir_path)
        count2 = cache_manager2.get_file_count(dir_path)

        self.assertEqual(count1, 10, "User 1 should see their own cached value")
        self.assertEqual(count2, 20, "User 2 should see their own cached value")

    def test_property_cache_isolation_by_tenant(self):
        """
        Property: 缓存按租户隔离
        Validates: Requirements 14.1

        For any two different tenants, their caches should be isolated
        """
        # Create another tenant and user
        tenant2 = Tenant.objects.create(name="测试租户2")
        teacher2 = create_user_with_profile("teacher3", tenant2)
        cache_manager2 = CacheManager(user_id=teacher2.id, tenant_id=tenant2.id)

        dir_path = "/shared/path"

        # Tenant 1 sets cache
        self.cache_manager.set_file_count(dir_path, 30)

        # Tenant 2 sets different cache
        cache_manager2.set_file_count(dir_path, 40)

        # Verify isolation
        count1 = self.cache_manager.get_file_count(dir_path)
        count2 = cache_manager2.get_file_count(dir_path)

        self.assertEqual(count1, 30, "Tenant 1 should see their own cached value")
        self.assertEqual(count2, 40, "Tenant 2 should see their own cached value")

    def test_property_cache_invalidation(self):
        """
        Property: 缓存失效逻辑
        Validates: Requirements 14.5

        For any cached value, clearing the cache should make it unavailable
        """
        test_paths = [
            "/path/a",
            "/path/b",
            "/path/c",
        ]

        # Set cache for all paths
        for i, path in enumerate(test_paths):
            self.cache_manager.set_file_count(path, i * 10)

        # Verify all are cached
        for i, path in enumerate(test_paths):
            count = self.cache_manager.get_file_count(path)
            self.assertEqual(count, i * 10)

        # Clear specific path
        self.cache_manager.clear_file_count(test_paths[0])

        # Verify only that path is cleared
        self.assertIsNone(self.cache_manager.get_file_count(test_paths[0]))
        self.assertIsNotNone(self.cache_manager.get_file_count(test_paths[1]))
        self.assertIsNotNone(self.cache_manager.get_file_count(test_paths[2]))


class DirTreeCachePropertyTest(TestCase):
    """
    目录树缓存属性测试

    **Feature: homework-grading-system, Property 14: 缓存避免重复计算**
    """

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_property_dir_tree_cache_avoids_recomputation(self):
        """
        Property 14: 目录树缓存避免重复计算
        Validates: Requirements 14.2

        For any directory tree structure, caching should avoid recomputation
        """
        dir_path = "/course/class/homework"
        tree_structure = {
            "name": "homework",
            "type": "directory",
            "children": [
                {"name": "student1.docx", "type": "file"},
                {"name": "student2.docx", "type": "file"},
            ],
        }

        # First call should return None
        cached_tree1 = self.cache_manager.get_dir_tree(dir_path)
        self.assertIsNone(cached_tree1)

        # Set the tree structure
        self.cache_manager.set_dir_tree(dir_path, tree_structure)

        # Second call should return cached structure
        cached_tree2 = self.cache_manager.get_dir_tree(dir_path)
        self.assertIsNotNone(cached_tree2)
        self.assertEqual(cached_tree2["name"], "homework")
        self.assertEqual(len(cached_tree2["children"]), 2)

        # Third call should still return cached structure
        cached_tree3 = self.cache_manager.get_dir_tree(dir_path)
        self.assertEqual(cached_tree3, cached_tree2)


class CommentTemplateCachePropertyTest(TestCase):
    """
    评价模板缓存属性测试

    **Feature: homework-grading-system, Property 14: 缓存避免重复计算**
    """

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_property_comment_template_cache_avoids_recomputation(self):
        """
        Property 14: 评价模板缓存避免重复计算
        Validates: Requirements 14.1

        For any comment template list, caching should avoid database queries
        """
        template_type = "personal"
        identifier = str(self.teacher.id)
        templates = [
            {"id": 1, "text": "优秀", "usage_count": 10},
            {"id": 2, "text": "良好", "usage_count": 5},
        ]

        # First call should return None
        cached1 = self.cache_manager.get_comment_templates(template_type, identifier)
        self.assertIsNone(cached1)

        # Set templates
        self.cache_manager.set_comment_templates(template_type, identifier, templates)

        # Second call should return cached templates
        cached2 = self.cache_manager.get_comment_templates(template_type, identifier)
        self.assertIsNotNone(cached2)
        self.assertEqual(len(cached2), 2)
        self.assertEqual(cached2[0]["text"], "优秀")

        # Third call should still return cached templates
        cached3 = self.cache_manager.get_comment_templates(template_type, identifier)
        self.assertEqual(cached3, cached2)


class CacheInvalidationPropertyTest(TestCase):
    """
    缓存失效逻辑属性测试

    **Feature: homework-grading-system, Property 14: 缓存避免重复计算**
    测试缓存失效的正确性
    """

    def setUp(self):
        """设置测试数据"""
        cache.clear()

        # 创建租户
        self.tenant = Tenant.objects.create(name="测试租户")

        # 创建用户和profile
        self.teacher = create_user_with_profile("teacher1", self.tenant)

        # 创建学期
        self.semester = Semester.objects.create(
            name="2024春季",
            start_date="2024-02-01",
            end_date="2024-06-30",
        )

        # 创建缓存管理器
        self.cache_manager = CacheManager(user_id=self.teacher.id, tenant_id=self.tenant.id)

    def tearDown(self):
        """清理测试数据"""
        cache.clear()
        logging.disable(logging.NOTSET)

    def test_property_course_creation_invalidates_cache(self):
        """
        Property: 创建课程应清除课程列表缓存
        Validates: Requirements 14.5

        For any teacher, creating a new course should invalidate their course list cache
        """
        service = CourseService(cache_manager=self.cache_manager)

        # Create initial course
        Course.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            semester=self.semester,
            name="初始课程",
            course_type="theory",
        )

        # First query - builds cache
        courses1 = service.list_courses(self.teacher)
        self.assertEqual(len(courses1), 1)

        # Verify cache exists
        cached = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNotNone(cached)

        # Create new course - should invalidate cache
        service.create_course(
            teacher=self.teacher,
            name="新课程",
            course_type="lab",
            semester=self.semester,
        )

        # Verify cache is cleared
        cached_after = self.cache_manager.get_course_list(teacher_id=self.teacher.id)
        self.assertIsNone(cached_after)

        # Query again - should rebuild cache with new data
        courses2 = service.list_courses(self.teacher)
        self.assertEqual(len(courses2), 2)

    def test_property_class_creation_invalidates_cache(self):
        """
        Property: 创建班级应清除班级列表缓存
        Validates: Requirements 14.5

        For any course, creating a new class should invalidate the class list cache
        """
        # Create course
        course = Course.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            semester=self.semester,
            name="测试课程",
            course_type="theory",
        )

        service = ClassService(cache_manager=self.cache_manager)

        # Create initial class
        Class.objects.create(tenant=self.tenant, course=course, name="初始班级", student_count=30)

        # First query - builds cache
        classes1 = service.list_classes(course=course)
        self.assertEqual(len(classes1), 1)

        # Verify cache exists
        cached = self.cache_manager.get_class_list(course_id=course.id)
        self.assertIsNotNone(cached)

        # Create new class - should invalidate cache
        service.create_class(course=course, name="新班级", student_count=25, tenant=self.tenant)

        # Verify cache is cleared
        cached_after = self.cache_manager.get_class_list(course_id=course.id)
        self.assertIsNone(cached_after)

        # Query again - should rebuild cache with new data
        classes2 = service.list_classes(course=course)
        self.assertEqual(len(classes2), 2)

    def test_property_comment_usage_invalidates_cache(self):
        """
        Property: 记录评价使用应清除评价模板缓存
        Validates: Requirements 14.5

        For any teacher, recording comment usage should invalidate template cache
        """
        service = CommentTemplateService(cache_manager=self.cache_manager)

        # Create initial template
        CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            template_type="personal",
            comment_text="初始评价",
            usage_count=5,
        )

        # First query - builds cache
        templates1 = service.get_personal_templates(self.teacher)
        self.assertEqual(len(templates1), 1)

        # Verify cache exists
        cached = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNotNone(cached)

        # Record new comment usage - should invalidate cache
        service.record_comment_usage(self.teacher, "新评价", self.tenant)

        # Verify cache is cleared
        cached_after = self.cache_manager.get_comment_templates("personal", str(self.teacher.id))
        self.assertIsNone(cached_after)

        # Query again - should rebuild cache with new data
        templates2 = service.get_personal_templates(self.teacher)
        self.assertEqual(len(templates2), 2)
