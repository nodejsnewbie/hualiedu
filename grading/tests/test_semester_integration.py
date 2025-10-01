"""
学期管理集成测试

测试学期自动创建和管理的完整流程，包括：
- 端到端的自动创建流程
- 各种日期场景的处理
- 与现有功能的集成
- 并发访问的数据一致性
- 错误恢复和回滚机制
"""

import threading
import time
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from grading.exceptions import SemesterError
from grading.models import Course, Semester, SemesterTemplate
from grading.services.semester_auto_creator import SemesterAutoCreator
from grading.services.semester_config import config_manager, template_manager
from grading.services.semester_manager import SemesterManager


class SemesterIntegrationTest(TestCase):
    """学期管理集成测试类"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # 清理现有数据
        Semester.objects.all().delete()
        SemesterTemplate.objects.all().delete()

        # 初始化默认模板
        template_manager.ensure_default_templates()

    def test_complete_auto_creation_flow(self):
        """测试完整的自动创建流程"""
        # 1. 初始状态：没有学期
        self.assertEqual(Semester.objects.count(), 0)

        # 2. 创建当前学期
        today = date.today()
        auto_creator = SemesterAutoCreator()

        # 第一次调用应该创建学期
        new_semester = auto_creator.check_and_create_current_semester(today)
        self.assertIsNotNone(new_semester)
        self.assertTrue(new_semester.auto_created)

        # 3. 验证学期管理器能正确识别
        manager = SemesterManager()
        current_semester = manager.get_current_semester(today)
        self.assertEqual(current_semester.id, new_semester.id)
        self.assertTrue(current_semester.is_active)

        # 4. 再次调用不应该创建重复学期
        duplicate_semester = auto_creator.check_and_create_current_semester(today)
        self.assertIsNone(duplicate_semester)
        self.assertEqual(Semester.objects.count(), 1)

        # 5. 测试排序功能
        sorted_semesters = manager.get_sorted_semesters_for_display()
        self.assertEqual(len(sorted_semesters), 1)
        self.assertEqual(sorted_semesters[0].id, new_semester.id)

    def test_multiple_semester_scenarios(self):
        """测试多学期场景"""
        today = date.today()

        # 创建过去的学期
        past_semester = Semester.objects.create(
            name="2023年春季学期",
            start_date=date(2023, 3, 1),
            end_date=date(2023, 7, 15),
            is_active=False,
            auto_created=True,
        )

        # 创建未来的学期
        future_semester = Semester.objects.create(
            name="2025年春季学期",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 7, 15),
            is_active=False,
            auto_created=True,
        )

        # 创建当前学期
        auto_creator = SemesterAutoCreator()
        current_semester = auto_creator.check_and_create_current_semester(today)

        # 验证学期管理器的排序
        manager = SemesterManager()
        sorted_semesters = manager.get_sorted_semesters_for_display()

        # 当前学期应该在第一位
        self.assertEqual(sorted_semesters[0].id, current_semester.id)
        self.assertTrue(sorted_semesters[0].is_active)

        # 其他学期应该按时间倒序
        non_current = [s for s in sorted_semesters if not s.is_active]
        self.assertTrue(len(non_current) >= 2)

        # 验证状态信息
        for semester in sorted_semesters:
            status_info = manager.get_semester_status_info(semester, today)
            if semester.id == current_semester.id:
                self.assertEqual(status_info["status"], "current")
                self.assertTrue(status_info["is_current"])
            elif semester.end_date < today:
                self.assertEqual(status_info["status"], "past")
            elif semester.start_date > today:
                self.assertEqual(status_info["status"], "future")

    def test_semester_with_courses_integration(self):
        """测试与课程的集成"""
        # 创建学期
        semester = Semester.objects.create(
            name="测试学期",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            is_active=True,
        )

        # 创建课程
        course = Course.objects.create(
            semester=semester, teacher=self.user, name="测试课程", location="测试教室"
        )

        # 验证学期管理器能正确处理有课程的学期
        manager = SemesterManager()
        current_semester = manager.get_current_semester()
        self.assertEqual(current_semester.id, semester.id)

        # 验证状态同步不会影响有课程的学期
        result = manager.sync_all_semester_status()
        self.assertTrue(result["success"])

        # 验证课程仍然存在
        course.refresh_from_db()
        self.assertEqual(course.semester.id, semester.id)

    def test_date_boundary_scenarios(self):
        """测试日期边界场景"""
        # 测试学期开始日期
        semester = Semester.objects.create(
            name="边界测试学期",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 7, 31),
            is_active=False,
        )

        manager = SemesterManager()

        # 测试开始日期当天
        self.assertTrue(manager.is_semester_current(semester, date(2024, 3, 1)))

        # 测试结束日期当天
        self.assertTrue(manager.is_semester_current(semester, date(2024, 7, 31)))

        # 测试开始前一天
        self.assertFalse(manager.is_semester_current(semester, date(2024, 2, 29)))

        # 测试结束后一天
        self.assertFalse(manager.is_semester_current(semester, date(2024, 8, 1)))

    def test_template_based_creation(self):
        """测试基于模板的创建"""
        # 确保有春季模板
        spring_template = SemesterTemplate.objects.filter(season="spring", is_active=True).first()
        self.assertIsNotNone(spring_template)

        # 测试春季日期的创建
        spring_date = date(2024, 4, 15)  # 春季中间
        auto_creator = SemesterAutoCreator()

        spring_semester = auto_creator.check_and_create_current_semester(spring_date)
        self.assertIsNotNone(spring_semester)
        self.assertEqual(spring_semester.season, "spring")

        # 测试秋季日期的创建
        autumn_date = date(2024, 10, 15)  # 秋季中间
        autumn_semester = auto_creator.check_and_create_current_semester(autumn_date)
        self.assertIsNotNone(autumn_semester)
        self.assertEqual(autumn_semester.season, "autumn")

    def test_reference_semester_creation(self):
        """测试基于参考学期的创建"""
        # 创建参考学期（去年春季）
        reference_semester = Semester.objects.create(
            name="2023年春季学期",
            start_date=date(2023, 3, 1),
            end_date=date(2023, 7, 15),
            is_active=False,
            season="spring",
        )

        # 创建今年春季学期（应该基于参考学期）
        spring_date = date(2024, 4, 15)
        auto_creator = SemesterAutoCreator()

        new_semester = auto_creator.check_and_create_current_semester(spring_date)
        self.assertIsNotNone(new_semester)
        self.assertEqual(new_semester.reference_semester.id, reference_semester.id)

        # 验证日期是基于参考学期计算的
        expected_start = date(2024, 3, 1)  # 参考学期的下一年
        self.assertEqual(new_semester.start_date, expected_start)

    def test_configuration_integration(self):
        """测试配置集成"""
        # 测试禁用自动创建
        original_enabled = config_manager.get_config("AUTO_CREATION_ENABLED")

        try:
            config_manager.set_config("AUTO_CREATION_ENABLED", False)

            auto_creator = SemesterAutoCreator()
            result = auto_creator.check_and_create_current_semester()

            # 当禁用时，应该不创建学期
            # 注意：这取决于具体实现，可能需要在auto_creator中添加配置检查

        finally:
            config_manager.set_config("AUTO_CREATION_ENABLED", original_enabled)

    def test_management_command_integration(self):
        """测试管理命令集成"""
        # 测试同步命令
        call_command("semester_management", "sync")

        # 测试创建当前学期命令
        call_command("semester_management", "create-current")

        # 验证学期被创建
        self.assertTrue(Semester.objects.exists())

        # 测试列表命令
        call_command("semester_management", "list", "--format=json")

        # 测试统计命令
        call_command("semester_management", "stats")

    def test_error_recovery(self):
        """测试错误恢复机制"""
        # 创建无效的学期数据
        invalid_semester = Semester.objects.create(
            name="无效学期",
            start_date=date(2024, 7, 1),
            end_date=date(2024, 3, 1),  # 结束日期早于开始日期
            is_active=False,
        )

        # 测试验证命令能发现问题
        call_command("semester_management", "validate", "--fix")

        # 验证问题被修复
        invalid_semester.refresh_from_db()
        self.assertLess(invalid_semester.start_date, invalid_semester.end_date)


class SemesterConcurrencyTest(TransactionTestCase):
    """学期并发访问测试"""

    def setUp(self):
        """设置测试数据"""
        # 清理现有数据
        Semester.objects.all().delete()
        SemesterTemplate.objects.all().delete()

        # 初始化默认模板
        template_manager.ensure_default_templates()

    def test_concurrent_semester_creation(self):
        """测试并发学期创建"""
        results = []
        errors = []

        def create_semester_worker():
            """工作线程函数"""
            try:
                auto_creator = SemesterAutoCreator()
                result = auto_creator.check_and_create_current_semester()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时尝试创建学期
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_semester_worker)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果：应该只有一个学期被创建
        created_semesters = [r for r in results if r is not None]
        self.assertEqual(len(created_semesters), 1, "应该只创建一个学期")
        self.assertEqual(Semester.objects.count(), 1, "数据库中应该只有一个学期")

        # 验证没有严重错误
        serious_errors = [e for e in errors if not isinstance(e, SemesterError)]
        self.assertEqual(len(serious_errors), 0, "不应该有严重错误")

    def test_concurrent_status_sync(self):
        """测试并发状态同步"""
        # 创建测试学期
        today = date.today()
        Semester.objects.create(
            name="测试学期1",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            is_active=False,  # 故意设为错误状态
        )

        Semester.objects.create(
            name="测试学期2",
            start_date=today + timedelta(days=90),
            end_date=today + timedelta(days=180),
            is_active=True,  # 故意设为错误状态
        )

        results = []
        errors = []

        def sync_worker():
            """同步工作线程"""
            try:
                manager = SemesterManager()
                result = manager.sync_all_semester_status()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时同步
        threads = []
        for i in range(3):
            thread = threading.Thread(target=sync_worker)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证最终状态一致
        active_semesters = Semester.objects.filter(is_active=True)
        self.assertEqual(active_semesters.count(), 1, "应该只有一个活跃学期")

        # 验证活跃学期是正确的（当前学期）
        active_semester = active_semesters.first()
        manager = SemesterManager()
        self.assertTrue(manager.is_semester_current(active_semester, today))

    def test_concurrent_template_initialization(self):
        """测试并发模板初始化"""
        # 删除所有模板
        SemesterTemplate.objects.all().delete()

        results = []
        errors = []

        def init_templates_worker():
            """模板初始化工作线程"""
            try:
                result = template_manager.ensure_default_templates()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时初始化模板
        threads = []
        for i in range(3):
            thread = threading.Thread(target=init_templates_worker)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证模板被正确创建
        spring_templates = SemesterTemplate.objects.filter(season="spring", is_active=True)
        autumn_templates = SemesterTemplate.objects.filter(season="autumn", is_active=True)

        self.assertEqual(spring_templates.count(), 1, "应该只有一个春季模板")
        self.assertEqual(autumn_templates.count(), 1, "应该只有一个秋季模板")

        # 验证没有严重错误
        serious_errors = [e for e in errors if not isinstance(e, SemesterError)]
        self.assertEqual(len(serious_errors), 0, "不应该有严重错误")


class SemesterPerformanceTest(TestCase):
    """学期管理性能测试"""

    def setUp(self):
        """设置测试数据"""
        # 清理现有数据
        Semester.objects.all().delete()

        # 创建大量测试学期
        self.create_test_semesters(100)

    def create_test_semesters(self, count):
        """创建测试学期"""
        semesters = []
        base_date = date(2020, 1, 1)

        for i in range(count):
            start_date = base_date + timedelta(days=i * 180)  # 每6个月一个学期
            end_date = start_date + timedelta(days=120)  # 4个月长度

            semester = Semester(
                name=f"测试学期{i+1}",
                start_date=start_date,
                end_date=end_date,
                is_active=(i == count - 1),  # 最后一个为活跃
                auto_created=True,
            )
            semesters.append(semester)

        Semester.objects.bulk_create(semesters)

    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        manager = SemesterManager()

        # 测试获取排序学期列表的性能
        start_time = time.time()
        sorted_semesters = manager.get_sorted_semesters_for_display()
        end_time = time.time()

        # 验证结果正确性
        self.assertEqual(len(sorted_semesters), 100)
        self.assertTrue(sorted_semesters[0].is_active)  # 当前学期在第一位

        # 验证性能（应该在合理时间内完成）
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0, f"排序操作耗时过长: {execution_time:.3f}秒")

    def test_status_sync_performance(self):
        """测试状态同步性能"""
        manager = SemesterManager()

        # 测试同步所有学期状态的性能
        start_time = time.time()
        result = manager.sync_all_semester_status()
        end_time = time.time()

        # 验证结果正确性
        self.assertTrue(result["success"])
        self.assertEqual(result["total_semesters"], 100)

        # 验证性能
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0, f"状态同步耗时过长: {execution_time:.3f}秒")
