import base64
import logging
import mimetypes
import os
import shutil
import subprocess

import mammoth
from django.conf import settings
try:
    from volcenginesdkarkruntime import Ark
except ImportError:  # Optional dependency for AI scoring
    Ark = None

from .config import FILE_ENCODINGS

logger = logging.getLogger(__name__)


class GitHandler:
    @staticmethod
    def is_git_repo(path):
        """Docstring."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def clone_repo(source_path, target_path):
        """Docstring."""
        try:
            logger.info(f"开始克隆仓?? ??{source_path} ??{target_path}")

            # 检查源路径是否??Git 仓库
            if not os.path.exists(source_path):
                raise Exception(f"源路径不存在: {source_path}")

            if not GitHandler.is_git_repo(source_path):
                raise Exception(f"源路径不是有效的 Git 仓库: {source_path}")

            # 如果目标路径已存在，先删??
            if os.path.exists(target_path):
                logger.info(f"目标路径已存在，正在删除: {target_path}")
                shutil.rmtree(target_path)

            # 创建父目??
            parent_dir = os.path.dirname(target_path)
            logger.info(f"创建父目?? {parent_dir}")
            os.makedirs(parent_dir, exist_ok=True)

            # 使用 git clone --local 克隆本地仓库
            logger.info("执行 git clone 命令")
            result = subprocess.run(
                ["git", "clone", "--local", source_path, target_path],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"克隆失败: {result.stderr}")
                raise Exception(f"克隆仓库失败: {result.stderr}")

            logger.info("仓库克隆成功")
            return True

        except Exception as e:
            logger.error(f"克隆仓库失败: {str(e)}")
            return False

    @staticmethod
    def get_repo_name(path):
        """Docstring."""
        try:
            # 尝试获取远程仓库名称
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                # 从远??URL 中提取仓库名
                repo_name = os.path.splitext(os.path.basename(result.stdout.strip()))[0]
            else:
                # 如果没有远程仓库，使用目录名
                repo_name = os.path.basename(path)

            return repo_name
        except Exception as e:
            logger.error(f"获取仓库名称失败: {str(e)}")
            return os.path.basename(path)

    @staticmethod
    def clone_repo_remote(repo_name, target_path):
        """Docstring."""
        try:
            result = subprocess.run(
                ["git", "clone", repo_name, target_path], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def pull_repo(repo_path):
        """Docstring."""
        try:
            result = subprocess.run(["git", "pull"], cwd=repo_path, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def checkout_branch(repo_path, branch):
        """Docstring."""
        try:
            result = subprocess.run(
                ["git", "checkout", branch], cwd=repo_path, capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_branches(repo_path):
        """Docstring."""
        try:
            result = subprocess.run(
                ["git", "branch", "-r"], cwd=repo_path, capture_output=True, text=True
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split("\n") if line.strip()]
            return []
        except Exception:
            return []

    @staticmethod
    def is_git_repository(path):
        """Docstring."""
        return os.path.exists(os.path.join(path, ".git"))

    @staticmethod
    def get_current_branch(path):
        """Docstring."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None


class FileHandler:
    @staticmethod
    def is_safe_path(path):
        """Docstring."""
        # 检查路径是否在媒体目录??
        media_root = getattr(settings, "MEDIA_ROOT", "")
        if media_root:
            try:
                real_path = os.path.realpath(path)
                real_media_root = os.path.realpath(media_root)
                return real_path.startswith(real_media_root)
            except (OSError, ValueError):
                return False

        # 如果没有设置MEDIA_ROOT，使用基本检??
        return not path.startswith("/") and ".." not in path

    @staticmethod
    def get_mime_type(file_path):
        """Docstring."""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type
        except Exception:
            return None

    @staticmethod
    def get_file_size(file_path):
        """Docstring."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    @staticmethod
    def create_directory_if_not_exists(path):
        """Docstring."""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def validate_file_extension(file_path):
        """Docstring."""
        allowed_extensions = {".txt", ".pdf", ".docx", ".doc"}
        ext = os.path.splitext(file_path)[1].lower()
        return ext in allowed_extensions

    @staticmethod
    def is_allowed_file(file_path):
        """Docstring."""
        # 检查文件扩展名
        allowed_extensions = {".txt", ".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".gif"}
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in allowed_extensions:
            return False

        # 检查文件大??
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)  # 10MB
        try:
            if os.path.getsize(file_path) > max_size:
                return False
        except OSError:
            return False

        return True

    @staticmethod
    def read_text_file(file_path):
        """Docstring."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in FILE_ENCODINGS:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise

    @staticmethod
    def handle_docx(file_path):
        """Docstring."""
        try:
            # 使用mammoth转换DOCX为HTML
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value

            # 处理图片
            def handle_image(image):
                with image.open() as image_bytes:
                    encoded = base64.b64encode(image_bytes.read()).decode()
                    return f'<img src="data:{image.content_type};base64,{encoded}" />'

            # 转换包含图片的DOCX
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file, convert_image=handle_image)
                html_content = result.value

            return html_content

        except Exception as e:
            logger.error(f"处理DOCX文件失败: {str(e)}")
            return f"<p>无法读取文件: {str(e)}</p>"


class DirectoryHandler:
    @staticmethod
    def ensure_directory(path):
        """Docstring."""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_directory_structure(root_dir):
        """Docstring."""
        structure = []

        try:
            for root, dirs, files in os.walk(root_dir):
                # 计算相对路径
                rel_path = os.path.relpath(root, root_dir)
                if rel_path == ".":
                    rel_path = ""

                # 添加目录
                for dir_name in sorted(dirs):
                    dir_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                    structure.append(
                        {"name": dir_name, "path": dir_path, "type": "directory", "size": None}
                    )

                # 添加文件
                for file_name in sorted(files):
                    file_path = os.path.join(rel_path, file_name) if rel_path else file_name
                    full_path = os.path.join(root, file_name)

                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        size = 0

                    structure.append(
                        {"name": file_name, "path": file_path, "type": "file", "size": size}
                    )

        except Exception as e:
            logger.error(f"获取目录结构失败: {str(e)}")

        return structure


class GradeHandler:
    @staticmethod
    def validate_grade(grade):
        """Docstring."""
        valid_grades = ["A", "B", "C", "D", "E"]
        return grade.upper() in valid_grades if grade else False

    @staticmethod
    def get_grade_description(grade):
        """Docstring."""
        descriptions = {"A": "Excellent", "B": "Good", "C": "Average", "D": "Pass", "E": "Fail"}
        return descriptions.get(grade.upper(), "未知")


def read_word_file(file_path):
    """Docstring."""
    try:
        from docx import Document

        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"读取Word文件失败: {str(e)}")
        return ""


def get_ai_evaluation(api_key, text):
    """Docstring."""
    if Ark is None:
        logger.error("volcenginesdkarkruntime is not installed; AI scoring unavailable")
        return "AI scoring dependency missing; please contact an admin"
    try:
        client = Ark(api_key=api_key)
        prompt = f"请阅读以下内容并给出成绩??50 字以内的评价：\n{text}"

        response = client.chat.completions.create(
            model="deepseek-r1-250528",
            messages=[{"content": prompt, "role": "user"}],
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI评价失败: {str(e)}")
        return f"请求出错：{str(e)}"


def process_multiple_files(api_key, file_paths):
    """Docstring."""
    results = []

    for file_path in file_paths:
        try:
            content = read_word_file(file_path)
            if content:
                evaluation = get_ai_evaluation(api_key, content)
                results.append({"file": file_path, "evaluation": evaluation, "status": "success"})
            else:
                results.append({"file": file_path, "evaluation": "文件内容为空", "status": "error"})
        except Exception as e:
            results.append(
                {"file": file_path, "evaluation": f"处理失败: {str(e)}", "status": "error"}
            )

    return results

