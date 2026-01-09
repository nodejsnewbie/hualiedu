import os
import sys
import threading

from django.apps import AppConfig


class GradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grading"
    verbose_name = "作业评分系统"

    def ready(self):
        if os.environ.get("RUN_STARTUP_SYNC") == "0":
            return

        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        start_args = {"runserver", "gunicorn", "uwsgi", "daphne", "uvicorn"}
        if not any(arg in sys.argv for arg in start_args):
            return

        from grading.startup_sync import sync_all_git_repositories

        threading.Thread(target=sync_all_git_repositories, daemon=True).start()
