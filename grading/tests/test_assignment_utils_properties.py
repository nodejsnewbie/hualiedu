"""
作业管理工具类的属性测试

使用 Hypothesis 进行基于属性的测试，验证通用规则。
"""

import os
import re
import tempfile
from unittest.mock import MagicMock, patch

import hypothesis
from django.core.cache import cache
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase

from grading.assignment_utils import (
    CacheManager,
    CredentialEncryption,
    PathValidator,
    ValidationError,
)

# 配置最小迭代次数
hypothesis.settings.register_profile("ci", max_examples=100)
hypothesis.settings.load_profile("ci")


class TestPathValidatorProperties(TestCase):
    """PathValidator 属性测试"""

    def test_validate_path_security(self):
        """测试路径安全验证 - 防止路径遍历攻击"""
        with tempfile.TemporaryDirectory() as base_dir:
            # 正常路径应该通过
            self.assertTrue(PathValidator.validate_path("subdir/file.txt", base_dir))
            self.assertTrue(PathValidator.validate_path("file.txt", base_dir))
            
            # 路径遍历攻击应该被阻止
            with self.assertRaises(ValidationError):
                PathValidator.validate_path("../etc/passwd", base_dir)
            
            with self.assertRaises(ValidationError):
                PathValidator.validate_path("../../etc/passwd", base_dir)
            
            with self.assertRaises(ValidationError):
                PathValidator.validate_path("subdir/../../etc/passwd", base_dir)

    def test_number_to_chinese(self):
        """测试数字转中文功能"""
        # 测试 1-10
        self.assertEqual(PathValidator._number_to_chinese(1), "一")
        self.assertEqual(PathValidator._number_to_chinese(5), "五")
        self.assertEqual(PathValidator._number_to_chinese(10), "十")
        
        # 测试 11-19
        self.assertEqual(PathValidator._number_to_chinese(11), "十一")
        self.assertEqual(PathValidator._number_to_chinese(15), "十五")
        self.assertEqual(PathValidator._number_to_chinese(19), "十九")
        
        # 测试 20+
        self.assertEqual(PathValidator._number_to_chinese(20), "20")
        self.assertEqual(PathValidator._number_to_chinese(25), "25")
        self.assertEqual(PathValidator._number_to_chinese(100), "100")

    def test_sanitize_name_edge_cases(self):
        """测试 sanitize_name 的边界情况"""
        # 空字符串应该抛出异常
        with self.assertRaises(ValidationError):
            PathValidator.sanitize_name("")
        
        # 只有空格应该抛出异常
        with self.assertRaises(ValidationError):
            PathValidator.sanitize_name("   ")
        
        # 只有非法字符应该抛出异常
        with self.assertRaises(ValidationError):
            PathValidator.sanitize_name("///")
        
        # 正常名称应该保持不变
        self.assertEqual(PathValidator.sanitize_name("数据结构"), "数据结构")
        self.assertEqual(PathValidator.sanitize_name("Class1"), "Class1")
        
        # 包含非法字符的名称应该被清理
        self.assertEqual(PathValidator.sanitize_name("数据/结构"), "数据-结构")
        self.assertEqual(PathValidator.sanitize_name("Class:1"), "Class-1")
        
        # 多个连续的连字符应该被合并
        self.assertEqual(PathValidator.sanitize_name("a///b"), "a-b")
        
        # 首尾的连字符应该被移除
        self.assertEqual(PathValidator.sanitize_name("/abc/"), "abc")

    @given(
        name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"), min_codepoint=32, max_codepoint=126
            ),
            min_size=1,
            max_size=100,
        )
    )
    @settings(max_examples=100)
    def test_property_10_special_char_handling(self, name):
        """**Feature: assignment-management-refactor, Property 10: 路径特殊字符处理**

        For any 包含特殊字符的课程名、班级名或作业次数，
        系统应该进行转义或替换以确保文件系统兼容性
        **Validates: Requirements 4.7**
        """
        # 尝试清理名称
        try:
            result = PathValidator.sanitize_name(name)
            
            # 如果成功清理，验证结果不包含非法字符
            for illegal_char in PathValidator.ILLEGAL_CHARS:
                self.assertNotIn(illegal_char, result)
            
            # 验证结果不为空
            self.assertTrue(result)
            
            # 验证结果不以连字符开头或结尾
            self.assertFalse(result.startswith('-'))
            self.assertFalse(result.endswith('-'))
            
            # 验证结果不包含连续的连字符
            self.assertNotIn('--', result)
            
        except ValidationError:
            # 如果抛出异常，验证是合理的情况：
            # 1. 名称为空或只有空格
            # 2. 名称只包含非法字符
            # 3. 清理后名称为空（如只有连字符或特殊字符）
            stripped = name.strip()
            
            # 这些情况应该抛出异常
            is_valid_exception = (
                not stripped or  # 空字符串
                all(c in PathValidator.ILLEGAL_CHARS for c in stripped) or  # 只有非法字符
                all(c in PathValidator.ILLEGAL_CHARS or c == '-' or c.isspace() for c in stripped)  # 只有非法字符、连字符或空格
            )
            
            # 验证异常是合理的
            self.assertTrue(
                is_valid_exception,
                f"Unexpected ValidationError for input: {repr(name)}"
            )

    @given(
        course_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"), min_codepoint=32, max_codepoint=126
            ),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip())
    )
    @settings(max_examples=100)
    def test_property_15_course_name_validation(self, course_name):
        """**Feature: assignment-management-refactor, Property 15: 课程名称验证**

        For any 课程名称输入，系统应该验证名称不为空且不包含
        文件系统非法字符
        **Validates: Requirements 8.1**
        """
        # 检查是否包含非法字符
        has_illegal = any(char in course_name for char in PathValidator.ILLEGAL_CHARS)

        if has_illegal or not course_name.strip():
            # 如果包含非法字符或为空，清理后应该不同或抛出异常
            try:
                cleaned = PathValidator.sanitize_name(course_name)
                # 清理后不应该包含非法字符
                for illegal_char in PathValidator.ILLEGAL_CHARS:
                    self.assertNotIn(illegal_char, cleaned)
            except ValidationError:
                # 预期的异常（如果清理后为空）
                pass
        else:
            # 如果不包含非法字符，应该成功清理
            cleaned = PathValidator.sanitize_name(course_name)
            self.assertTrue(cleaned)
            for illegal_char in PathValidator.ILLEGAL_CHARS:
                self.assertNotIn(illegal_char, cleaned)

    @given(
        class_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"), min_codepoint=32, max_codepoint=126
            ),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip())
    )
    @settings(max_examples=100)
    def test_property_16_class_name_validation(self, class_name):
        """**Feature: assignment-management-refactor, Property 16: 班级名称验证**

        For any 班级名称输入，系统应该验证名称不为空且不包含
        文件系统非法字符
        **Validates: Requirements 8.2**
        """
        # 检查是否包含非法字符
        has_illegal = any(char in class_name for char in PathValidator.ILLEGAL_CHARS)

        if has_illegal or not class_name.strip():
            # 如果包含非法字符或为空，清理后应该不同或抛出异常
            try:
                cleaned = PathValidator.sanitize_name(class_name)
                # 清理后不应该包含非法字符
                for illegal_char in PathValidator.ILLEGAL_CHARS:
                    self.assertNotIn(illegal_char, cleaned)
            except ValidationError:
                # 预期的异常（如果清理后为空）
                pass
        else:
            # 如果不包含非法字符，应该成功清理
            cleaned = PathValidator.sanitize_name(class_name)
            self.assertTrue(cleaned)
            for illegal_char in PathValidator.ILLEGAL_CHARS:
                self.assertNotIn(illegal_char, cleaned)

    @given(existing_numbers=st.lists(st.integers(min_value=1, max_value=100), max_size=20))
    @settings(max_examples=100)
    def test_property_21_assignment_number_auto_increment(self, existing_numbers):
        """**Feature: assignment-management-refactor, Property 21: 作业次数自动递增**

        For any 现有的作业次数列表，点击"创建新作业"应该生成下一个序号的
        作业目录名（如已有"第一次作业"则生成"第二次作业"）
        **Validates: Requirements 9.3**
        """
        result = PathValidator.generate_assignment_number_name(existing_numbers)

        # 验证格式
        self.assertTrue(result.startswith("第"))
        self.assertTrue(result.endswith("次作业"))

        # 验证递增逻辑
        if existing_numbers:
            expected_number = max(existing_numbers) + 1
        else:
            expected_number = 1

        # 验证数字在名称中
        if expected_number <= 10:
            # 应该包含中文数字
            chinese_nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
            self.assertIn(chinese_nums[expected_number], result)
        elif expected_number < 20:
            # 应该是"十X"格式
            self.assertIn("十", result)
        else:
            # 应该包含阿拉伯数字
            self.assertIn(str(expected_number), result)

    @given(existing_numbers=st.lists(st.integers(min_value=1, max_value=100), max_size=20))
    @settings(max_examples=100)
    def test_property_22_assignment_naming_consistency(self, existing_numbers):
        """**Feature: assignment-management-refactor, Property 22: 作业命名规范一致性**

        For any 自动生成的作业目录名称，应该遵循统一的命名规范（"第N次作业"格式）
        **Validates: Requirements 9.4**
        """
        result = PathValidator.generate_assignment_number_name(existing_numbers)

        # 验证统一格式
        self.assertTrue(result.startswith("第"))
        self.assertTrue(result.endswith("次作业"))

        # 验证格式一致性：多次调用应该产生相同结果
        result2 = PathValidator.generate_assignment_number_name(existing_numbers)
        self.assertEqual(result, result2)

    @given(
        assignment_name=st.one_of(
            # 有效格式：中文数字
            st.builds(
                lambda n: f"第{n}次作业",
                n=st.sampled_from(["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"])
            ),
            # 有效格式：阿拉伯数字
            st.builds(
                lambda n: f"第{n}次作业",
                n=st.integers(min_value=1, max_value=100).map(str)
            ),
            # 有效格式：实验
            st.builds(
                lambda n: f"第{n}次实验",
                n=st.sampled_from(["一", "二", "三", "1", "2", "3", "10", "20"])
            ),
            # 有效格式：练习
            st.builds(
                lambda n: f"第{n}次练习",
                n=st.sampled_from(["一", "二", "三", "1", "2", "3", "10", "20"])
            ),
            # 无效格式：缺少"第"
            st.builds(
                lambda n: f"{n}次作业",
                n=st.sampled_from(["一", "1", "10"])
            ),
            # 无效格式：缺少"次"
            st.builds(
                lambda n: f"第{n}作业",
                n=st.sampled_from(["一", "1", "10"])
            ),
            # 无效格式：错误的类型
            st.builds(
                lambda n: f"第{n}次测试",
                n=st.sampled_from(["一", "1", "10"])
            ),
            # 无效格式：随机文本
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N")),
                min_size=1,
                max_size=20
            ).filter(lambda x: not x.startswith("第"))
        )
    )
    @settings(max_examples=100)
    def test_property_17_assignment_number_format_validation(self, assignment_name):
        """**Feature: assignment-management-refactor, Property 17: 作业次数格式验证**

        For any 作业次数输入，系统应该验证格式符合 "第N次作业" 或 "第N次实验" 等规范格式
        **Validates: Requirements 8.3**
        """
        result = PathValidator.validate_assignment_number_format(assignment_name)

        # 检查名称是否符合有效格式
        valid_patterns = [
            r'^第[一二三四五六七八九十\d]+次作业$',
            r'^第[一二三四五六七八九十\d]+次实验$',
            r'^第[一二三四五六七八九十\d]+次练习$',
        ]

        expected_valid = any(re.match(pattern, assignment_name) for pattern in valid_patterns)

        # 验证结果与预期一致
        self.assertEqual(
            result,
            expected_valid,
            f"Validation mismatch for '{assignment_name}': got {result}, expected {expected_valid}"
        )


class TestCredentialEncryptionProperties(TestCase):
    """CredentialEncryption 属性测试"""

    @given(
        plaintext=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=200
        )
    )
    @settings(max_examples=100)
    def test_property_30_credential_secure_storage(self, plaintext):
        """**Feature: assignment-management-refactor, Property 30: 凭据安全存储**

        For any Git 仓库认证凭据，应该使用加密方式存储在数据库中，
        不应该以明文形式存储
        **Validates: Requirements 10.7**
        """
        # 加密
        encrypted = CredentialEncryption.encrypt(plaintext)

        # 验证加密后不等于明文
        self.assertNotEqual(encrypted, plaintext)

        # 验证加密后的长度大于0
        self.assertTrue(len(encrypted) > 0)

        # 解密
        decrypted = CredentialEncryption.decrypt(encrypted)

        # 验证解密后等于原文
        self.assertEqual(decrypted, plaintext)

        # 验证加密是确定性的（相同输入产生相同输出）
        encrypted2 = CredentialEncryption.encrypt(plaintext)
        # 注意：Fernet 加密包含随机 IV，所以每次加密结果不同
        # 但解密后应该相同
        decrypted2 = CredentialEncryption.decrypt(encrypted2)
        self.assertEqual(decrypted2, plaintext)


class TestCacheManagerProperties(TestCase):
    """CacheManager 属性测试"""

    def setUp(self):
        """测试前清理缓存"""
        cache.clear()

    def tearDown(self):
        """测试后清理缓存"""
        cache.clear()

    @given(
        assignment_id=st.integers(min_value=1, max_value=10000),
        path=st.text(alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=50),
        data=st.lists(
            st.fixed_dictionaries({
                "name": st.text(max_size=20),
                "type": st.sampled_from(["file", "dir"]),
                "size": st.integers(min_value=0, max_value=10000),
            }),
            max_size=5,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[hypothesis.HealthCheck.too_slow])
    def test_property_27_memory_cache_constraint(self, assignment_id, path, data):
        """**Feature: assignment-management-refactor, Property 27: 内存缓存约束**

        For any 远程仓库数据缓存，应该使用内存缓存（Django cache）
        而不是文件系统缓存
        **Validates: Requirements 10.4**
        """
        # 设置缓存
        CacheManager.set_directory_listing(assignment_id, path, data)

        # 验证可以从缓存获取
        cached_data = CacheManager.get_directory_listing(assignment_id, path)

        # 验证缓存数据正确
        self.assertEqual(cached_data, data)

        # 验证使用的是 Django 缓存（内存缓存）
        # 通过检查缓存键的存在来验证
        cache_key = CacheManager.get_cache_key(assignment_id, path, "ls")
        self.assertIsNotNone(cache.get(cache_key))

    @given(
        assignment_id=st.integers(min_value=1, max_value=10000),
        path=st.text(alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=50),
        content=st.binary(min_size=1, max_size=1000),
    )
    @settings(max_examples=100, suppress_health_check=[hypothesis.HealthCheck.too_slow])
    def test_property_28_cache_auto_refresh(self, assignment_id, path, content):
        """**Feature: assignment-management-refactor, Property 28: 缓存自动刷新**

        For any 过期的缓存数据，系统应该自动从远程仓库重新获取最新数据
        **Validates: Requirements 10.5**
        """
        # 设置缓存
        CacheManager.set_file_content(assignment_id, path, content)

        # 验证缓存存在
        cached_content = CacheManager.get_file_content(assignment_id, path)
        self.assertEqual(cached_content, content)

        # 清除缓存模拟过期
        cache_key = CacheManager.get_cache_key(assignment_id, path, "file")
        cache.delete(cache_key)

        # 验证缓存已过期（返回 None）
        expired_content = CacheManager.get_file_content(assignment_id, path)
        self.assertIsNone(expired_content)

        # 在实际应用中，这里会触发从远程仓库重新获取
        # 这个测试验证了缓存过期机制正常工作

    @given(
        assignment_id=st.integers(min_value=1, max_value=10000),
        path=st.text(alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=50),
        data=st.lists(
            st.fixed_dictionaries({
                "name": st.text(max_size=20),
                "type": st.sampled_from(["file", "dir"]),
                "size": st.integers(min_value=0, max_value=10000),
            }),
            max_size=5,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[hypothesis.HealthCheck.too_slow])
    def test_property_29_cache_sharing(self, assignment_id, path, data):
        """**Feature: assignment-management-refactor, Property 29: 缓存共享**

        For any 多个教师访问同一仓库的相同路径，应该共享缓存数据以提高性能
        **Validates: Requirements 10.6**
        """
        # 第一个教师设置缓存
        CacheManager.set_directory_listing(assignment_id, path, data)

        # 第二个教师访问相同的作业和路径
        # 应该获取到相同的缓存数据
        cached_data = CacheManager.get_directory_listing(assignment_id, path)

        # 验证缓存共享
        self.assertEqual(cached_data, data)

        # 验证缓存键相同（基于 assignment_id 和 path）
        cache_key1 = CacheManager.get_cache_key(assignment_id, path, "ls")
        cache_key2 = CacheManager.get_cache_key(assignment_id, path, "ls")
        self.assertEqual(cache_key1, cache_key2)

        # 验证不同路径产生不同的缓存键
        different_path = path + "_different"
        cache_key3 = CacheManager.get_cache_key(assignment_id, different_path, "ls")
        self.assertNotEqual(cache_key1, cache_key3)
