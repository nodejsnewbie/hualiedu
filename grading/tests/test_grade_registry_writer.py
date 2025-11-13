"""
作业成绩写入成绩登分册工具类单元测试

测试三个核心工具类：
- GradeFileProcessor: 处理作业成绩文件
- RegistryManager: 管理Excel登分册
- NameMatcher: 学生姓名匹配
"""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from docx import Document
from openpyxl import Workbook

from grading.grade_registry_writer import (
    GradeFileProcessor,
    RegistryManager,
    NameMatcher,
)
from .base import BaseTestCase


class GradeFileProcessorExtractStudentNameTest(BaseTestCase):
    """测试GradeFileProcessor.extract_student_name方法"""

    def test_extract_name_with_underscore_name_first(self):
        """测试使用下划线分隔，姓名在前"""
        result = GradeFileProcessor.extract_student_name("张三_作业1.docx")
        self.assertEqual(result, "张三")

    def test_extract_name_with_underscore_homework_first(self):
        """测试使用下划线分隔，作业标识在前"""
        result = GradeFileProcessor.extract_student_name("作业1_张三.docx")
        self.assertEqual(result, "张三")

    def test_extract_name_with_hyphen(self):
        """测试使用连字符分隔"""
        result = GradeFileProcessor.extract_student_name("张三-作业1.docx")
        self.assertEqual(result, "张三")

    def test_extract_name_with_em_dash(self):
        """测试使用长破折号分隔"""
        result = GradeFileProcessor.extract_student_name("张三—作业1.docx")
        self.assertEqual(result, "张三")
    
    def test_extract_name_no_separator(self):
        """文件名无分隔符时应直接返回文件名"""
        result = GradeFileProcessor.extract_student_name("李四.docx")
        self.assertEqual(result, "李四")


class GradeFileProcessorExtractHomeworkNumberTest(BaseTestCase):
    """测试作业批次提取支持中文数字"""

    def test_extract_from_path_with_chinese_characters(self):
        """目录名包含中文数字时也能识别批次"""
        path = "/tmp/Web前端开发/23计算机5班/第一次作业"
        self.assertEqual(GradeFileProcessor.extract_homework_number_from_path(path), 1)

    def test_extract_from_path_with_double_digit_chinese(self):
        """支持两位中文数字（第十二次）"""
        path = "/tmp/Web前端开发/23计算机5班/第十二次作业"
        self.assertEqual(GradeFileProcessor.extract_homework_number_from_path(path), 12)

    def test_extract_from_filename_with_chinese_characters(self):
        """Excel 文件名中的中文数字可识别"""
        filename = "/tmp/成绩/第十次作业成绩.xlsx"
        self.assertEqual(GradeFileProcessor.extract_homework_number_from_filename(filename), 10)


class RegistryManagerConcurrencyTest(BaseTestCase):
    """测试RegistryManager的并发控制功能"""

    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.test_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.test_dir, "成绩登分册.xlsx")
        self._create_test_registry()

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        super().tearDown()

    def _create_test_registry(self):
        """创建测试用的登分册文件"""
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "成绩表"

        # 添加表头
        worksheet.cell(1, 1).value = "姓名"
        worksheet.cell(1, 2).value = "学号"

        # 添加学生数据
        students = [
            ("张三", "20210001"),
            ("李四", "20210002"),
            ("王五", "20210003"),
        ]
        for i, (name, student_id) in enumerate(students, start=2):
            worksheet.cell(i, 1).value = name
            worksheet.cell(i, 2).value = student_id

        workbook.save(self.registry_path)
        workbook.close()

    def test_acquire_file_lock_success(self):
        """测试成功获取文件锁"""
        manager = RegistryManager(self.registry_path)

        # 加载文件应该成功获取锁
        self.assertTrue(manager.load())
        self.assertIsNotNone(manager.lock_file_handle)
        self.assertTrue(os.path.exists(manager.lock_file_path))

        # 清理
        manager._release_file_lock()

    def test_file_lock_prevents_concurrent_access(self):
        """测试文件锁阻止并发访问"""
        manager1 = RegistryManager(self.registry_path)
        manager2 = RegistryManager(self.registry_path)

        # 第一个管理器加载文件并获取锁
        self.assertTrue(manager1.load())

        # 第二个管理器尝试加载应该失败（文件被锁定）
        self.assertFalse(manager2.load())

        # 释放第一个管理器的锁
        manager1._release_file_lock()

        # 现在第二个管理器应该能够加载
        self.assertTrue(manager2.load())
        manager2._release_file_lock()

    def test_release_file_lock(self):
        """测试释放文件锁"""
        manager = RegistryManager(self.registry_path)

        # 获取锁
        manager.load()
        lock_file_path = manager.lock_file_path

        # 释放锁
        manager._release_file_lock()

        # 验证锁文件被删除
        self.assertFalse(os.path.exists(lock_file_path))
        self.assertIsNone(manager.lock_file_handle)

    def test_check_file_in_use(self):
        """测试检测文件是否被占用"""
        manager1 = RegistryManager(self.registry_path)
        manager2 = RegistryManager(self.registry_path)

        # 第一个管理器加载文件
        manager1.load()

        # 第二个管理器尝试加载应该失败（因为文件被锁定）
        # _check_file_in_use 在 load() 中被调用
        self.assertFalse(manager2.load())

        # 释放锁后应该能够加载
        manager1._release_file_lock()
        self.assertTrue(manager2.load())
        manager2._release_file_lock()

    def test_save_releases_lock(self):
        """测试保存文件后释放锁"""
        manager = RegistryManager(self.registry_path)

        # 加载并修改
        manager.load()
        manager.validate_format()
        lock_file_path = manager.lock_file_path

        # 保存应该释放锁
        self.assertTrue(manager.save())
        self.assertFalse(os.path.exists(lock_file_path))
        self.assertIsNone(manager.lock_file_handle)

    def test_restore_from_backup_releases_lock(self):
        """测试从备份恢复后释放锁"""
        manager = RegistryManager(self.registry_path)

        # 加载并创建备份
        manager.load()
        manager.validate_format()
        manager.create_backup()
        lock_file_path = manager.lock_file_path

        # 恢复应该释放锁
        self.assertTrue(manager.restore_from_backup())
        self.assertFalse(os.path.exists(lock_file_path))
        self.assertIsNone(manager.lock_file_handle)

    def test_destructor_releases_lock(self):
        """测试析构函数释放锁"""
        manager = RegistryManager(self.registry_path)
        manager.load()
        lock_file_path = manager.lock_file_path

        # 删除对象应该释放锁
        del manager

        # 验证锁文件被删除
        self.assertFalse(os.path.exists(lock_file_path))

    def test_concurrent_write_conflict_handling(self):
        """测试并发写入冲突处理"""
        manager1 = RegistryManager(self.registry_path)
        manager2 = RegistryManager(self.registry_path)

        # 第一个管理器加载并修改
        self.assertTrue(manager1.load())
        self.assertTrue(manager1.validate_format()[0])
        col = manager1.find_or_create_homework_column(1)
        row = manager1.find_student_row("张三")
        manager1.write_grade(row, col, "A")

        # 第二个管理器尝试加载应该失败
        self.assertFalse(manager2.load())

        # 第一个管理器保存
        self.assertTrue(manager1.save())

        # 现在第二个管理器可以加载
        self.assertTrue(manager2.load())
        self.assertTrue(manager2.validate_format()[0])

        # 验证第一个管理器的修改已保存
        row = manager2.find_student_row("张三")
        grade = manager2.worksheet.cell(row, col).value
        self.assertEqual(grade, "A")

        manager2._release_file_lock()

    def test_load_failure_releases_lock(self):
        """测试加载失败时释放锁"""
        # 创建一个不存在的文件路径
        invalid_path = os.path.join(self.test_dir, "不存在的文件.xlsx")
        manager = RegistryManager(invalid_path)

        # 加载应该失败
        self.assertFalse(manager.load())

        # 验证没有锁文件残留
        lock_file_path = f"{invalid_path}.lock"
        self.assertFalse(os.path.exists(lock_file_path))
        self.assertIsNone(manager.lock_file_handle)


class RegistryManagerHeaderDetectionTest(BaseTestCase):
    """测试登分册表头自动检测"""

    def setUp(self):
        super().setUp()
        self.test_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.test_dir, "registry.xlsx")
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(["学校成绩表"])
        worksheet.append(["", "", ""])
        worksheet.append(["序号", "学号", "姓名", "第1次作业"])
        worksheet.append([1, "1001", "张三", "A"])
        workbook.save(self.registry_path)
        workbook.close()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        super().tearDown()

    def test_validate_format_detects_header_not_in_first_row(self):
        manager = RegistryManager(self.registry_path)
        self.assertTrue(manager.load())
        is_valid, error = manager.validate_format()
        self.assertTrue(is_valid, msg=error)
        self.assertEqual(manager.header_row_index, 3)
        self.assertEqual(manager.name_column_index, 3)
        self.assertEqual(manager.find_student_row("张三"), 4)
        manager._release_file_lock()
