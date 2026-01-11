"""
学期管理Django命令

提供学期相关的管理命令，包括：
- 创建学期
- 同步学期状态
- 初始化默认模板
- 数据验证和修复
"""

import json
from datetime import date, datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from grading.exceptions import SemesterError
from grading.models import Semester, SemesterTemplate
from grading.services.semester_auto_creator import SemesterAutoCreator
from grading.services.semester_config import config_manager, template_manager
from grading.services.semester_manager import SemesterManager


class Command(BaseCommand):
    help = "学期管理命令"

    def add_arguments(self, parser):
        """添加命令参数"""
        subparsers = parser.add_subparsers(dest="action", help="可用操作")

        # 同步学期状态
        sync_parser = subparsers.add_parser("sync", help="同步所有学期状态")
        sync_parser.add_argument(
            "--dry-run", action="store_true", help="仅显示将要执行的操作，不实际修改数据"
        )

        # 创建当前学期
        create_parser = subparsers.add_parser("create-current", help="创建当前学期")
        create_parser.add_argument("--date", type=str, help="指定日期 (YYYY-MM-DD)，默认为今天")
        create_parser.add_argument(
            "--force", action="store_true", help="强制创建，即使已存在当前学期"
        )

        # 初始化默认模板
        init_parser = subparsers.add_parser("init-templates", help="初始化默认学期模板")
        init_parser.add_argument("--force", action="store_true", help="强制重新创建模板")

        # 验证数据
        validate_parser = subparsers.add_parser("validate", help="验证学期数据")
        validate_parser.add_argument("--fix", action="store_true", help="自动修复发现的问题")

        # 列出学期
        list_parser = subparsers.add_parser("list", help="列出所有学期")
        list_parser.add_argument(
            "--format", choices=["table", "json"], default="table", help="输出格式"
        )
        list_parser.add_argument("--active-only", action="store_true", help="仅显示活跃学期")

        # 配置管理
        config_parser = subparsers.add_parser("config", help="配置管理")
        config_parser.add_argument("--show", action="store_true", help="显示当前配置")
        config_parser.add_argument("--validate", action="store_true", help="验证配置")
        config_parser.add_argument("--reload", action="store_true", help="重新加载配置")

        # 统计信息
        stats_parser = subparsers.add_parser("stats", help="显示学期统计信息")

    def handle(self, *args, **options):
        """处理命令"""
        action = options.get("action")

        if not action:
            self.print_help("manage.py", "semester_management")
            return

        try:
            if action == "sync":
                self.handle_sync(options)
            elif action == "create-current":
                self.handle_create_current(options)
            elif action == "init-templates":
                self.handle_init_templates(options)
            elif action == "validate":
                self.handle_validate(options)
            elif action == "list":
                self.handle_list(options)
            elif action == "config":
                self.handle_config(options)
            elif action == "stats":
                self.handle_stats(options)
            else:
                raise CommandError(f"未知操作: {action}")

        except SemesterError as e:
            raise CommandError(f"学期操作失败: {e.message}")
        except Exception as e:
            raise CommandError(f"命令执行失败: {str(e)}")

    def handle_sync(self, options):
        """处理同步学期状态"""
        dry_run = options.get("dry_run", False)

        self.stdout.write("正在同步学期状态...")

        manager = SemesterManager()

        if dry_run:
            self.stdout.write(self.style.WARNING("这是预演模式，不会实际修改数据"))
            # 在预演模式下，我们只显示当前状态
            current_semester = manager.get_current_semester()
            if current_semester:
                self.stdout.write(f"当前学期: {current_semester.name}")
            else:
                self.stdout.write("未检测到当前学期")
        else:
            result = manager.sync_all_semester_status()

            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'同步完成: 总共 {result["total_semesters"]} 个学期，'
                        f'更新了 {result["updated_count"]} 个学期'
                    )
                )
                if result["current_semester"]:
                    self.stdout.write(f'当前学期: {result["current_semester"]}')
            else:
                raise CommandError(f'同步失败: {result["error"]}')

    def handle_create_current(self, options):
        """处理创建当前学期"""
        date_str = options.get("date")
        force = options.get("force", False)

        # 解析日期
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise CommandError(f"无效的日期格式: {date_str}，请使用 YYYY-MM-DD")
        else:
            target_date = date.today()

        self.stdout.write(f"正在为日期 {target_date} 创建学期...")

        # 检查是否已存在当前学期
        if not force:
            manager = SemesterManager()
            existing = manager.get_current_semester(target_date)
            if existing:
                self.stdout.write(self.style.WARNING(f"已存在当前学期: {existing.name}"))
                return

        # 创建学期
        auto_creator = SemesterAutoCreator()
        new_semester = auto_creator.check_and_create_current_semester(target_date)

        if new_semester:
            self.stdout.write(self.style.SUCCESS(f"成功创建学期: {new_semester.name}"))
        else:
            self.stdout.write("未创建新学期（可能不需要或已存在）")

    def handle_init_templates(self, options):
        """处理初始化默认模板"""
        force = options.get("force", False)

        self.stdout.write("正在初始化默认学期模板...")

        if force:
            # 删除现有模板
            deleted_count = SemesterTemplate.objects.filter(is_active=True).count()
            SemesterTemplate.objects.filter(is_active=True).delete()
            self.stdout.write(f"删除了 {deleted_count} 个现有模板")

        result = template_manager.ensure_default_templates()

        self.stdout.write(self.style.SUCCESS(f'模板初始化完成: {result["message"]}'))

    def handle_validate(self, options):
        """处理数据验证"""
        fix = options.get("fix", False)

        self.stdout.write("正在验证学期数据...")

        issues = []

        # 验证配置
        config_result = config_manager.validate_config()
        if not config_result["valid"]:
            issues.extend([f"配置错误: {error}" for error in config_result["errors"]])

        # 验证学期数据
        semesters = Semester.objects.all()
        for semester in semesters:
            # 检查日期范围
            if semester.start_date >= semester.end_date:
                issue = f"学期 {semester.name} 的日期范围无效: {semester.start_date} >= {semester.end_date}"
                issues.append(issue)

                if fix:
                    # 尝试修复：设置合理的结束日期
                    from datetime import timedelta

                    semester.end_date = semester.start_date + timedelta(weeks=16)
                    semester.save()
                    self.stdout.write(f"已修复: {issue}")

        # 检查重复的活跃学期
        active_semesters = Semester.objects.filter(is_active=True)
        if active_semesters.count() > 1:
            issue = f"发现多个活跃学期: {[s.name for s in active_semesters]}"
            issues.append(issue)

            if fix:
                # 修复：只保留最新的活跃学期
                manager = SemesterManager()
                manager.sync_all_semester_status()
                self.stdout.write(f"已修复: {issue}")

        # 输出结果
        if issues:
            self.stdout.write(self.style.WARNING(f"发现 {len(issues)} 个问题:"))
            for issue in issues:
                self.stdout.write(f"  - {issue}")

            if not fix:
                self.stdout.write("使用 --fix 参数自动修复问题")
        else:
            self.stdout.write(self.style.SUCCESS("数据验证通过，未发现问题"))

    def handle_list(self, options):
        """处理列出学期"""
        format_type = options.get("format", "table")
        active_only = options.get("active_only", False)

        # 获取学期数据
        manager = SemesterManager()
        semesters = manager.get_sorted_semesters_for_display()

        if active_only:
            semesters = [s for s in semesters if s.is_active]

        if format_type == "json":
            # JSON格式输出
            data = []
            for semester in semesters:
                status_info = manager.get_semester_status_info(semester)
                data.append(
                    {
                        "id": semester.id,
                        "name": semester.name,
                        "start_date": str(semester.start_date),
                        "end_date": str(semester.end_date),
                        "is_active": semester.is_active,
                        "auto_created": semester.auto_created,
                        "season": semester.season,
                        "status": status_info["status_text"],
                    }
                )

            self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            self.stdout.write("学期列表:")
            self.stdout.write("-" * 80)

            header = (
                f'{"ID":<4} {"名称":<20} {"开始日期":<12} {"结束日期":<12} {"状态":<8} {"类型":<8}'
            )
            self.stdout.write(header)
            self.stdout.write("-" * 80)

            for semester in semesters:
                status_info = manager.get_semester_status_info(semester)
                auto_type = "自动" if semester.auto_created else "手动"

                row = (
                    f"{semester.id:<4} "
                    f"{semester.name:<20} "
                    f"{semester.start_date:<12} "
                    f"{semester.end_date:<12} "
                    f'{status_info["status_text"]:<8} '
                    f"{auto_type:<8}"
                )

                if semester.is_active:
                    self.stdout.write(self.style.SUCCESS(row))
                else:
                    self.stdout.write(row)

    def handle_config(self, options):
        """处理配置管理"""
        show = options.get("show", False)
        validate = options.get("validate", False)
        reload = options.get("reload", False)

        if show:
            config = config_manager.get_all_config()
            self.stdout.write("当前配置:")
            for key, value in config.items():
                self.stdout.write(f"  {key}: {value}")

        if validate:
            result = config_manager.validate_config()
            if result["valid"]:
                self.stdout.write(self.style.SUCCESS("配置验证通过"))
            else:
                self.stdout.write(self.style.ERROR("配置验证失败:"))
                for error in result["errors"]:
                    self.stdout.write(f"  - {error}")
                for warning in result["warnings"]:
                    self.stdout.write(self.style.WARNING(f"  - {warning}"))

        if reload:
            config_manager.reload_config()
            self.stdout.write(self.style.SUCCESS("配置已重新加载"))

    def handle_stats(self, options):
        """处理统计信息"""
        self.stdout.write("学期统计信息:")
        self.stdout.write("-" * 40)

        # 基本统计
        total_semesters = Semester.objects.count()
        active_semesters = Semester.objects.filter(is_active=True).count()
        auto_created = Semester.objects.filter(auto_created=True).count()

        self.stdout.write(f"总学期数: {total_semesters}")
        self.stdout.write(f"活跃学期数: {active_semesters}")
        self.stdout.write(f"自动创建学期数: {auto_created}")
        self.stdout.write(f"手动创建学期数: {total_semesters - auto_created}")

        if total_semesters > 0:
            auto_percentage = (auto_created / total_semesters) * 100
            self.stdout.write(f"自动创建比例: {auto_percentage:.1f}%")

        # 按季节统计
        spring_count = Semester.objects.filter(season="spring").count()
        autumn_count = Semester.objects.filter(season="autumn").count()
        unknown_season = total_semesters - spring_count - autumn_count

        self.stdout.write(f"春季学期: {spring_count}")
        self.stdout.write(f"秋季学期: {autumn_count}")
        if unknown_season > 0:
            self.stdout.write(f"未知季节: {unknown_season}")

        # 模板统计
        template_count = SemesterTemplate.objects.filter(is_active=True).count()
        self.stdout.write(f"活跃模板数: {template_count}")

        # 当前学期信息
        manager = SemesterManager()
        current_semester = manager.get_current_semester()
        if current_semester:
            self.stdout.write(f"当前学期: {current_semester.name}")
        else:
            self.stdout.write("当前学期: 无")
