"""
学期相关的Django模板标签

提供在模板中使用的学期状态和信息标签。
"""

from django import template
from django.utils.safestring import mark_safe

from grading.services.semester_status import semester_status_service

register = template.Library()


@register.simple_tag
def get_semester_status():
    """获取当前学期状态"""
    try:
        return semester_status_service.get_comprehensive_status()
    except Exception:
        return None


@register.simple_tag
def get_dashboard_info():
    """获取仪表板信息"""
    try:
        return semester_status_service.get_dashboard_info()
    except Exception:
        return {
            "current_status": "状态未知",
            "current_semester": None,
            "is_vacation": False,
            "vacation_type": "",
            "next_semester": None,
            "days_to_next": None,
        }


@register.simple_tag
def get_simple_status():
    """获取简单状态文本"""
    try:
        return semester_status_service.get_simple_status()
    except Exception:
        return "状态未知"


@register.inclusion_tag("semester_status_widget.html")
def semester_status_widget():
    """学期状态小部件"""
    try:
        dashboard_info = semester_status_service.get_dashboard_info()
        return {"dashboard": dashboard_info}
    except Exception:
        return {"dashboard": None}


@register.inclusion_tag("semester_timeline_widget.html")
def semester_timeline_widget():
    """学期时间线小部件"""
    try:
        status = semester_status_service.get_comprehensive_status()
        return {
            "timeline": status.get("timeline", []),
            "current_semester": status.get("current_semester"),
            "next_semester": status.get("next_semester"),
            "previous_semester": status.get("previous_semester"),
        }
    except Exception:
        return {"timeline": [], "current_semester": None}


@register.filter
def semester_progress_color(progress):
    """根据学期进度返回颜色"""
    try:
        progress = float(progress)
        if progress < 25:
            return "success"  # 绿色 - 学期初
        elif progress < 50:
            return "info"  # 蓝色 - 学期前期
        elif progress < 75:
            return "warning"  # 黄色 - 学期中后期
        else:
            return "danger"  # 红色 - 学期末
    except (ValueError, TypeError):
        return "secondary"


@register.filter
def vacation_icon(vacation_type):
    """根据假期类型返回图标"""
    icons = {"winter": "❄️", "summer": "☀️", "intersemester": "🏖️", "unknown": "📅", "none": "🎓"}
    return icons.get(vacation_type, "📅")


@register.filter
def days_to_text(days):
    """将天数转换为友好的文本"""
    try:
        days = int(days)
        if days == 0:
            return "今天"
        elif days == 1:
            return "明天"
        elif days < 7:
            return f"{days}天"
        elif days < 30:
            weeks = round(days / 7, 1)
            return f"{weeks}周"
        elif days < 365:
            months = round(days / 30, 1)
            return f"{months}个月"
        else:
            years = round(days / 365, 1)
            return f"{years}年"
    except (ValueError, TypeError):
        return str(days)


@register.filter
def semester_phase_text(phase):
    """学期阶段文本"""
    phase_texts = {
        "beginning": "学期初",
        "early": "前期",
        "middle": "中期",
        "late": "后期",
        "ending": "学期末",
    }
    return phase_texts.get(phase, phase)
