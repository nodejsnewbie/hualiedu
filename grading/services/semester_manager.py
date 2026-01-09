"""
学期管理服务模块

提供学期的自动管理功能，包括：
- 自动识别当前学期
- 自动更新学期状态
- 学期排序和显示优化
"""

import logging
from datetime import date
from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from grading.exceptions import (
    SemesterDetectionError,
    SemesterError,
    SemesterErrorContext,
    SemesterOperationError,
    handle_semester_exceptions,
)
from grading.models import Semester
from grading.services.semester_detector import CurrentSemesterDetector

# 配置日志
logger = logging.getLogger(__name__)


class SemesterManager:
    """学期管理服务

    负责学期的自动管理，包括自动识别当前学期、更新学期状态等功能。
    """

    def __init__(self):
        """初始化学期管理服务"""
        self.detector = CurrentSemesterDetector()

    @handle_semester_exceptions(default_return=None)
    def auto_update_current_semester(self, current_date: date = None) -> Optional[Semester]:
        """自动更新当前学期

        根据当前日期自动识别并更新当前学期状态。

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            当前学期对象，如果没有找到则返回None
        """
        if current_date is None:
            current_date = date.today()

        logger.info(f"开始自动更新当前学期，基准日期: {current_date}")

        try:
            with transaction.atomic():
                # 检测当前学期
                detected_semester = self.detector.detect_current_semester(current_date)

                if detected_semester:
                    # 获取当前标记为活跃的学期
                    current_active_semesters = Semester.objects.filter(is_active=True)

                    # 检查是否需要更新
                    needs_update = False

                    if not current_active_semesters.exists():
                        # 没有活跃学期，需要设置
                        needs_update = True
                        logger.info("没有活跃学期，需要设置当前学期")
                    elif current_active_semesters.count() > 1:
                        # 有多个活跃学期，需要修正
                        needs_update = True
                        logger.warning(
                            f"发现多个活跃学期: {[s.name for s in current_active_semesters]}"
                        )
                    elif not current_active_semesters.filter(id=detected_semester.id).exists():
                        # 活跃学期不是检测到的当前学期，需要更新
                        needs_update = True
                        current_active = current_active_semesters.first()
                        logger.info(
                            f"当前活跃学期 '{current_active.name}' 不是实际当前学期 '{detected_semester.name}'"
                        )

                    if needs_update:
                        # 将所有学期设为非活跃
                        Semester.objects.all().update(is_active=False)

                        # 设置检测到的学期为活跃
                        detected_semester.is_active = True
                        detected_semester.save()

                        logger.info(f"已将学期 '{detected_semester.name}' 设置为当前学期")
                    else:
                        logger.info(f"当前学期状态正确: {detected_semester.name}")

                    return detected_semester
                else:
                    # 没有检测到当前学期
                    logger.info("没有检测到当前学期")

                    # 检查是否有错误标记为活跃的学期
                    current_active_semesters = Semester.objects.filter(is_active=True)
                    if current_active_semesters.exists():
                        logger.info("将所有学期设为非活跃状态")
                        current_active_semesters.update(is_active=False)

                    return None

        except Exception as e:
            logger.error(f"自动更新当前学期失败: {str(e)}")
            raise

    def get_current_semester(self, current_date: date = None) -> Optional[Semester]:
        """获取当前学期

        首先尝试自动更新，然后返回当前学期。

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            当前学期对象，如果没有找到则返回None
        """
        try:
            return self.auto_update_current_semester(current_date)
        except Exception as e:
            logger.error(f"获取当前学期失败: {str(e)}")
            # 如果自动更新失败，尝试从数据库获取
            return Semester.objects.filter(is_active=True).first()

    def get_sorted_semesters_for_display(self) -> List[Semester]:
        """获取用于显示的排序学期列表

        返回按显示优先级排序的学期列表：
        1. 当前学期排在最前面
        2. 其他学期按开始日期倒序排列

        Returns:
            排序后的学期列表
        """
        try:
            # 先自动更新当前学期状态
            self.auto_update_current_semester()

            # 获取所有学期
            all_semesters = list(Semester.objects.all().order_by("-start_date"))

            # 分离当前学期和其他学期
            current_semesters = [s for s in all_semesters if s.is_active]
            other_semesters = [s for s in all_semesters if not s.is_active]

            # 当前学期排在前面，其他学期按开始日期倒序
            sorted_semesters = current_semesters + other_semesters

            logger.info(
                f"返回 {len(sorted_semesters)} 个学期，当前学期: {len(current_semesters)} 个"
            )

            return sorted_semesters

        except Exception as e:
            logger.error(f"获取排序学期列表失败: {str(e)}")
            # 如果出错，返回基本排序
            return list(Semester.objects.all().order_by("-start_date"))

    def is_semester_current(self, semester: Semester, current_date: date = None) -> bool:
        """检查指定学期是否为当前学期

        Args:
            semester: 要检查的学期
            current_date: 当前日期，默认为今天

        Returns:
            是否为当前学期
        """
        if current_date is None:
            current_date = date.today()

        return semester.start_date <= current_date <= semester.end_date

    def get_semester_status_info(self, semester: Semester, current_date: date = None) -> dict:
        """获取学期状态信息

        Args:
            semester: 学期对象
            current_date: 当前日期，默认为今天

        Returns:
            包含学期状态信息的字典
        """
        if current_date is None:
            current_date = date.today()

        is_current = self.is_semester_current(semester, current_date)

        # 计算学期状态
        if is_current:
            status = "current"
            status_text = "当前学期"
            status_class = "current"
        elif semester.end_date < current_date:
            status = "past"
            status_text = "已结束"
            status_class = "past"
        elif semester.start_date > current_date:
            status = "future"
            status_text = "未开始"
            status_class = "future"
        else:
            status = "unknown"
            status_text = "未知"
            status_class = "unknown"

        # 计算时间信息
        days_to_start = (semester.start_date - current_date).days
        days_to_end = (semester.end_date - current_date).days

        return {
            "status": status,
            "status_text": status_text,
            "status_class": status_class,
            "is_current": is_current,
            "is_active_in_db": semester.is_active,
            "days_to_start": days_to_start,
            "days_to_end": days_to_end,
            "needs_sync": is_current != semester.is_active,  # 数据库状态是否需要同步
        }

    def sync_all_semester_status(self) -> dict:
        """同步所有学期的状态

        检查并修正所有学期的 is_active 状态。

        Returns:
            同步结果统计
        """
        logger.info("开始同步所有学期状态")

        try:
            with transaction.atomic():
                current_date = date.today()
                all_semesters = Semester.objects.all()

                updated_count = 0
                current_semester = None

                for semester in all_semesters:
                    is_current = self.is_semester_current(semester, current_date)

                    if is_current:
                        current_semester = semester
                        if not semester.is_active:
                            semester.is_active = True
                            semester.save()
                            updated_count += 1
                            logger.info(f"将学期 '{semester.name}' 设置为活跃")
                    else:
                        if semester.is_active:
                            semester.is_active = False
                            semester.save()
                            updated_count += 1
                            logger.info(f"将学期 '{semester.name}' 设置为非活跃")

                result = {
                    "total_semesters": all_semesters.count(),
                    "updated_count": updated_count,
                    "current_semester": current_semester.name if current_semester else None,
                    "success": True,
                }

                logger.info(f"学期状态同步完成: {result}")
                return result

        except Exception as e:
            logger.error(f"同步学期状态失败: {str(e)}")
            return {"success": False, "error": str(e)}
