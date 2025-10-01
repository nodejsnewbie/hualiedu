"""
学期管理器测试模块

测试学期管理器的自动识别和管理功能
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from grading.models import Semester
from grading.services.semester_manager import SemesterManager


class SemesterManagerTest(TestCase):
    """学期管理器测试类"""

    def setUp(self):
        """设置测试数据"""
        self.manager = SemesterManager()

        # 创建测试用户
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # 创建测试学期
        today = date.today()

        # 过去的学期
        self.past_semester = Semester.objects.create(
            name="2023年春季学期",
            start_date=date(2023, 3, 1),
            end_date=date(2023, 7, 15),
            is_active=False,
        )

        # 当前学期（包含今天）
        self.current_semester = Semester.objects.create(
            name="2024年春季学期",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            is_active=False,  # 故意设为False，测试自动更新
        )

        # 未来的学期
        self.future_semester = Semester.objects.create(
            name="2024年秋季学期",
            start_date=today + timedelta(days=90),
            end_date=today + timedelta(days=180),
            is_active=False,
        )

    def test_auto_update_current_semester(self):
        """测试自动更新当前学期"""
        # 确保开始时没有活跃学期
        self.assertFalse(Semester.objects.filter(is_active=True).exists())

        # 执行自动更新
        result = self.manager.auto_update_current_semester()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.current_semester.id)

        # 验证数据库状态
        self.current_semester.refresh_from_db()
        self.assertTrue(self.current_semester.is_active)

        # 验证其他学期仍为非活跃
        self.past_semester.refresh_from_db()
        self.future_semester.refresh_from_db()
        self.assertFalse(self.past_semester.is_active)
        self.assertFalse(self.future_semester.is_active)

    def test_auto_update_no_current_semester(self):
        """测试没有当前学期的情况"""
        # 删除当前学期
        self.current_semester.delete()

        # 设置一个学期为活跃（但实际不是当前学期）
        self.past_semester.is_active = True
        self.past_semester.save()

        # 执行自动更新
        result = self.manager.auto_update_current_semester()

        # 验证结果
        self.assertIsNone(result)

        # 验证所有学期都被设为非活跃
        self.past_semester.refresh_from_db()
        self.future_semester.refresh_from_db()
        self.assertFalse(self.past_semester.is_active)
        self.assertFalse(self.future_semester.is_active)

    def test_auto_update_multiple_active_semesters(self):
        """测试多个活跃学期的修正"""
        # 设置多个学期为活跃
        self.past_semester.is_active = True
        self.past_semester.save()
        self.future_semester.is_active = True
        self.future_semester.save()

        # 执行自动更新
        result = self.manager.auto_update_current_semester()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.current_semester.id)

        # 验证只有当前学期为活跃
        self.current_semester.refresh_from_db()
        self.past_semester.refresh_from_db()
        self.future_semester.refresh_from_db()

        self.assertTrue(self.current_semester.is_active)
        self.assertFalse(self.past_semester.is_active)
        self.assertFalse(self.future_semester.is_active)

    def test_get_current_semester(self):
        """测试获取当前学期"""
        result = self.manager.get_current_semester()

        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.current_semester.id)

        # 验证学期状态已更新
        self.current_semester.refresh_from_db()
        self.assertTrue(self.current_semester.is_active)

    def test_get_sorted_semesters_for_display(self):
        """测试获取排序的学期列表"""
        semesters = self.manager.get_sorted_semesters_for_display()

        # 验证返回所有学期
        self.assertEqual(len(semesters), 3)

        # 验证当前学期排在第一位
        self.assertEqual(semesters[0].id, self.current_semester.id)
        self.assertTrue(semesters[0].is_active)

        # 验证其他学期按开始日期倒序排列
        remaining_semesters = semesters[1:]
        self.assertEqual(len(remaining_semesters), 2)

        # 未来学期应该在过去学期之前（按开始日期倒序）
        self.assertEqual(remaining_semesters[0].id, self.future_semester.id)
        self.assertEqual(remaining_semesters[1].id, self.past_semester.id)

    def test_is_semester_current(self):
        """测试学期是否为当前学期的判断"""
        today = date.today()

        # 测试当前学期
        self.assertTrue(self.manager.is_semester_current(self.current_semester, today))

        # 测试过去学期
        self.assertFalse(self.manager.is_semester_current(self.past_semester, today))

        # 测试未来学期
        self.assertFalse(self.manager.is_semester_current(self.future_semester, today))

    def test_get_semester_status_info(self):
        """测试获取学期状态信息"""
        today = date.today()

        # 测试当前学期状态
        current_info = self.manager.get_semester_status_info(self.current_semester, today)
        self.assertEqual(current_info["status"], "current")
        self.assertEqual(current_info["status_text"], "当前学期")
        self.assertTrue(current_info["is_current"])
        self.assertTrue(current_info["needs_sync"])  # 因为数据库中is_active=False

        # 测试过去学期状态
        past_info = self.manager.get_semester_status_info(self.past_semester, today)
        self.assertEqual(past_info["status"], "past")
        self.assertEqual(past_info["status_text"], "已结束")
        self.assertFalse(past_info["is_current"])

        # 测试未来学期状态
        future_info = self.manager.get_semester_status_info(self.future_semester, today)
        self.assertEqual(future_info["status"], "future")
        self.assertEqual(future_info["status_text"], "未开始")
        self.assertFalse(future_info["is_current"])

    def test_sync_all_semester_status(self):
        """测试同步所有学期状态"""
        # 设置错误的初始状态
        self.past_semester.is_active = True
        self.past_semester.save()
        self.future_semester.is_active = True
        self.future_semester.save()

        # 执行同步
        result = self.manager.sync_all_semester_status()

        # 验证同步结果
        self.assertTrue(result["success"])
        self.assertEqual(result["total_semesters"], 3)
        self.assertEqual(result["updated_count"], 3)  # 所有学期都需要更新
        self.assertEqual(result["current_semester"], self.current_semester.name)

        # 验证数据库状态
        self.current_semester.refresh_from_db()
        self.past_semester.refresh_from_db()
        self.future_semester.refresh_from_db()

        self.assertTrue(self.current_semester.is_active)
        self.assertFalse(self.past_semester.is_active)
        self.assertFalse(self.future_semester.is_active)

    def test_sync_all_semester_status_no_current(self):
        """测试没有当前学期时的同步"""
        # 删除当前学期
        self.current_semester.delete()

        # 设置其他学期为活跃
        self.past_semester.is_active = True
        self.past_semester.save()

        # 执行同步
        result = self.manager.sync_all_semester_status()

        # 验证同步结果
        self.assertTrue(result["success"])
        self.assertEqual(result["total_semesters"], 2)
        self.assertEqual(result["updated_count"], 1)  # 只有过去学期需要更新
        self.assertIsNone(result["current_semester"])

        # 验证数据库状态
        self.past_semester.refresh_from_db()
        self.future_semester.refresh_from_db()

        self.assertFalse(self.past_semester.is_active)
        self.assertFalse(self.future_semester.is_active)

    def test_edge_case_semester_boundaries(self):
        """测试学期边界日期的处理"""
        # 测试学期开始日期
        start_date = self.current_semester.start_date
        self.assertTrue(self.manager.is_semester_current(self.current_semester, start_date))

        # 测试学期结束日期
        end_date = self.current_semester.end_date
        self.assertTrue(self.manager.is_semester_current(self.current_semester, end_date))

        # 测试学期开始前一天
        before_start = start_date - timedelta(days=1)
        self.assertFalse(self.manager.is_semester_current(self.current_semester, before_start))

        # 测试学期结束后一天
        after_end = end_date + timedelta(days=1)
        self.assertFalse(self.manager.is_semester_current(self.current_semester, after_end))
