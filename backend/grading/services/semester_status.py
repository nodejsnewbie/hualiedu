"""
学期状态服务模块

提供学期状态的综合显示功能，包括：
- 当前学期识别
- 寒暑假状态判断
- 下一个学期预测
- 学期间隙分析
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Q

from grading.exceptions import SemesterDetectionError, handle_semester_exceptions
from grading.models import Semester
from grading.services.semester_detector import CurrentSemesterDetector
from grading.services.semester_manager import SemesterManager

# 配置日志
logger = logging.getLogger(__name__)


class SemesterStatusService:
    """学期状态服务

    提供完整的学期状态信息，包括当前状态、假期判断、下一学期等。
    """

    def __init__(self):
        """初始化学期状态服务"""
        self.detector = CurrentSemesterDetector()
        self.manager = SemesterManager()

    @handle_semester_exceptions(default_return={})
    def get_comprehensive_status(self, current_date: date = None) -> Dict[str, Any]:
        """获取综合学期状态

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            包含完整学期状态信息的字典
        """
        if current_date is None:
            current_date = date.today()

        logger.info(f"获取日期 {current_date} 的综合学期状态")

        # 获取当前学期
        current_semester = self.manager.get_current_semester(current_date)

        # 获取所有相关学期
        all_semesters = self._get_relevant_semesters(current_date)

        # 分析学期状态
        status_info = self._analyze_semester_status(current_date, current_semester, all_semesters)

        # 获取假期信息
        vacation_info = self._analyze_vacation_status(current_date, all_semesters)

        # 获取下一学期信息
        next_semester_info = self._get_next_semester_info(current_date, all_semesters)

        # 获取上一学期信息
        previous_semester_info = self._get_previous_semester_info(current_date, all_semesters)

        # 构建综合状态
        comprehensive_status = {
            "current_date": current_date,
            "current_semester": (
                self._format_semester_info(current_semester, current_date)
                if current_semester
                else None
            ),
            "status": status_info,
            "vacation": vacation_info,
            "next_semester": next_semester_info,
            "previous_semester": previous_semester_info,
            "timeline": self._build_semester_timeline(current_date, all_semesters),
            "summary": self._build_status_summary(status_info, vacation_info, current_semester),
        }

        logger.info(f"学期状态分析完成: {comprehensive_status['summary']['text']}")

        return comprehensive_status

    def _get_relevant_semesters(self, current_date: date, range_years: int = 2) -> List[Semester]:
        """获取相关学期

        Args:
            current_date: 当前日期
            range_years: 查找范围（年）

        Returns:
            相关学期列表
        """
        start_year = current_date.year - range_years
        end_year = current_date.year + range_years

        semesters = Semester.objects.filter(
            Q(start_date__year__gte=start_year, start_date__year__lte=end_year)
            | Q(end_date__year__gte=start_year, end_date__year__lte=end_year)
        ).order_by("start_date")

        return list(semesters)

    def _analyze_semester_status(
        self,
        current_date: date,
        current_semester: Optional[Semester],
        all_semesters: List[Semester],
    ) -> Dict[str, Any]:
        """分析学期状态

        Args:
            current_date: 当前日期
            current_semester: 当前学期
            all_semesters: 所有相关学期

        Returns:
            学期状态信息
        """
        if current_semester:
            # 在学期中
            days_since_start = (current_date - current_semester.start_date).days
            days_to_end = (current_semester.end_date - current_date).days
            total_days = (current_semester.end_date - current_semester.start_date).days
            progress_percentage = (days_since_start / total_days * 100) if total_days > 0 else 0

            return {
                "type": "in_semester",
                "text": "学期中",
                "description": f"当前在 {current_semester.name} 中",
                "days_since_start": days_since_start,
                "days_to_end": days_to_end,
                "total_days": total_days,
                "progress_percentage": round(progress_percentage, 1),
                "phase": self._determine_semester_phase(progress_percentage),
            }
        else:
            # 不在学期中，可能在假期
            return {
                "type": "not_in_semester",
                "text": "非学期时间",
                "description": "当前不在任何学期时间范围内",
                "phase": "vacation",
            }

    def _analyze_vacation_status(
        self, current_date: date, all_semesters: List[Semester]
    ) -> Dict[str, Any]:
        """分析假期状态

        Args:
            current_date: 当前日期
            all_semesters: 所有相关学期

        Returns:
            假期状态信息
        """
        # 查找当前日期前后的学期
        previous_semester = None
        next_semester = None

        for semester in all_semesters:
            if semester.end_date < current_date:
                if not previous_semester or semester.end_date > previous_semester.end_date:
                    previous_semester = semester
            elif semester.start_date > current_date:
                if not next_semester or semester.start_date < next_semester.start_date:
                    next_semester = semester

        # 判断假期类型
        vacation_type = self._determine_vacation_type(
            current_date, previous_semester, next_semester
        )

        if vacation_type == "none":
            return {
                "is_vacation": False,
                "type": "none",
                "text": "非假期",
                "description": "当前在学期时间内",
            }

        # 计算假期长度和剩余时间
        vacation_info = {
            "is_vacation": True,
            "type": vacation_type,
            "text": self._get_vacation_text(vacation_type),
            "description": self._get_vacation_description(
                vacation_type, previous_semester, next_semester
            ),
        }

        # 添加时间信息
        if previous_semester:
            days_since_end = (current_date - previous_semester.end_date).days
            vacation_info["days_since_last_semester"] = days_since_end

        if next_semester:
            days_to_start = (next_semester.start_date - current_date).days
            vacation_info["days_to_next_semester"] = days_to_start

        # 计算假期总长度
        if previous_semester and next_semester:
            total_vacation_days = (next_semester.start_date - previous_semester.end_date).days
            vacation_progress = (
                (days_since_end / total_vacation_days * 100) if total_vacation_days > 0 else 0
            )
            vacation_info["total_vacation_days"] = total_vacation_days
            vacation_info["vacation_progress_percentage"] = round(vacation_progress, 1)

        return vacation_info

    def _determine_vacation_type(
        self,
        current_date: date,
        previous_semester: Optional[Semester],
        next_semester: Optional[Semester],
    ) -> str:
        """确定假期类型

        Args:
            current_date: 当前日期
            previous_semester: 上一学期
            next_semester: 下一学期

        Returns:
            假期类型字符串
        """
        # 如果在学期中，不是假期
        current_semester = self.manager.get_current_semester(current_date)
        if current_semester:
            return "none"

        # 根据月份和学期情况判断假期类型
        month = current_date.month

        if previous_semester and next_semester:
            # 有前后学期，根据季节判断
            if previous_semester.season == "autumn" and next_semester.season == "spring":
                return "winter"  # 寒假
            elif previous_semester.season == "spring" and next_semester.season == "autumn":
                return "summer"  # 暑假

        # 根据月份推断
        # 注意：根据新的学期安排，寒假和暑假时间需要调整
        if month in [8]:
            return "summer"  # 暑假（7月底-8月底）
        elif month in [2]:
            # 2月可能是寒假末期或学期末，需要更精确判断
            if current_date.day > 20:  # 2月下旬可能是寒假
                return "winter"
            else:
                return "intersemester"
        elif month in [7]:
            # 7月底可能是暑假开始
            if current_date.day > 25:  # 7月底
                return "summer"
            else:
                return "intersemester"
        else:
            return "intersemester"

    def _get_vacation_text(self, vacation_type: str) -> str:
        """获取假期文本"""
        vacation_texts = {
            "winter": "寒假",
            "summer": "暑假",
            "intersemester": "学期间隙",
            "unknown": "假期",
            "none": "非假期",
        }
        return vacation_texts.get(vacation_type, "未知")

    def _get_vacation_description(
        self,
        vacation_type: str,
        previous_semester: Optional[Semester],
        next_semester: Optional[Semester],
    ) -> str:
        """获取假期描述"""
        if vacation_type == "winter":
            return "寒假期间，春节假期"
        elif vacation_type == "summer":
            return "暑假期间，夏季假期"
        elif vacation_type == "intersemester":
            return "学期间的短暂间隙"
        else:
            return "非学期时间"

    def _get_next_semester_info(
        self, current_date: date, all_semesters: List[Semester]
    ) -> Optional[Dict[str, Any]]:
        """获取下一学期信息

        Args:
            current_date: 当前日期
            all_semesters: 所有相关学期

        Returns:
            下一学期信息字典
        """
        # 查找下一个学期
        next_semester = None
        for semester in all_semesters:
            if semester.start_date > current_date:
                if not next_semester or semester.start_date < next_semester.start_date:
                    next_semester = semester

        if not next_semester:
            return None

        days_to_start = (next_semester.start_date - current_date).days

        return {
            "semester": self._format_semester_info(next_semester, current_date),
            "days_to_start": days_to_start,
            "weeks_to_start": round(days_to_start / 7, 1),
            "start_date": next_semester.start_date,
            "is_soon": days_to_start <= 30,  # 30天内算即将开始
            "countdown_text": self._format_countdown_text(days_to_start, "开始"),
        }

    def _get_previous_semester_info(
        self, current_date: date, all_semesters: List[Semester]
    ) -> Optional[Dict[str, Any]]:
        """获取上一学期信息

        Args:
            current_date: 当前日期
            all_semesters: 所有相关学期

        Returns:
            上一学期信息字典
        """
        # 查找上一个学期
        previous_semester = None
        for semester in all_semesters:
            if semester.end_date < current_date:
                if not previous_semester or semester.end_date > previous_semester.end_date:
                    previous_semester = semester

        if not previous_semester:
            return None

        days_since_end = (current_date - previous_semester.end_date).days

        return {
            "semester": self._format_semester_info(previous_semester, current_date),
            "days_since_end": days_since_end,
            "weeks_since_end": round(days_since_end / 7, 1),
            "end_date": previous_semester.end_date,
            "is_recent": days_since_end <= 30,  # 30天内算刚结束
            "elapsed_text": self._format_countdown_text(days_since_end, "结束"),
        }

    def _format_semester_info(self, semester: Semester, current_date: date) -> Dict[str, Any]:
        """格式化学期信息

        Args:
            semester: 学期对象
            current_date: 当前日期

        Returns:
            格式化的学期信息
        """
        status_info = self.manager.get_semester_status_info(semester, current_date)

        return {
            "id": semester.id,
            "name": semester.name,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "season": semester.season,
            "season_text": (
                "春季"
                if semester.season == "spring"
                else "秋季" if semester.season == "autumn" else "未知"
            ),
            "auto_created": semester.auto_created,
            "is_active": semester.is_active,
            "status": status_info["status_text"],
            "duration_days": (semester.end_date - semester.start_date).days,
            "duration_weeks": round((semester.end_date - semester.start_date).days / 7, 1),
        }

    def _determine_semester_phase(self, progress_percentage: float) -> str:
        """确定学期阶段

        Args:
            progress_percentage: 进度百分比

        Returns:
            学期阶段字符串
        """
        if progress_percentage < 20:
            return "beginning"  # 学期初
        elif progress_percentage < 40:
            return "early"  # 学期前期
        elif progress_percentage < 60:
            return "middle"  # 学期中期
        elif progress_percentage < 80:
            return "late"  # 学期后期
        else:
            return "ending"  # 学期末

    def _format_countdown_text(self, days: int, action: str) -> str:
        """格式化倒计时文本

        Args:
            days: 天数
            action: 动作（如"开始"、"结束"）

        Returns:
            格式化的倒计时文本
        """
        if days == 0:
            return f"今天{action}"
        elif days == 1:
            return f"明天{action}"
        elif days < 7:
            return f"{days}天后{action}"
        elif days < 30:
            weeks = round(days / 7, 1)
            return f"{weeks}周后{action}"
        elif days < 365:
            months = round(days / 30, 1)
            return f"{months}个月后{action}"
        else:
            years = round(days / 365, 1)
            return f"{years}年后{action}"

    def _build_semester_timeline(
        self, current_date: date, all_semesters: List[Semester]
    ) -> List[Dict[str, Any]]:
        """构建学期时间线

        Args:
            current_date: 当前日期
            all_semesters: 所有相关学期

        Returns:
            时间线列表
        """
        timeline = []

        # 按时间排序
        sorted_semesters = sorted(all_semesters, key=lambda s: s.start_date)

        for semester in sorted_semesters:
            # 判断与当前日期的关系
            if semester.end_date < current_date:
                relation = "past"
            elif semester.start_date > current_date:
                relation = "future"
            else:
                relation = "current"

            timeline.append(
                {
                    "semester": self._format_semester_info(semester, current_date),
                    "relation": relation,
                    "is_current": relation == "current",
                }
            )

        return timeline

    def _build_status_summary(
        self,
        status_info: Dict[str, Any],
        vacation_info: Dict[str, Any],
        current_semester: Optional[Semester],
    ) -> Dict[str, Any]:
        """构建状态摘要

        Args:
            status_info: 状态信息
            vacation_info: 假期信息
            current_semester: 当前学期

        Returns:
            状态摘要字典
        """
        if current_semester:
            # 在学期中
            phase_texts = {
                "beginning": "刚开始",
                "early": "前期",
                "middle": "中期",
                "late": "后期",
                "ending": "即将结束",
            }
            phase_text = phase_texts.get(status_info.get("phase", ""), "")

            summary_text = f"当前在{current_semester.name}中（{phase_text}）"

            if status_info.get("days_to_end", 0) <= 7:
                summary_text += "，即将结束"
            elif status_info.get("days_since_start", 0) <= 7:
                summary_text += "，刚刚开始"
        else:
            # 在假期中
            if vacation_info["is_vacation"]:
                summary_text = f"当前在{vacation_info['text']}中"

                if vacation_info.get("days_to_next_semester", 0) <= 7:
                    summary_text += "，即将开学"
            else:
                summary_text = "当前不在学期时间内"

        return {
            "text": summary_text,
            "type": status_info["type"],
            "is_semester": current_semester is not None,
            "is_vacation": vacation_info["is_vacation"],
        }

    def get_simple_status(self, current_date: date = None) -> str:
        """获取简单状态文本

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            简单的状态文本
        """
        try:
            status = self.get_comprehensive_status(current_date)
            return status["summary"]["text"]
        except Exception as e:
            logger.error(f"获取简单状态失败: {str(e)}")
            return "状态未知"

    def get_dashboard_info(self, current_date: date = None) -> Dict[str, Any]:
        """获取仪表板信息

        Args:
            current_date: 当前日期，默认为今天

        Returns:
            适合仪表板显示的信息
        """
        try:
            status = self.get_comprehensive_status(current_date)

            dashboard_info = {
                "current_status": status["summary"]["text"],
                "current_semester": (
                    status["current_semester"]["name"] if status["current_semester"] else None
                ),
                "is_vacation": status["vacation"]["is_vacation"],
                "vacation_type": status["vacation"].get("text", ""),
                "next_semester": None,
                "days_to_next": None,
            }

            if status["next_semester"]:
                dashboard_info["next_semester"] = status["next_semester"]["semester"]["name"]
                dashboard_info["days_to_next"] = status["next_semester"]["days_to_start"]

            return dashboard_info

        except Exception as e:
            logger.error(f"获取仪表板信息失败: {str(e)}")
            return {
                "current_status": "状态未知",
                "current_semester": None,
                "is_vacation": False,
                "vacation_type": "",
                "next_semester": None,
                "days_to_next": None,
            }


# 全局学期状态服务实例
semester_status_service = SemesterStatusService()
