"""
仓库管理服务模块

提供仓库的创建、配置和管理功能，包括：
- 创建Git仓库配置
- 创建文件系统仓库
- 生成目录名（处理重名）
- 验证Git连接
- 验证目录结构
- 列出仓库
"""

import logging
import os
import re
from typing import List, Optional, Tuple

from django.contrib.auth.models import User
from django.db import transaction

from grading.models import Class, Repository, Tenant

# 配置日志
logger = logging.getLogger(__name__)


class RepositoryService:
    """仓库管理服务

    负责仓库的创建、配置和管理，支持Git仓库和文件系统两种方式。
    """

    @transaction.atomic
    def create_git_repository(
        self,
        teacher: User,
        class_obj: Class,
        name: str,
        git_url: str,
        branch: str = "main",
        username: str = "",
        password: str = "",
        description: str = "",
        tenant: Optional[Tenant] = None,
    ) -> Repository:
        """创建Git仓库配置

        Args:
            teacher: 仓库所有者（教师）
            class_obj: 关联的班级
            name: 仓库名称
            git_url: Git仓库URL
            branch: Git分支名称
            username: Git用户名（可选）
            password: Git密码（可选）
            description: 仓库描述
            tenant: 所属租户

        Returns:
            创建的仓库对象

        Raises:
            ValueError: 如果参数无效
        """
        # 验证必需参数
        if not name or not name.strip():
            raise ValueError("仓库名称不能为空")

        if not git_url or not git_url.strip():
            raise ValueError("Git仓库URL不能为空")

        if not teacher:
            raise ValueError("必须指定仓库所有者")

        if not class_obj:
            raise ValueError("必须指定关联的班级")

        # 如果没有提供租户，尝试从教师的用户配置中获取
        if not tenant and hasattr(teacher, "profile"):
            tenant = teacher.profile.tenant

        if not tenant:
            raise ValueError("无法确定租户信息")

        # 验证Git URL格式
        if not self._is_valid_git_url(git_url):
            raise ValueError(f"无效的Git仓库URL: {git_url}")

        # 创建Git仓库配置
        repository = Repository.objects.create(
            owner=teacher,
            tenant=tenant,
            class_obj=class_obj,
            name=name.strip(),
            repo_type="git",
            git_url=git_url.strip(),
            git_branch=branch.strip() if branch else "main",
            git_username=username.strip() if username else "",
            git_password=password,  # TODO: 加密存储
            url=git_url.strip(),  # 兼容旧字段
            branch=branch.strip() if branch else "main",  # 兼容旧字段
            description=description.strip() if description else "",
            is_active=True,
        )

        logger.info(
            f"创建Git仓库配置成功: {repository.name} "
            f"(URL: {git_url}, 分支: {branch}, 教师: {teacher.username}, 租户: {tenant.name})"
        )

        return repository

    @transaction.atomic
    def create_filesystem_repository(
        self,
        teacher: User,
        class_obj: Class,
        name: str,
        allocated_space_mb: int = 1024,
        description: str = "",
        tenant: Optional[Tenant] = None,
    ) -> Repository:
        """创建文件系统仓库

        Args:
            teacher: 仓库所有者（教师）
            class_obj: 关联的班级
            name: 仓库名称
            allocated_space_mb: 分配空间（MB）
            description: 仓库描述
            tenant: 所属租户

        Returns:
            创建的仓库对象

        Raises:
            ValueError: 如果参数无效
        """
        # 验证必需参数
        if not name or not name.strip():
            raise ValueError("仓库名称不能为空")

        if not teacher:
            raise ValueError("必须指定仓库所有者")

        if not class_obj:
            raise ValueError("必须指定关联的班级")

        # 如果没有提供租户，尝试从教师的用户配置中获取
        if not tenant and hasattr(teacher, "profile"):
            tenant = teacher.profile.tenant

        if not tenant:
            raise ValueError("无法确定租户信息")

        # 验证分配空间
        if allocated_space_mb <= 0:
            raise ValueError("分配空间必须大于0")

        # 生成唯一的目录名
        directory_name = self.generate_directory_name(teacher.username, name)

        # 创建文件系统仓库
        repository = Repository.objects.create(
            owner=teacher,
            tenant=tenant,
            class_obj=class_obj,
            name=name.strip(),
            repo_type="filesystem",
            filesystem_path=directory_name,
            allocated_space_mb=allocated_space_mb,
            path=directory_name,  # 兼容旧字段
            description=description.strip() if description else "",
            is_active=True,
        )

        # 创建物理目录
        full_path = repository.get_full_path()
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"创建仓库目录: {full_path}")
        except OSError as e:
            logger.error(f"创建仓库目录失败: {full_path}, 错误: {e}")
            # 回滚事务会自动删除数据库记录
            raise ValueError(f"创建仓库目录失败: {e}")

        logger.info(
            f"创建文件系统仓库成功: {repository.name} "
            f"(路径: {directory_name}, 空间: {allocated_space_mb}MB, "
            f"教师: {teacher.username}, 租户: {tenant.name})"
        )

        return repository

    def generate_directory_name(self, username: str, base_name: str = "") -> str:
        """生成目录名，处理重名情况

        规则：
        1. 基于用户名生成目录名
        2. 如果提供了base_name，使用 username_basename 格式
        3. 如果目录已存在，添加数字后缀（如 username_2, username_3）

        Args:
            username: 用户名
            base_name: 基础名称（可选）

        Returns:
            唯一的目录名
        """
        # 清理用户名和基础名称，只保留字母、数字、下划线和连字符
        clean_username = re.sub(r"[^\w-]", "_", username)

        if base_name:
            clean_base = re.sub(r"[^\w-]", "_", base_name)
            base_dir_name = f"{clean_username}_{clean_base}"
        else:
            base_dir_name = clean_username

        # 检查是否已存在同名仓库
        existing_repos = Repository.objects.filter(
            owner__username=username, filesystem_path__startswith=base_dir_name
        )

        if not existing_repos.exists():
            return base_dir_name

        # 如果存在，找到最大的数字后缀
        max_suffix = 0
        pattern = re.compile(rf"^{re.escape(base_dir_name)}_(\d+)$")

        for repo in existing_repos:
            path = repo.filesystem_path or repo.path
            if path == base_dir_name:
                max_suffix = max(max_suffix, 1)
            else:
                match = pattern.match(path)
                if match:
                    suffix = int(match.group(1))
                    max_suffix = max(max_suffix, suffix)

        # 生成新的目录名
        if max_suffix == 0:
            return f"{base_dir_name}_2"
        else:
            return f"{base_dir_name}_{max_suffix + 1}"

    def validate_git_connection(
        self, git_url: str, branch: str = "main", username: str = "", password: str = ""
    ) -> Tuple[bool, str]:
        """验证Git连接

        Args:
            git_url: Git仓库URL
            branch: 分支名称
            username: Git用户名（可选）
            password: Git密码（可选）

        Returns:
            (是否成功, 错误信息)
        """
        try:
            import git

            # 验证URL格式
            if not self._is_valid_git_url(git_url):
                return False, f"无效的Git仓库URL: {git_url}"

            # 尝试列出远程引用（不克隆整个仓库）
            # 这是一个轻量级的验证方法
            remote_refs = {}

            # 构建认证URL
            if username and password:
                # 解析URL并插入认证信息
                from urllib.parse import urlparse, urlunparse

                parsed = urlparse(git_url)
                if parsed.scheme in ["http", "https"]:
                    # 构建带认证的URL
                    netloc = f"{username}:{password}@{parsed.netloc}"
                    auth_url = urlunparse(
                        (
                            parsed.scheme,
                            netloc,
                            parsed.path,
                            parsed.params,
                            parsed.query,
                            parsed.fragment,
                        )
                    )
                    remote_refs = git.cmd.Git().ls_remote(auth_url)
                else:
                    # SSH URL，使用原始URL
                    remote_refs = git.cmd.Git().ls_remote(git_url)
            else:
                remote_refs = git.cmd.Git().ls_remote(git_url)

            # 检查分支是否存在
            if branch:
                branch_ref = f"refs/heads/{branch}"
                if branch_ref not in remote_refs and f"refs/remotes/origin/{branch}" not in str(
                    remote_refs
                ):
                    logger.warning(f"分支 {branch} 可能不存在于远程仓库")
                    # 不作为错误，因为分支可能稍后创建

            logger.info(f"Git连接验证成功: {git_url}")
            return True, ""

        except ImportError:
            error_msg = "GitPython未安装，无法验证Git连接"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Git连接验证失败: {str(e)}"
            logger.error(f"{error_msg} (URL: {git_url})")
            return False, error_msg

    def validate_directory_structure(self, repo_path: str) -> Tuple[bool, str, List[str]]:
        """验证目录结构

        验证目录是否符合"课程/班级/作业批次/学生作业"格式

        Args:
            repo_path: 仓库路径

        Returns:
            (是否有效, 错误信息, 建议修复步骤)
        """
        if not os.path.exists(repo_path):
            return False, f"目录不存在: {repo_path}", ["创建目录"]

        if not os.path.isdir(repo_path):
            return False, f"路径不是目录: {repo_path}", []

        # 检查目录结构
        # 期望结构：课程/班级/作业批次/学生作业
        issues = []
        suggestions = []

        try:
            # 列出顶层目录（课程）
            courses = [
                d
                for d in os.listdir(repo_path)
                if os.path.isdir(os.path.join(repo_path, d)) and not d.startswith(".")
            ]

            if not courses:
                issues.append("未找到课程目录")
                suggestions.append("在仓库根目录下创建课程目录")
                return False, "目录结构不符合规范: " + "; ".join(issues), suggestions

            # 检查每个课程目录
            for course in courses:
                course_path = os.path.join(repo_path, course)

                # 列出班级目录
                classes = [
                    d
                    for d in os.listdir(course_path)
                    if os.path.isdir(os.path.join(course_path, d)) and not d.startswith(".")
                ]

                if not classes:
                    issues.append(f"课程 '{course}' 下未找到班级目录")
                    suggestions.append(f"在 '{course}' 目录下创建班级目录")
                    continue

                # 检查每个班级目录
                for class_name in classes:
                    class_path = os.path.join(course_path, class_name)

                    # 列出作业批次目录
                    homeworks = [
                        d
                        for d in os.listdir(class_path)
                        if os.path.isdir(os.path.join(class_path, d)) and not d.startswith(".")
                    ]

                    if not homeworks:
                        issues.append(f"班级 '{course}/{class_name}' 下未找到作业批次目录")
                        suggestions.append(f"在 '{course}/{class_name}' 目录下创建作业批次目录")

            if issues:
                return (
                    False,
                    "目录结构部分不符合规范: " + "; ".join(issues),
                    suggestions,
                )

            logger.info(f"目录结构验证通过: {repo_path}")
            return True, "", []

        except PermissionError as e:
            error_msg = f"无权限访问目录: {e}"
            logger.error(error_msg)
            return False, error_msg, ["检查目录权限"]
        except Exception as e:
            error_msg = f"验证目录结构时出错: {e}"
            logger.error(error_msg)
            return False, error_msg, []

    def list_repositories(
        self, teacher: User, tenant: Optional[Tenant] = None, class_obj: Optional[Class] = None
    ) -> List[Repository]:
        """列出教师的所有仓库

        Args:
            teacher: 教师用户
            tenant: 租户（可选，用于额外过滤）
            class_obj: 班级（可选，用于过滤特定班级的仓库）

        Returns:
            仓库列表
        """
        # 基础查询：只返回该教师的仓库
        queryset = Repository.objects.filter(owner=teacher)

        # 如果提供了租户，额外过滤
        if tenant:
            queryset = queryset.filter(tenant=tenant)

        # 如果提供了班级，过滤特定班级
        if class_obj:
            queryset = queryset.filter(class_obj=class_obj)

        # 使用 select_related 优化查询
        queryset = queryset.select_related("owner", "tenant", "class_obj", "class_obj__course")

        # 按创建时间倒序排序
        repositories = list(queryset.order_by("-created_at"))

        logger.info(
            f"查询教师 {teacher.username} 的仓库，共 {len(repositories)} 个"
            + (f" (班级: {class_obj.name})" if class_obj else "")
        )

        return repositories

    def get_repository_by_id(self, repo_id: int, teacher: Optional[User] = None) -> Repository:
        """根据ID获取仓库

        Args:
            repo_id: 仓库ID
            teacher: 教师用户（可选，用于验证权限）

        Returns:
            仓库对象

        Raises:
            Repository.DoesNotExist: 如果仓库不存在或教师无权访问
        """
        queryset = Repository.objects.select_related("owner", "tenant", "class_obj")

        # 如果提供了教师，确保只能访问自己的仓库
        if teacher:
            queryset = queryset.filter(owner=teacher)

        repository = queryset.get(id=repo_id)

        return repository

    @transaction.atomic
    def update_repository(
        self,
        repo_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        git_url: Optional[str] = None,
        git_branch: Optional[str] = None,
        git_username: Optional[str] = None,
        git_password: Optional[str] = None,
        allocated_space_mb: Optional[int] = None,
        teacher: Optional[User] = None,
    ) -> Repository:
        """更新仓库信息

        Args:
            repo_id: 仓库ID
            name: 新的仓库名称（可选）
            description: 新的仓库描述（可选）
            is_active: 是否激活（可选）
            git_url: 新的Git URL（可选，仅Git仓库）
            git_branch: 新的Git分支（可选，仅Git仓库）
            git_username: 新的Git用户名（可选，仅Git仓库）
            git_password: 新的Git密码（可选，仅Git仓库）
            allocated_space_mb: 新的分配空间（可选，仅文件系统仓库）
            teacher: 教师用户（可选，用于验证权限）

        Returns:
            更新后的仓库对象

        Raises:
            ValueError: 如果参数无效
            Repository.DoesNotExist: 如果仓库不存在或教师无权访问
        """
        repository = self.get_repository_by_id(repo_id, teacher)

        updated_fields = []

        # 更新名称
        if name is not None:
            if not name.strip():
                raise ValueError("仓库名称不能为空")
            repository.name = name.strip()
            updated_fields.append("name")

        # 更新描述
        if description is not None:
            repository.description = description.strip() if description else ""
            updated_fields.append("description")

        # 更新激活状态
        if is_active is not None:
            repository.is_active = is_active
            updated_fields.append("is_active")

        # 更新Git仓库特定字段
        if repository.repo_type == "git":
            if git_url is not None:
                if not self._is_valid_git_url(git_url):
                    raise ValueError(f"无效的Git仓库URL: {git_url}")
                repository.git_url = git_url.strip()
                repository.url = git_url.strip()  # 兼容旧字段
                updated_fields.extend(["git_url", "url"])

            if git_branch is not None:
                repository.git_branch = git_branch.strip() if git_branch else "main"
                repository.branch = git_branch.strip() if git_branch else "main"
                updated_fields.extend(["git_branch", "branch"])

            if git_username is not None:
                repository.git_username = git_username.strip() if git_username else ""
                updated_fields.append("git_username")

            if git_password is not None:
                repository.git_password = git_password  # TODO: 加密存储
                updated_fields.append("git_password")

        # 更新文件系统仓库特定字段
        if repository.repo_type == "filesystem":
            if allocated_space_mb is not None:
                if allocated_space_mb <= 0:
                    raise ValueError("分配空间必须大于0")
                repository.allocated_space_mb = allocated_space_mb
                updated_fields.append("allocated_space_mb")

        if updated_fields:
            repository.save(update_fields=updated_fields + ["updated_at"])
            logger.info(f"更新仓库 {repository.name}: {', '.join(updated_fields)}")

        return repository

    def delete_repository(self, repo_id: int, teacher: Optional[User] = None) -> None:
        """删除仓库配置

        注意：只删除数据库配置，不删除物理文件

        Args:
            repo_id: 仓库ID
            teacher: 教师用户（可选，用于验证权限）

        Raises:
            Repository.DoesNotExist: 如果仓库不存在或教师无权访问
        """
        repository = self.get_repository_by_id(repo_id, teacher)

        repo_name = repository.name
        repo_type = repository.get_repo_type_display()
        teacher_name = repository.owner.username if repository.owner else "未知"

        repository.delete()

        logger.info(f"删除仓库配置: {repo_name} (类型: {repo_type}, 教师: {teacher_name})")
        logger.warning("注意：物理文件未被删除，仅移除了配置")

    def _is_valid_git_url(self, url: str) -> bool:
        """验证Git URL格式

        Args:
            url: Git URL

        Returns:
            是否有效
        """
        if not url:
            return False

        # 支持的格式：
        # - https://github.com/user/repo.git
        # - http://github.com/user/repo.git
        # - git@github.com:user/repo.git
        # - ssh://git@github.com/user/repo.git

        # HTTP(S) URL
        if url.startswith("http://") or url.startswith("https://"):
            return True

        # SSH URL (git@...)
        if url.startswith("git@"):
            return True

        # SSH URL (ssh://...)
        if url.startswith("ssh://"):
            return True

        return False
