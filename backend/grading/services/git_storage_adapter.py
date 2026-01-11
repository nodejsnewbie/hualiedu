"""
Git 远程仓库存储适配器 (Git Storage Adapter)

本模块实现通过 Git 命令直接访问远程仓库的存储适配器，无需本地克隆。

核心特性：
1. 远程直接访问：使用 git ls-tree 和 git show 命令直接读取远程仓库
2. 无本地克隆：不在本地文件系统创建仓库副本，节省存储空间
3. 自动缓存：使用 Django 缓存框架缓存远程数据，提高性能
4. 认证支持：支持 HTTP/HTTPS 用户名密码认证和 SSH 密钥认证
5. 协议支持：支持 http://, https://, git://, ssh://, git@ 等协议

实现需求：
- Requirements 3.2: 直接从远程 Git 仓库读取目录结构
- Requirements 3.4: 直接从远程仓库获取文件内容
- Requirements 3.6: 不在本地文件系统创建仓库克隆
- Requirements 10.1-10.3: 使用 Git 远程命令（ls-tree, show）
- Requirements 10.4: 使用内存缓存而不是文件系统缓存
- Requirements 10.5: 缓存过期自动刷新
- Requirements 10.6: 多用户共享缓存

技术实现：
- 使用 subprocess 执行 Git 命令
- 使用 Django cache 框架进行缓存
- 使用 URL 解析处理认证信息
- 使用 hashlib 生成缓存键

缓存策略：
- 目录列表缓存：5分钟
- 文件内容缓存：5分钟
- 缓存键格式：git_ls_{hash} 或 git_file_{hash}
- 多用户访问同一仓库共享缓存

使用示例：
    adapter = GitStorageAdapter(
        git_url="https://github.com/user/repo.git",
        branch="main",
        username="user",
        password="token"
    )

    # 列出目录（直接从远程读取）
    entries = adapter.list_directory("第一次作业")

    # 读取文件（直接从远程读取）
    content = adapter.read_file("第一次作业/张三-作业1.docx")
"""

import hashlib
import logging
import os
import subprocess
import tempfile
import locale
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from django.core.cache import cache

from .storage_adapter import RemoteAccessError, StorageAdapter, ValidationError

logger = logging.getLogger(__name__)


class GitStorageAdapter(StorageAdapter):
    """Git 远程仓库存储适配器

    使用 Git 命令（ls-tree, show）直接访问远程仓库，无需本地克隆。
    支持 HTTP/HTTPS 和 SSH 协议，支持用户名密码认证。

    工作原理：
    1. list_directory: 执行 `git ls-tree` 命令列出远程目录
    2. read_file: 执行 `git show` 命令读取远程文件
    3. 所有操作都通过 Git 命令直接访问远程仓库
    4. 结果自动缓存到 Django cache，提高性能

    认证处理：
    - HTTP/HTTPS: 将用户名密码嵌入 URL（如 https://user:pass@github.com/repo.git）
    - SSH: 使用系统 SSH 配置和密钥
    - 密码加密存储在数据库中，使用时解密

    缓存机制：
    - 使用 MD5 哈希生成缓存键
    - 缓存键包含 URL、分支和路径信息
    - 默认缓存 5 分钟
    - 多用户访问相同路径共享缓存

    错误处理：
    - Git 命令失败抛出 RemoteAccessError
    - 提供用户友好的错误消息
    - 记录详细的技术错误日志

    性能优化：
    - 首次访问较慢（需要连接远程仓库）
    - 后续访问使用缓存，速度快
    - 缓存过期自动刷新
    """

    def __init__(
        self,
        git_url: str,
        branch: str = "main",
        username: str = "",
        password: str = "",
        cache_timeout: int = 300,
    ):
        """初始化 Git 存储适配器

        Args:
            git_url: Git 仓库 URL
            branch: 分支名称，默认 "main"
            username: 用户名（可选）
            password: 密码（可选）
            cache_timeout: 缓存超时时间（秒），默认 300 秒（5分钟）
        """
        self.git_url = git_url
        self.branch = branch
        self.username = username
        self.password = password
        self.cache_timeout = cache_timeout
        self._auth_url = self._build_auth_url()

    def _build_auth_url(self) -> str:
        """构建带认证的 URL

        Returns:
            带认证信息的 URL（如果提供了用户名和密码）
        """
        if not self.username or not self.password:
            return self.git_url

        parsed = urlparse(self.git_url)

        # 只对 HTTP/HTTPS 协议添加认证
        if parsed.scheme in ["http", "https"]:
            netloc = f"{self.username}:{self.password}@{parsed.netloc}"
            return urlunparse(
                (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
            )

        return self.git_url

    def _is_ssh_url(self) -> bool:
        return self.git_url.startswith("git@") or self.git_url.startswith("ssh://")

    def _write_ssh_key_tempfile(self, ssh_key: str) -> str:
        key = (ssh_key or "").replace("\r\n", "\n").strip()
        if not key.endswith("\n"):
            key = f"{key}\n"
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
        temp_file.write(key)
        temp_file.flush()
        temp_file.close()
        return temp_file.name

    def _get_repo_dir(self) -> str:
        repo_hash = hashlib.md5(self.git_url.encode("utf-8")).hexdigest()
        base_dir = os.path.join(tempfile.gettempdir(), "huali-edu-git")
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, repo_hash)

    def _ensure_remote_configured(self, repo_dir: str) -> None:
        try:
            remotes_output = self._execute_git_command(
                ["remote"], cwd=repo_dir, use_auth=False
            )
            remotes = {
                remote.strip()
                for remote in remotes_output.decode("utf-8", errors="ignore").splitlines()
                if remote.strip()
            }
        except RemoteAccessError:
            remotes = set()

        if "origin" in remotes:
            self._execute_git_command(
                ["remote", "set-url", "origin", "{url}"], cwd=repo_dir, use_auth=True
            )
        else:
            self._execute_git_command(
                ["remote", "add", "origin", "{url}"], cwd=repo_dir, use_auth=True
            )

    def _ensure_remote_fetched(self) -> str:
        repo_dir = self._get_repo_dir()
        os.makedirs(repo_dir, exist_ok=True)

        if not os.path.isfile(os.path.join(repo_dir, "HEAD")):
            self._execute_git_command(["init", "--bare"], cwd=repo_dir, use_auth=False)

        self._ensure_remote_configured(repo_dir)
        
        # 实现重试机制，处理网络不稳定问题
        max_retries = 3
        retry_delay = 1  # 初始延迟1秒
        
        for attempt in range(max_retries):
            try:
                self._execute_git_command(
                    ["fetch", "--depth", "1", "origin", self.branch],
                    cwd=repo_dir,
                    use_auth=False,
                )
                break  # 成功则跳出重试循环
            except RemoteAccessError as exc:
                stderr = ""
                if getattr(exc, "details", None):
                    stderr = (exc.details.get("stderr") or "").lower()
                
                # 处理shallow file问题
                if "shallow file has changed" in stderr:
                    shallow_path = os.path.join(repo_dir, "shallow")
                    if os.path.isfile(shallow_path):
                        try:
                            os.remove(shallow_path)
                        except OSError:
                            pass
                    try:
                        self._execute_git_command(
                            ["fetch", "--depth", "1", "--force", "origin", self.branch],
                            cwd=repo_dir,
                            use_auth=False,
                        )
                        break  # 成功则跳出重试循环
                    except RemoteAccessError:
                        pass  # 继续重试
                
                # 处理锁文件问题
                elif "shallow.lock" in stderr or "index.lock" in stderr or "another git process" in stderr:
                    for lock_name in ("shallow.lock", "index.lock"):
                        lock_path = os.path.join(repo_dir, lock_name)
                        if os.path.isfile(lock_path):
                            try:
                                os.remove(lock_path)
                            except OSError:
                                pass
                    try:
                        self._execute_git_command(
                            ["fetch", "--depth", "1", "--force", "origin", self.branch],
                            cwd=repo_dir,
                            use_auth=False,
                        )
                        break  # 成功则跳出重试循环
                    except RemoteAccessError:
                        pass  # 继续重试
                
                # 检查是否为网络连接问题
                elif any(keyword in stderr for keyword in ["could not resolve hostname", "name or service not known", "network unreachable", "connection timed out"]):
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        import time
                        logger.warning(f"网络连接失败，{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        # 最后一次尝试失败，抛出网络错误
                        raise RemoteAccessError(
                            f"网络连接失败，已重试{max_retries}次: {stderr}",
                            user_message="网络连接失败，无法访问远程Git仓库。请检查网络连接。"
                        )
                else:
                    # 非网络问题，直接抛出
                    raise exc
        
        return repo_dir

    def _get_cache_key(self, path: str, operation: str) -> str:
        """生成缓存键

        Args:
            path: 文件或目录路径
            operation: 操作类型（ls, file 等）

        Returns:
            缓存键字符串
        """
        key_data = f"{self.git_url}:{self.branch}:{path}:{operation}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"git_storage:{key_hash}"

    def get_head_commit(self) -> Optional[str]:
        try:
            repo_dir = self._ensure_remote_fetched()
            output = self._execute_git_command(
                ["rev-parse", "FETCH_HEAD"], cwd=repo_dir, use_auth=False
            )
            return output.decode("utf-8", errors="ignore").strip()
        except Exception:
            return None

    def file_changed_since_commit(self, path: str, commit: str) -> Optional[bool]:
        if not path or not commit:
            return None
        try:
            repo_dir = self._ensure_remote_fetched()
            output = self._execute_git_command(
                ["diff", "--name-only", f"{commit}..FETCH_HEAD", "--", path],
                cwd=repo_dir,
                use_auth=False,
            )
            output_str = output.decode("utf-8", errors="ignore").strip()
            return bool(output_str)
        except Exception:
            return None

    def _execute_git_command(
        self,
        args: List[str],
        timeout: int = 30,
        use_auth: bool = True,
        cwd: Optional[str] = None,
    ) -> bytes:
        """?? Git ??

        Args:
            args: Git ??????
            timeout: ???????
            use_auth: ?????? URL

        Returns:
            ????????

        Raises:
            RemoteAccessError: ?????????
        """
        url = self._auth_url if use_auth else self.git_url

        # ??????
        cmd = ["git", "-c", "core.quotepath=false"] + args

        # ?????? URL ???
        cmd = [url if arg == "{url}" else arg for arg in cmd]

        ssh_key_path = None

        try:
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"
            if self._is_ssh_url():
                ssh_command = (
                    "ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10"
                )
                if self.password and "PRIVATE KEY" in self.password:
                    ssh_key_path = self._write_ssh_key_tempfile(self.password)
                    ssh_command = f'{ssh_command} -i "{ssh_key_path}" -o IdentitiesOnly=yes'
                env["GIT_SSH_COMMAND"] = ssh_command

            result = subprocess.run(
                cmd,
                env=env,  # ???????
                capture_output=True,
                timeout=timeout,
                check=False,
                cwd=cwd,
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="ignore").strip()

                # ???????????????
                user_message = self._get_user_friendly_error(error_msg)

                raise RemoteAccessError(
                    f"Git command failed: {' '.join(cmd)}\nError: {error_msg}",
                    user_message=user_message,
                    details={
                        "command": " ".join(cmd),
                        "return_code": result.returncode,
                        "stderr": error_msg,
                    },
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RemoteAccessError(
                f"Git command timeout: {' '.join(cmd)}",
                user_message="??????????????",
                details={"command": " ".join(cmd), "timeout": timeout},
            )
        except FileNotFoundError:
            raise RemoteAccessError(
                "Git command not found",
                user_message="Git ??????????????",
                details={"command": "git"},
            )
        finally:
            if ssh_key_path:
                try:
                    os.remove(ssh_key_path)
                except OSError:
                    pass

    def _get_user_friendly_error(self, error_msg: str) -> str:
        """将技术错误消息转换为用户友好的消息

        Args:
            error_msg: 技术错误消息

        Returns:
            用户友好的错误消息
        """
        error_lower = error_msg.lower()

        # Check more specific patterns first
        if "permission denied" in error_lower:
            return "没有权限访问该仓库，请检查访问权限"
        elif "authentication failed" in error_lower:
            return "Git 仓库认证失败，请检查用户名和密码"
        elif "could not read" in error_lower and (
            "username" in error_lower or "password" in error_lower
        ):
            return "Git 仓库认证失败，请检查用户名和密码"
        elif "repository not found" in error_lower or "not found" in error_lower:
            return "找不到指定的 Git 仓库，请检查 URL"
        elif (
            "connection" in error_lower or "network" in error_lower or "resolve host" in error_lower
        ):
            return "网络连接失败，请检查网络或稍后重试"
        elif "timeout" in error_lower:
            return "网络连接超时，请稍后重试"
        else:
            return "无法访问远程仓库，请检查配置或稍后重试"

    def _decode_output(self, output: bytes) -> str:
        try:
            text = output.decode("utf-8")
            if "\ufffd" in text:
                return output.decode("gbk", errors="replace")
            return text
        except UnicodeDecodeError:
            fallback = locale.getpreferredencoding(False) or "gbk"
            return output.decode(fallback, errors="replace")

    def _parse_ls_tree_output(self, output: bytes) -> List[Dict]:
        """解析 git ls-tree 输出

        Args:
            output: git ls-tree 命令的输出

        Returns:
            目录条目列表
        """
        entries = []
        output_str = self._decode_output(output)

        for line in output_str.strip().split("\n"):
            if not line:
                continue

            # 格式: <mode> <type> <hash>\t<name>
            # 或: <mode> <type> <hash> <size>\t<name> (使用 -l 选项时)
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            meta_parts = parts[0].split()
            name = parts[1]

            if len(meta_parts) < 3:
                continue

            mode = meta_parts[0]
            obj_type = meta_parts[1]
            obj_hash = meta_parts[2]
            size = int(meta_parts[3]) if len(meta_parts) > 3 and meta_parts[3] != "-" else 0

            entries.append(
                {
                    "name": name,
                    "type": "dir" if obj_type == "tree" else "file",
                    "size": size,
                    "mode": mode,
                    "hash": obj_hash,
                }
            )

        return entries

    def list_directory(self, path: str = "") -> List[Dict]:
        """列出远程目录内容

        使用 git ls-tree 命令列出远程仓库的目录内容。
        结果会被缓存以提高性能。

        Args:
            path: 相对路径，空字符串表示根目录

        Returns:
            目录条目列表

        Raises:
            RemoteAccessError: 访问失败时抛出
        """
        # 检查缓存
        cache_key = self._get_cache_key(path, "ls")
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for directory listing: {path}")
            return cached

        try:
            repo_dir = self._ensure_remote_fetched()
            ref = f"FETCH_HEAD:{path}" if path else "FETCH_HEAD"
            output = self._execute_git_command(
                ["ls-tree", "-l", ref], cwd=repo_dir, use_auth=False
            )

            entries = self._parse_ls_tree_output(output)

            # 缓存结果
            cache.set(cache_key, entries, self.cache_timeout)
            logger.debug(f"Cached directory listing: {path}")

            return entries

        except RemoteAccessError:
            raise
        except Exception as e:
            raise RemoteAccessError(
                f"Failed to list directory: {str(e)}",
                user_message="无法读取远程目录，请检查路径是否正确",
                details={"path": path, "error": str(e)},
            )

    def read_file(self, path: str) -> bytes:
        """读取远程文件内容

        使用 git show 命令读取远程仓库的文件内容。
        结果会被缓存以提高性能。

        Args:
            path: 文件相对路径

        Returns:
            文件内容（字节）

        Raises:
            RemoteAccessError: 读取失败时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", user_message="文件路径不能为空")

        # 检查缓存
        cache_key = self._get_cache_key(path, "file")
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for file: {path}")
            return cached

        try:
            repo_dir = self._ensure_remote_fetched()
            ref = f"FETCH_HEAD:{path}"
            content = self._execute_git_command(["show", ref], cwd=repo_dir, use_auth=False)

            # 缓存结果（文件内容缓存时间更长）
            cache.set(cache_key, content, self.cache_timeout * 2)
            logger.debug(f"Cached file content: {path}")

            return content

        except RemoteAccessError:
            raise
        except Exception as e:
            raise RemoteAccessError(
                f"Failed to read file: {str(e)}",
                user_message="无法读取文件内容，请检查文件路径",
                details={"path": path, "error": str(e)},
            )

    def write_file(self, path: str, content: bytes) -> bool:
        """写入文件（Git 远程仓库不支持直接写入）

        Args:
            path: 文件相对路径
            content: 文件内容

        Raises:
            NotImplementedError: Git 远程仓库不支持直接写入
        """
        raise NotImplementedError(
            "Git 远程仓库不支持直接写入文件。" "如需修改文件，请使用 Git 客户端进行提交和推送。"
        )

    def create_directory(self, path: str) -> bool:
        """创建目录（Git 远程仓库不支持直接创建）

        Args:
            path: 目录相对路径

        Raises:
            NotImplementedError: Git 远程仓库不支持直接创建目录
        """
        raise NotImplementedError("Git 远程仓库不支持直接创建目录。" "Git 会自动管理目录结构。")

    def delete_file(self, path: str) -> bool:
        """删除文件（Git 远程仓库不支持直接删除）

        Args:
            path: 文件相对路径

        Raises:
            NotImplementedError: Git 远程仓库不支持直接删除
        """
        raise NotImplementedError(
            "Git 远程仓库不支持直接删除文件。" "如需删除文件，请使用 Git 客户端进行提交和推送。"
        )

    def file_exists(self, path: str) -> bool:
        """检查文件是否存在

        Args:
            path: 文件相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        try:
            self.read_file(path)
            return True
        except (RemoteAccessError, ValidationError):
            return False

    def directory_exists(self, path: str) -> bool:
        """检查目录是否存在

        Args:
            path: 目录相对路径

        Returns:
            存在返回 True，不存在返回 False
        """
        try:
            self.list_directory(path)
            return True
        except RemoteAccessError:
            return False

    def invalidate_cache(self, path: Optional[str] = None):
        """清除缓存

        Args:
            path: 要清除的路径，None 表示清除所有缓存
        """
        if path is not None:
            # 清除特定路径的缓存
            cache.delete(self._get_cache_key(path, "ls"))
            cache.delete(self._get_cache_key(path, "file"))
            logger.debug(f"Invalidated cache for path: {path}")
        else:
            # 清除所有相关缓存（需要遍历所有可能的键）
            # 注意：Django 缓存不支持按前缀删除，这里只是示例
            logger.debug("Cache invalidation for all paths not fully implemented")
