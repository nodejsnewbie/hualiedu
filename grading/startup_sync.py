import logging
import os

from django.utils import timezone

from grading.cache_manager import CacheManager
from grading.models import Repository
from grading.utils import GitHandler

logger = logging.getLogger(__name__)


def sync_all_git_repositories():
    """系统启动时同步一次所有 Git 仓库。"""
    repos = Repository.objects.filter(is_active=True, repo_type="git")
    if not repos.exists():
        return

    any_success = False
    for repo in repos:
        if not repo.can_sync():
            continue

        full_path = repo.get_full_path()
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"创建仓库根目录失败: {e}")

        try:
            if os.path.exists(full_path):
                success = GitHandler.pull_repo(full_path, repo.branch or None)
            else:
                success = GitHandler.clone_repo_remote(repo.url, full_path, repo.branch or None)
        except Exception as e:
            logger.warning(f"同步仓库失败: {repo.name}, error={e}")
            success = False

        if success:
            repo.last_sync = timezone.now()
            repo.save(update_fields=["last_sync"])
            any_success = True
            logger.info(f"启动同步成功: {repo.name}")
        else:
            logger.warning(f"启动同步失败: {repo.name}")

    if any_success:
        cache_manager = CacheManager()
        cache_manager.clear_dir_tree()
        cache_manager.clear_file_count()
        cache_manager.clear_file_content()
