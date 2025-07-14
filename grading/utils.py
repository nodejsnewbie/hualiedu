import os
import logging
import mimetypes
import subprocess
from django.conf import settings
from .config import ALLOWED_FILE_TYPES, FILE_ENCODINGS, FILE_PROCESSING
import mammoth
import base64
import shutil
from .models import GlobalConfig
import traceback

logger = logging.getLogger(__name__)


class GitHandler:
    @staticmethod
    def is_git_repo(path):
        """检查目录是否为 Git 仓库"""
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
        """克隆本地仓库到目标路径"""
        try:
            logger.info(f"开始克隆仓库: 从 {source_path} 到 {target_path}")

            # 检查源路径是否为 Git 仓库
            if not os.path.exists(source_path):
                raise Exception(f"源路径不存在: {source_path}")

            if not GitHandler.is_git_repo(source_path):
                raise Exception(f"源路径不是有效的 Git 仓库: {source_path}")

            # 如果目标路径已存在，先删除
            if os.path.exists(target_path):
                logger.info(f"目标路径已存在，正在删除: {target_path}")
                shutil.rmtree(target_path)

            # 创建父目录
            parent_dir = os.path.dirname(target_path)
            logger.info(f"创建父目录: {parent_dir}")
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
        """获取仓库名称"""
        try:
            # 尝试获取远程仓库名称
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                # 从远程 URL 中提取仓库名
                repo_name = os.path.splitext(os.path.basename(result.stdout.strip()))[0]
            else:
                # 如果没有远程仓库，使用目录名
                repo_name = os.path.basename(path)

            return repo_name
        except Exception as e:
            logger.error(f"获取仓库名称失败: {str(e)}")
            return os.path.basename(path)


class FileHandler:
    @staticmethod
    def is_safe_path(path):
        """检查路径是否在允许的范围内"""
        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return False

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        return os.path.abspath(path).startswith(os.path.abspath(base_dir))

    @staticmethod
    def get_mime_type(file_path):
        """获取文件的 MIME 类型"""
        try:
            logger.info(f"开始获取文件类型: {file_path}")

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return None

            # 检查文件是否可读
            if not os.access(file_path, os.R_OK):
                logger.error(f"文件不可读: {file_path}")
                return None

            # 初始化 mimetypes 模块
            mimetypes.init()
            logger.info("mimetypes 模块已初始化")

            # 首先尝试使用 mimetypes 模块
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                logger.info(
                    f"使用 mimetypes 模块识别文件类型: {file_path} -> {mime_type}"
                )
                return mime_type

            # 如果 mimetypes 无法识别，根据文件扩展名判断
            ext = os.path.splitext(file_path)[1].lower()
            logger.info(f"文件扩展名: {ext}")

            if ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml"]:
                logger.info(f"使用扩展名识别文本文件: {file_path} -> text/plain")
                return "text/plain"
            elif ext in [".docx"]:
                logger.info(
                    f"使用扩展名识别 Word 文件: {file_path} -> application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext in [".pdf"]:
                logger.info(f"使用扩展名识别 PDF 文件: {file_path} -> application/pdf")
                return "application/pdf"

            logger.warning(f"无法识别文件类型: {file_path}")
            return None
        except Exception as e:
            logger.error(f"获取文件类型失败: {str(e)}\n{traceback.format_exc()}")
            return None

    @staticmethod
    def is_allowed_file(file_path):
        """检查文件是否允许上传"""
        try:
            mime_type = FileHandler.get_mime_type(file_path)
            if not mime_type:
                return False

            # 检查文件类型是否在允许列表中
            allowed_types = [
                "text/plain",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/pdf",
            ]
            return mime_type in allowed_types
        except Exception as e:
            logger.error(f"检查文件类型失败: {str(e)}")
            return False

    @staticmethod
    def read_text_file(file_path):
        """读取文本文件，尝试不同编码"""
        content = None
        for encoding in FILE_ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        return content

    @staticmethod
    def handle_docx(file_path):
        """处理Word文档"""
        try:
            # 自定义样式映射
            style_map = """
                p[style-name='Title'] => h1:fresh
                p[style-name='Heading 1'] => h2:fresh
                p[style-name='Heading 2'] => h3:fresh
                p[style-name='Heading 3'] => h4:fresh
                p[style-name='Normal'] => p:fresh
                r[style-name='Strong'] => strong
                r[style-name='Emphasis'] => em
                table => table.word-table
                tr => tr
                td => td
                p[style-name='List Paragraph'] => li:fresh
            """

            def handle_image(image):
                try:
                    with image.open() as image_bytes:
                        encoded_image = base64.b64encode(image_bytes.read()).decode(
                            "utf-8"
                        )
                        image_type = image.content_type or "image/png"
                        return {
                            "src": f"data:{image_type};base64,{encoded_image}",
                            "class": "word-image",
                        }
                except Exception as e:
                    logger.error(f"图片处理失败: {str(e)}")
                    return {"src": "", "alt": "图片加载失败"}

            with open(file_path, "rb") as docx_file:
                # 使用自定义样式映射转换文档
                result = mammoth.convert_to_html(
                    docx_file,
                    style_map=style_map,
                    convert_image=mammoth.images.img_element(handle_image),
                )

                # 添加警告信息到日志
                if result.messages:
                    for message in result.messages:
                        logger.warning(f"Word转换警告: {message}")

                # 添加基本样式
                html_content = f"""
                <div class="word-document">
                    <style>
                        .word-document {{
                            font-family: 'Microsoft YaHei', Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 100%;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .word-document h1 {{ font-size: 24px; margin: 20px 0; color: #2c3e50; }}
                        .word-document h2 {{ font-size: 20px; margin: 18px 0; color: #34495e; }}
                        .word-document h3 {{ font-size: 18px; margin: 16px 0; color: #2c3e50; }}
                        .word-document h4 {{ font-size: 16px; margin: 14px 0; color: #34495e; }}
                        .word-document p {{ margin: 12px 0; text-align: justify; }}
                        .word-document .word-image {{
                            max-width: 100%;
                            height: auto;
                            margin: 15px auto;
                            display: block;
                            border-radius: 4px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }}
                        .word-document .word-table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 15px 0;
                            background: #fff;
                        }}
                        .word-document .word-table td,
                        .word-document .word-table th {{
                            border: 1px solid #ddd;
                            padding: 12px;
                            text-align: left;
                        }}
                        .word-document .word-table tr:nth-child(even) {{
                            background-color: #f8f9fa;
                        }}
                        .word-document ul,
                        .word-document ol {{
                            margin: 12px 0;
                            padding-left: 24px;
                        }}
                        .word-document li {{
                            margin: 6px 0;
                        }}
                    </style>
                    {result.value}
                </div>
                """
                return html_content

        except FileNotFoundError:
            logger.error(f"Word文档不存在: {file_path}")
            return None
        except mammoth.DocumentHasZeroPages:
            logger.error(f"Word文档为空: {file_path}")
            return None
        except mammoth.InvalidFileFormat:
            logger.error(f"无效的Word文档格式: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Word文档处理失败: {str(e)}")
            return None


class DirectoryHandler:
    @staticmethod
    def ensure_directory(path):
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_directory_structure(root_dir):
        """获取目录结构"""
        try:
            name = os.path.basename(root_dir)
            # 获取相对于 BASE_DIR 的路径
            rel_path = os.path.relpath(root_dir, settings.BASE_DIR)
            structure = {
                "text": name,
                "children": [],
                "type": "folder",
                "id": rel_path,  # 使用相对路径
            }

            if not os.path.exists(root_dir):
                logger.warning(f"目录不存在: {root_dir}")
                return structure

            # 过滤掉隐藏文件和目录
            items = [
                item
                for item in sorted(os.listdir(root_dir))
                if not item.startswith(".")
            ]

            for item in items:
                abs_path = os.path.join(root_dir, item)
                rel_item_path = os.path.relpath(abs_path, settings.BASE_DIR)

                if os.path.isdir(abs_path):
                    child_structure = DirectoryHandler.get_directory_structure(abs_path)
                    # 确保子目录的 id 也是相对路径
                    child_structure["id"] = rel_item_path
                    structure["children"].append(child_structure)
                else:
                    structure["children"].append(
                        {
                            "text": item,
                            "type": "file",
                            "icon": "jstree-file",
                            "id": rel_item_path,
                        }
                    )
            return structure
        except Exception as e:
            logger.error(f"获取目录结构失败: {str(e)}")
            return structure


class GradeHandler:
    @staticmethod
    def validate_grade(grade):
        """验证评分是否有效"""
        from .config import GRADE_LEVELS

        return grade in GRADE_LEVELS

    @staticmethod
    def get_grade_description(grade):
        """获取评分描述"""
        from .config import GRADE_LEVELS

        return GRADE_LEVELS.get(grade, {}).get("description", "未知")
