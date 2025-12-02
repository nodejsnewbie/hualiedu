"""
清除缓存管理命令

用法:
    python manage.py clear_cache                    # 清除所有缓存
    python manage.py clear_cache --type file_count  # 清除文件数量缓存
    python manage.py clear_cache --user 1           # 清除指定用户的缓存
    python manage.py clear_cache --tenant 1         # 清除指定租户的缓存
"""

from django.core.management.base import BaseCommand

from grading.cache_manager import CacheManager, clear_all_cache


class Command(BaseCommand):
    help = "清除系统缓存"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=[
                "all",
                "file_count",
                "dir_tree",
                "file_content",
                "file_metadata",
                "comment_template",
                "course_list",
                "class_list",
            ],
            default="all",
            help="缓存类型",
        )
        parser.add_argument(
            "--user",
            type=int,
            help="用户ID（清除指定用户的缓存）",
        )
        parser.add_argument(
            "--tenant",
            type=int,
            help="租户ID（清除指定租户的缓存）",
        )

    def handle(self, *args, **options):
        cache_type = options["type"]
        user_id = options.get("user")
        tenant_id = options.get("tenant")

        # 创建缓存管理器
        cache_manager = CacheManager(user_id=user_id, tenant_id=tenant_id)

        # 根据选项清除缓存
        if user_id:
            self.stdout.write(f"清除用户 {user_id} 的缓存...")
            cache_manager.clear_user_cache()
            self.stdout.write(self.style.SUCCESS(f"✓ 已清除用户 {user_id} 的所有缓存"))
        elif tenant_id:
            self.stdout.write(f"清除租户 {tenant_id} 的缓存...")
            cache_manager.clear_tenant_cache()
            self.stdout.write(self.style.SUCCESS(f"✓ 已清除租户 {tenant_id} 的所有缓存"))
        elif cache_type == "all":
            self.stdout.write("清除所有缓存...")
            clear_all_cache()
            self.stdout.write(self.style.SUCCESS("✓ 已清除所有缓存"))
        elif cache_type == "file_count":
            self.stdout.write("清除文件数量缓存...")
            cache_manager.clear_file_count()
            self.stdout.write(self.style.SUCCESS("✓ 已清除文件数量缓存"))
        elif cache_type == "dir_tree":
            self.stdout.write("清除目录树缓存...")
            cache_manager.clear_dir_tree()
            self.stdout.write(self.style.SUCCESS("✓ 已清除目录树缓存"))
        elif cache_type == "file_content":
            self.stdout.write("清除文件内容缓存...")
            cache_manager.clear_file_content()
            self.stdout.write(self.style.SUCCESS("✓ 已清除文件内容缓存"))
        elif cache_type == "file_metadata":
            self.stdout.write("清除文件元数据缓存...")
            cache_manager.clear_file_metadata()
            self.stdout.write(self.style.SUCCESS("✓ 已清除文件元数据缓存"))
        elif cache_type == "comment_template":
            self.stdout.write("清除评价模板缓存...")
            cache_manager.clear_comment_templates()
            self.stdout.write(self.style.SUCCESS("✓ 已清除评价模板缓存"))
        elif cache_type == "course_list":
            self.stdout.write("清除课程列表缓存...")
            cache_manager.clear_course_list()
            self.stdout.write(self.style.SUCCESS("✓ 已清除课程列表缓存"))
        elif cache_type == "class_list":
            self.stdout.write("清除班级列表缓存...")
            cache_manager.clear_class_list()
            self.stdout.write(self.style.SUCCESS("✓ 已清除班级列表缓存"))

        # 显示缓存统计信息
        stats = cache_manager.get_cache_stats()
        self.stdout.write("\n缓存配置信息:")
        self.stdout.write(f"  缓存后端: {stats['cache_backend']}")
        self.stdout.write(f"  超时设置:")
        for key, value in stats["timeouts"].items():
            self.stdout.write(f"    - {key}: {value}秒")
        self.stdout.write(f"  性能阈值:")
        for key, value in stats["thresholds"].items():
            self.stdout.write(f"    - {key}: {value}")
