import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError, JsonResponse, HttpResponseForbidden
import os
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.conf import settings
import json
import traceback
import mimetypes
import mammoth
import base64
from pathlib import Path
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from .utils import FileHandler, GitHandler
from django.views.decorators.http import require_http_methods
from .models import GlobalConfig, Repository
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.utils.decorators import method_decorator
import glob
from django.views import View
from volcenginesdkarkruntime import Ark

logger = logging.getLogger(__name__)

# Create your views here.

# 在文件开头添加缓存字典
directory_file_count_cache = {}


def get_directory_file_count_cached(dir_path):
    """获取目录文件数量（带缓存）"""
    if dir_path in directory_file_count_cache:
        return directory_file_count_cache[dir_path]

    try:
        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return 0

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, dir_path)

        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
            logger.error(f"路径不在基础目录内: {full_path}")
            return 0

        if not os.path.exists(full_path):
            logger.error(f"目录不存在: {full_path}")
            return 0

        if not os.path.isdir(full_path):
            logger.error(f"不是目录: {full_path}")
            return 0

        # 统计.docx文件
        file_count = 0
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isfile(item_path) and item.lower().endswith(".docx"):
                file_count += 1

        # 缓存结果
        directory_file_count_cache[dir_path] = file_count
        return file_count

    except Exception as e:
        logger.error(f"统计目录文件数量失败: {str(e)}")
        return 0


def clear_directory_file_count_cache():
    """清除目录文件数量缓存"""
    directory_file_count_cache.clear()


def index(request):
    return render(request, "index.html")


def test_js(request):
    return render(request, "test_js.html")


def test_grade_switch(request):
    return render(request, "test_grade_switch.html")


def debug_grading(request):
    return render(request, "debug_grading.html")


def simple_test(request):
    return render(request, "simple_test.html")


def grading_simple(request):
    """简化版评分页面视图"""
    try:
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return HttpResponseForbidden("请先登录")

        if not request.user.is_staff:
            logger.error("用户无权限")
            return HttpResponseForbidden("无权限访问")

        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir="~/jobs")

        base_dir = os.path.expanduser(config.repo_base_dir)

        # 检查目录权限
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        if not os.access(base_dir, os.R_OK):
            logger.error(f"无权限访问目录: {base_dir}")
            return HttpResponseForbidden("无权限访问目录")

        # 获取目录树
        try:
            initial_tree_data = get_directory_tree()
        except Exception as e:
            logger.error(f"获取目录树失败: {str(e)}")
            return render(
                request,
                "grading_simple.html",
                {
                    "files": [],
                    "error": f"获取目录树失败: {str(e)}",
                    "config": config,
                    "base_dir": base_dir,
                    "initial_tree_data": "[]",
                },
            )

        return render(
            request,
            "grading_simple.html",
            {
                "files": [],
                "error": None,
                "config": config,
                "base_dir": base_dir,
                "initial_tree_data": json.dumps(initial_tree_data, ensure_ascii=False),
            },
        )

    except Exception as e:
        logger.error(f"处理简化评分页面请求失败: {str(e)}")
        return render(
            request,
            "grading_simple.html",
            {
                "files": [],
                "error": f"处理请求失败: {str(e)}",
                "config": config if "config" in locals() else None,
                "base_dir": base_dir if "base_dir" in locals() else None,
                "initial_tree_data": "[]",
            },
        )


@login_required
@require_http_methods(["POST"])
def get_dir_file_count(request):
    """获取目录中文件数量的视图函数"""
    try:
        # 解析请求数据
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            elif request.content_type == "application/x-www-form-urlencoded":
                data = request.POST
            else:
                return HttpResponse("不支持的Content-Type", status=400)
        except json.JSONDecodeError:
            return HttpResponse("无效的JSON数据", status=400)

        # 获取目录路径
        dir_path = data.get("path")
        if not dir_path:
            return HttpResponse("缺少path参数", status=400)

        # 使用缓存获取文件数量
        file_count = get_directory_file_count_cached(dir_path)

        # 直接返回文件数量字符串
        return HttpResponse(str(file_count))

    except Exception as e:
        logger.error(f"获取目录文件数量出错: {str(e)}")
        return HttpResponse("服务器错误", status=500)


@login_required
@require_http_methods(["GET", "POST"])
def grading_page(request):
    """评分页面视图"""
    try:
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return HttpResponseForbidden("请先登录")

        if not request.user.is_staff:
            logger.error("用户无权限")
            return HttpResponseForbidden("无权限访问")

        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir="~/jobs")

        base_dir = os.path.expanduser(config.repo_base_dir)

        # 检查目录权限
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        if not os.access(base_dir, os.R_OK):
            logger.error(f"无权限访问目录: {base_dir}")
            return HttpResponseForbidden("无权限访问目录")

        # 获取目录树
        try:
            initial_tree_data = get_directory_tree()
        except Exception as e:
            logger.error(f"获取目录树失败: {str(e)}")
            return render(
                request,
                "grading.html",
                {
                    "files": [],
                    "error": f"获取目录树失败: {str(e)}",
                    "config": config,
                    "base_dir": base_dir,
                    "initial_tree_data": "[]",
                },
            )

        return render(
            request,
            "grading.html",
            {
                "files": [],
                "error": None,
                "config": config,
                "base_dir": base_dir,
                "initial_tree_data": json.dumps(initial_tree_data, ensure_ascii=False),
            },
        )

    except Exception as e:
        logger.error(f"处理评分页面请求失败: {str(e)}")
        return render(
            request,
            "grading.html",
            {
                "files": [],
                "error": f"处理请求失败: {str(e)}",
                "config": config if "config" in locals() else None,
                "base_dir": base_dir if "base_dir" in locals() else None,
                "initial_tree_data": "[]",
            },
        )


def get_directory_structure(root_dir):
    try:
        name = os.path.basename(root_dir)
        structure = {"text": name, "children": [], "type": "folder", "id": root_dir}

        if not os.path.exists(root_dir):
            logger.warning(f"目录不存在: {root_dir}")
            return structure

        # 过滤掉隐藏文件和目录
        items = [
            item for item in sorted(os.listdir(root_dir)) if not item.startswith(".")
        ]

        for item in items:
            path = os.path.join(root_dir, item)
            if os.path.isdir(path):
                structure["children"].append(get_directory_structure(path))
            else:
                structure["children"].append(
                    {"text": item, "type": "file", "icon": "jstree-file", "id": path}
                )
        return structure

    except Exception as e:
        logger.error(f"获取目录结构失败: {str(e)}")
        return {
            "text": os.path.basename(root_dir),
            "children": [],
            "type": "folder",
            "id": root_dir,
        }


def is_safe_path(path):
    """检查路径是否在允许的范围内"""
    normalized_path = os.path.normpath(path)
    return normalized_path.startswith(
        os.path.join(settings.BASE_DIR, "media", "grades")
    )


@require_http_methods(["POST"])
def create_directory(request):
    """创建目录"""
    try:
        data = json.loads(request.body)
        repo_name = data.get("repo_name")

        if not repo_name:
            return JsonResponse({"status": "error", "message": "未提供仓库名称"})

        logger.info(f"接收到的仓库名称: {repo_name}")

        # 构建目标路径
        target_path = os.path.join(settings.BASE_DIR, "media", "grades", repo_name)
        logger.info(f"目标路径: {target_path}")

        # 创建目录
        success = GitHandler.clone_repo(repo_name, target_path)

        if success:
            return JsonResponse(
                {"status": "success", "message": "目录创建成功", "repo_name": repo_name}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "目录创建失败，请检查日志"}
            )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "无效的 JSON 数据"})
    except Exception as e:
        logger.error(f"创建目录时发生错误: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})


def serve_file(request, file_path):
    """提供文件下载服务"""
    try:
        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return HttpResponse("未配置仓库基础目录", status=400)

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, file_path)

        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
            return HttpResponse("无权访问该文件", status=403)

        if not os.path.exists(full_path):
            return HttpResponse("文件不存在", status=404)

        # 获取文件类型
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = "application/octet-stream"

        # 以二进制模式读取文件
        with open(full_path, "rb") as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response["Content-Disposition"] = (
                f'inline; filename="{os.path.basename(file_path)}"'
            )
            return response

    except Exception as e:
        logger.error(f"文件服务失败: {str(e)}")
        return HttpResponse("服务器错误", status=500)


@login_required
def change_branch(request, repo_id):
    """切换仓库分支"""
    try:
        repo = Repository.objects.get(id=repo_id)
        if request.method == "POST":
            branch = request.POST.get("branch")
            if branch in repo.branches:
                repo.branch = branch
                repo.save()
                messages.success(request, f"已切换到分支 {branch}")
                return redirect("admin:grading_repository_changelist")
            else:
                messages.error(request, f"分支 {branch} 不存在")
        return render(
            request,
            "admin/grading/repository/change_branch.html",
            {"repo": repo, "branches": repo.branches, "current_branch": repo.branch},
        )
    except Repository.DoesNotExist:
        messages.error(request, "仓库不存在")
        return redirect("admin:grading_repository_changelist")


@login_required
def grading_view(request):
    logger.info("开始处理评分页面请求")

    if request.method == "POST":
        action = request.POST.get("action")
        logger.info(f"收到 POST 请求，action: {action}")

        if action == "get_content":
            path = request.POST.get("path")
            logger.info(f"请求获取文件内容，路径: {path}")
            try:
                # 从全局配置获取仓库基础目录
                config = GlobalConfig.objects.first()
                if not config or not config.repo_base_dir:
                    logger.error("未配置仓库基础目录")
                    return JsonResponse(
                        {"status": "error", "message": "未配置仓库基础目录"}
                    )

                # 展开路径中的用户目录符号（~）
                base_dir = os.path.expanduser(config.repo_base_dir)
                full_path = os.path.join(base_dir, path)

                logger.info(f"尝试读取文件: {full_path}")

                # 检查文件是否存在
                if not os.path.exists(full_path):
                    logger.error(f"文件不存在: {full_path}")
                    return JsonResponse({"status": "error", "message": "文件不存在"})

                # 读取文件内容
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(f"成功读取文件: {full_path}")
                return JsonResponse({"status": "success", "content": content})
            except Exception as e:
                logger.error(f"读取文件失败: {str(e)}\n{traceback.format_exc()}")
                return JsonResponse({"status": "error", "message": str(e)})

        elif action == "save_grade":
            path = request.POST.get("path")
            grade = request.POST.get("grade")
            logger.info(f"保存评分: 文件={path}, 评分={grade}")
            try:
                # 这里可以添加保存评分的逻辑
                # 例如保存到数据库或文件中
                return JsonResponse({"status": "success", "message": "评分已保存"})
            except Exception as e:
                logger.error(f"保存评分失败: {str(e)}")
                return JsonResponse({"status": "error", "message": str(e)})

    # GET 请求，显示评分页面
    try:
        logger.info("处理 GET 请求，准备显示评分页面")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return render(
                request,
                "grading.html",
                {
                    "files": [],
                    "error": "未配置仓库基础目录",
                    "config": config,
                    "base_dir": None,
                },
            )

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        logger.info(f"使用仓库基础目录: {base_dir}")

        # 如果目录不存在，尝试创建它
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir, exist_ok=True)
                logger.info(f"创建目录: {base_dir}")
            except Exception as e:
                logger.error(f"创建目录失败: {str(e)}")
                return render(
                    request,
                    "grading.html",
                    {
                        "files": [],
                        "error": f"无法创建目录: {str(e)}",
                        "config": config,
                        "base_dir": base_dir,
                    },
                )

        # 获取所有文件
        files = []
        logger.info("开始扫描文件...")

        # 检查目录权限
        try:
            os.access(base_dir, os.R_OK)
            logger.info(f"目录 {base_dir} 可读")
        except Exception as e:
            logger.error(f"目录权限检查失败: {str(e)}")

        # 遍历所有目录和文件
        for root, dirs, filenames in os.walk(base_dir):
            # 过滤掉隐藏文件和目录
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            filenames = [f for f in filenames if not f.startswith(".")]

            logger.info(f"扫描目录: {root}")
            logger.info(f"发现文件: {filenames}")

            for filename in filenames:
                # 构建相对路径
                rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                full_path = os.path.join(root, filename)

                logger.info(f"处理文件: {filename}")
                logger.info(f"相对路径: {rel_path}")
                logger.info(f"完整路径: {full_path}")

                # 检查文件类型
                mime_type = FileHandler.get_mime_type(full_path)
                logger.info(f"文件类型检查: {filename} -> {mime_type}")

                if mime_type and (
                    mime_type.startswith("text/")
                    or mime_type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    or mime_type == "application/pdf"
                ):
                    files.append(
                        {"name": filename, "path": rel_path, "type": mime_type}
                    )
                    logger.info(f"添加文件: {filename} ({mime_type})")
                else:
                    logger.info(f"跳过文件: {filename} (不支持的文件类型)")

        # 按文件名排序
        files.sort(key=lambda x: x["name"].lower())

        # 添加调试信息
        logger.info(f"找到 {len(files)} 个文件")
        for file in files:
            logger.info(
                f'文件: {file["name"]}, 路径: {file["path"]}, 类型: {file["type"]}'
            )

        return render(
            request,
            "grading.html",
            {"files": files, "error": None, "config": config, "base_dir": base_dir},
        )

    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}\n{traceback.format_exc()}")
        return render(
            request,
            "grading.html",
            {
                "files": [],
                "error": f"获取文件列表失败: {str(e)}",
                "config": config if "config" in locals() else None,
                "base_dir": base_dir if "base_dir" in locals() else None,
            },
        )


def get_directory_tree(file_path=""):
    """获取目录树结构"""
    try:
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir="~/jobs")
            logger.info("Created new GlobalConfig with default repo_base_dir")

        base_dir = os.path.expanduser(config.repo_base_dir)
        logger.info(f"Base directory: {base_dir}")

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            logger.info(f"Created base directory: {base_dir}")

        # 检查目录权限
        if not os.access(base_dir, os.R_OK):
            error_msg = f"No read permission for directory: {base_dir}"
            logger.error(error_msg)
            return []

        # 构建完整路径
        full_path = os.path.join(base_dir, file_path)
        logger.info(f"Getting directory tree for path: {full_path}")

        # 检查路径是否存在
        if not os.path.exists(full_path):
            error_msg = f"Path does not exist: {full_path}"
            logger.error(error_msg)
            return []

        # 检查路径权限
        if not os.access(full_path, os.R_OK):
            error_msg = f"No read permission for path: {full_path}"
            logger.error(error_msg)
            return []

        items = []
        try:
            # 获取目录内容并过滤掉隐藏文件和目录
            for item in sorted(os.listdir(full_path)):
                # 跳过隐藏文件和目录
                if item.startswith("."):
                    continue

                item_path = os.path.join(full_path, item)
                relative_path = os.path.join(file_path, item)

                # 检查项目权限
                if not os.access(item_path, os.R_OK):
                    logger.warning(f"No read permission for item: {item_path}")
                    continue

                # 获取项目状态
                is_dir = os.path.isdir(item_path)

                # 构建节点数据
                node = {
                    "id": relative_path,
                    "text": item,
                    "type": "folder" if is_dir else "file",
                    "icon": "jstree-folder" if is_dir else "jstree-file",
                    "state": {"opened": False, "disabled": False, "selected": False},
                }

                # 如果是目录，递归获取子目录并统计文件数量
                if is_dir:
                    children = get_directory_tree(relative_path)
                    if children:
                        node["children"] = children
                    else:
                        node["children"] = []
                        node["state"]["disabled"] = True

                    # 统计并缓存目录文件数量
                    file_count = get_directory_file_count_cached(relative_path)
                    node["data"] = {"file_count": file_count}
                # 如果是文件，添加文件特定的属性
                else:
                    # 获取文件扩展名
                    _, ext = os.path.splitext(item)
                    node["a_attr"] = {
                        "href": "#",
                        "data-type": "file",
                        "data-ext": ext.lower(),
                    }

                items.append(node)
                logger.info(f"Added {'directory' if is_dir else 'file'}: {item}")

            # 按类型和名称排序：目录在前，文件在后
            items.sort(key=lambda x: (x["type"] == "file", x["text"].lower()))

            logger.info(f"Successfully generated directory tree for path: {full_path}")
            logger.info(f"Found {len(items)} items")
            return items

        except Exception as e:
            error_msg = f"Error listing directory contents: {str(e)}"
            logger.error(error_msg)
            return []

    except Exception as e:
        error_msg = f"Error in get_directory_tree: {str(e)}"
        logger.error(error_msg)
        return []


def get_file_grade_info(full_path):
    """获取文件中的评分信息"""
    try:
        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        grade_info = {
            "has_grade": False,
            "grade": None,
            "grade_type": None,  # 'letter' 或 'text'
            "in_table": False,
        }

        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 检查评分
            try:
                doc = Document(full_path)

                # 首先检查表格中是否有评分
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if "评定分数" in cell.text:
                                # 检查下一个单元格是否有评分
                                cell_index = None
                                for j, table_cell in enumerate(row.cells):
                                    if table_cell == cell:
                                        cell_index = j
                                        break

                                if cell_index is not None and cell_index + 1 < len(
                                    row.cells
                                ):
                                    next_cell = row.cells[cell_index + 1]
                                    if next_cell.text.strip():
                                        grade_info["has_grade"] = True
                                        grade_info["grade"] = next_cell.text.strip()
                                        grade_info["in_table"] = True
                                        # 判断评分类型
                                        if grade_info["grade"] in [
                                            "A",
                                            "B",
                                            "C",
                                            "D",
                                            "E",
                                        ]:
                                            grade_info["grade_type"] = "letter"
                                        elif grade_info["grade"] in [
                                            "优秀",
                                            "良好",
                                            "中等",
                                            "及格",
                                            "不及格",
                                        ]:
                                            grade_info["grade_type"] = "text"
                                        break
                        if grade_info["has_grade"]:
                            break
                    if grade_info["has_grade"]:
                        break

                # 如果表格中没有找到，检查段落中是否有评分
                if not grade_info["has_grade"]:
                    for paragraph in doc.paragraphs:
                        if paragraph.text.startswith("老师评分："):
                            grade_text = paragraph.text.replace(
                                "老师评分：", ""
                            ).strip()
                            if grade_text:
                                grade_info["has_grade"] = True
                                grade_info["grade"] = grade_text
                                # 判断评分类型
                                if grade_text in ["A", "B", "C", "D", "E"]:
                                    grade_info["grade_type"] = "letter"
                                elif grade_text in [
                                    "优秀",
                                    "良好",
                                    "中等",
                                    "及格",
                                    "不及格",
                                ]:
                                    grade_info["grade_type"] = "text"
                                break

            except Exception as e:
                logger.error(f"检查 Word 文档评分失败: {str(e)}")
        else:
            # 对于其他文件，尝试以文本方式检查
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 查找评分行
                    for line in lines:
                        if line.strip().startswith("老师评分："):
                            grade_text = line.strip().replace("老师评分：", "").strip()
                            if grade_text:
                                grade_info["has_grade"] = True
                                grade_info["grade"] = grade_text
                                # 判断评分类型
                                if grade_text in ["A", "B", "C", "D", "E"]:
                                    grade_info["grade_type"] = "letter"
                                elif grade_text in [
                                    "优秀",
                                    "良好",
                                    "中等",
                                    "及格",
                                    "不及格",
                                ]:
                                    grade_info["grade_type"] = "text"
                                break

            except Exception as e:
                logger.error(f"检查文件评分失败: {str(e)}")

        logger.info(f"文件评分信息: {grade_info}")
        return grade_info

    except Exception as e:
        logger.error(f"获取文件评分信息失败: {str(e)}")
        return {
            "has_grade": False,
            "grade": None,
            "grade_type": None,
            "in_table": False,
        }


@login_required
@require_http_methods(["GET"])
def get_template_list(request):
    """获取模板列表"""
    try:
        logger.info("开始处理获取模板列表请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse(
                {
                    "code": 403,
                    "msg": "permission error",
                    "error": "exceptions.UserAuthError",
                },
                status=403,
            )

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse(
                {
                    "code": 403,
                    "msg": "permission error",
                    "error": "exceptions.UserAuthError",
                },
                status=403,
            )

        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            logger.error("未找到全局配置")
            return JsonResponse(
                {
                    "code": 500,
                    "msg": "configuration error",
                    "error": "exceptions.ConfigError",
                },
                status=500,
            )

        # 获取模板目录路径
        template_dir = os.path.join(settings.BASE_DIR, "templates", "writing")
        logger.info(f"模板目录路径: {template_dir}")

        # 检查目录是否存在
        if not os.path.exists(template_dir):
            logger.info(f"创建模板目录: {template_dir}")
            os.makedirs(template_dir, exist_ok=True)

        # 获取模板列表
        templates = []
        if os.path.exists(template_dir):
            for item in os.listdir(template_dir):
                if item.endswith(".docx"):
                    template_path = os.path.join(template_dir, item)
                    templates.append(
                        {
                            "name": item,
                            "path": template_path,
                            "size": os.path.getsize(template_path),
                            "modified": os.path.getmtime(template_path),
                        }
                    )

        logger.info(f"找到 {len(templates)} 个模板")
        return JsonResponse({"code": 200, "msg": "success", "data": templates})

    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse(
            {"code": 500, "msg": str(e), "error": "exceptions.ServerError"}, status=500
        )


@csrf_exempt
def get_file_content(request):
    if request.method == "POST":
        try:
            path = request.POST.get("path")
            if not path:
                logger.error("未提供文件路径")
                return JsonResponse({"status": "error", "message": "未提供文件路径"})

            # 从全局配置获取仓库基础目录
            config = GlobalConfig.objects.first()
            if not config or not config.repo_base_dir:
                logger.error("未配置仓库基础目录")
                return JsonResponse(
                    {"status": "error", "message": "未配置仓库基础目录"}
                )

            # 展开路径中的用户目录符号（~）
            base_dir = os.path.expanduser(config.repo_base_dir)
            full_path = os.path.join(base_dir, path)

            # 检查文件是否存在
            if not os.path.exists(full_path):
                logger.error(f"文件不存在: {full_path}")
                return JsonResponse({"status": "error", "message": "文件不存在"})

            # 获取文件类型
            mime_type, _ = mimetypes.guess_type(full_path)

            # 根据文件类型处理
            if mime_type:
                if mime_type.startswith("image/"):
                    # 图片文件
                    with open(full_path, "rb") as f:
                        content = base64.b64encode(f.read()).decode("utf-8")
                        return JsonResponse(
                            {
                                "status": "success",
                                "type": "image",
                                "content": f"data:{mime_type};base64,{content}",
                            }
                        )
                elif mime_type == "application/pdf":
                    # PDF 文件
                    return JsonResponse(
                        {
                            "status": "success",
                            "type": "pdf",
                            "content": f"/media/{path}",
                        }
                    )
                elif mime_type in [
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                ]:
                    # Excel 文件
                    try:
                        # 读取 Excel 文件
                        df = pd.read_excel(full_path, engine="openpyxl")

                        # 转换为 HTML
                        html_content = df.to_html(
                            index=False, classes="table table-bordered table-striped"
                        )

                        # 获取文件评分信息
                        grade_info = get_file_grade_info(full_path)

                        return JsonResponse(
                            {
                                "status": "success",
                                "type": "excel",
                                "content": html_content,
                                "grade_info": grade_info,
                            }
                        )
                    except Exception as e:
                        logger.error(f"Excel 文件处理失败: {str(e)}")
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": f"Excel 文件处理失败: {str(e)}",
                            }
                        )
                elif mime_type == "text/plain":
                    # 文本文件
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # 获取文件评分信息
                        grade_info = get_file_grade_info(full_path)

                        return JsonResponse(
                            {
                                "status": "success",
                                "type": "text",
                                "content": content,
                                "grade_info": grade_info,
                            }
                        )
                elif (
                    mime_type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ):
                    # Word 文档
                    try:
                        # 尝试使用 mammoth 读取
                        try:
                            import mammoth

                            with open(full_path, "rb") as docx_file:
                                result = mammoth.convert_to_html(docx_file)
                                html_content = result.value

                            # 添加样式
                            css = """
                            <style>
                                .docx-content {
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    padding: 20px;
                                    max-width: 100%;
                                    overflow-x: auto;
                                    box-sizing: border-box;
                                }
                                .docx-content img {
                                    max-width: 100%;
                                    height: auto;
                                }
                                .docx-content table {
                                    margin: 15px 0;
                                    border-collapse: collapse;
                                    width: 100%;
                                    max-width: 100%;
                                    overflow-x: auto;
                                    display: block;
                                }
                                .docx-content td, .docx-content th {
                                    padding: 8px;
                                    border: 1px solid #ddd;
                                    min-width: 100px;
                                    word-break: break-word;
                                }
                                .docx-content tr:nth-child(even) {
                                    background-color: #f9f9f9;
                                }
                                .docx-content h1 { 
                                    font-size: clamp(20px, 5vw, 24px);
                                    margin: 20px 0;
                                }
                                .docx-content h2 { 
                                    font-size: clamp(18px, 4vw, 20px);
                                    margin: 18px 0;
                                }
                                .docx-content h3 { 
                                    font-size: clamp(16px, 3vw, 18px);
                                    margin: 16px 0;
                                }
                                .docx-content p {
                                    margin: 10px 0;
                                    font-size: clamp(14px, 2vw, 16px);
                                }
                                @media screen and (max-width: 768px) {
                                    .docx-content {
                                        padding: 10px;
                                    }
                                    .docx-content td, .docx-content th {
                                        padding: 4px;
                                        font-size: 14px;
                                    }
                                }
                            </style>
                            """

                            final_content = (
                                css + f'<div class="docx-content">{html_content}</div>'
                            )

                            # 获取文件评分信息
                            grade_info = get_file_grade_info(full_path)

                            return JsonResponse(
                                {
                                    "status": "success",
                                    "type": "docx",
                                    "content": final_content,
                                    "grade_info": grade_info,
                                }
                            )

                        except Exception as mammoth_error:
                            logger.error(
                                f"Mammoth 处理失败，尝试使用 python-docx: {str(mammoth_error)}"
                            )
                            # 如果 mammoth 失败，回退到 python-docx
                            from docx import Document

                            doc = Document(full_path)

                            # 构建 HTML 内容
                            html_content = ['<div class="docx-content">']

                            # 处理段落
                            for paragraph in doc.paragraphs:
                                # 检查段落样式和内容
                                style = paragraph.style.name
                                text = paragraph.text.strip()

                                # 跳过完全空的段落
                                if not text and not paragraph.runs:
                                    continue

                                # 处理段落样式
                                if style.startswith("Heading"):
                                    level = style[-1] if style[-1].isdigit() else 1
                                    html_content.append(f"<h{level}>{text}</h{level}>")
                                else:
                                    # 处理段落中的格式
                                    formatted_text = ""
                                    for run in paragraph.runs:
                                        if run.bold:
                                            formatted_text += (
                                                f"<strong>{run.text}</strong>"
                                            )
                                        elif run.italic:
                                            formatted_text += f"<em>{run.text}</em>"
                                        else:
                                            formatted_text += run.text

                                    if formatted_text:
                                        html_content.append(f"<p>{formatted_text}</p>")
                                    else:
                                        html_content.append(f"<p>{text}</p>")

                            # 处理表格
                            for table in doc.tables:
                                html_content.append(
                                    '<table class="table table-bordered">'
                                )
                                for row in table.rows:
                                    html_content.append("<tr>")
                                    for cell in row.cells:
                                        # 处理单元格中的格式
                                        cell_text = ""
                                        for paragraph in cell.paragraphs:
                                            for run in paragraph.runs:
                                                if run.bold:
                                                    cell_text += (
                                                        f"<strong>{run.text}</strong>"
                                                    )
                                                elif run.italic:
                                                    cell_text += f"<em>{run.text}</em>"
                                                else:
                                                    cell_text += run.text
                                        html_content.append(f"<td>{cell_text}</td>")
                                    html_content.append("</tr>")
                                html_content.append("</table>")

                            html_content.append("</div>")

                            # 添加样式
                            css = """
                            <style>
                                .docx-content {
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    padding: 20px;
                                    max-width: 100%;
                                    overflow-x: auto;
                                    box-sizing: border-box;
                                }
                                .docx-content img {
                                    max-width: 100%;
                                    height: auto;
                                }
                                .docx-content table {
                                    margin: 15px 0;
                                    border-collapse: collapse;
                                    width: 100%;
                                    max-width: 100%;
                                    overflow-x: auto;
                                    display: block;
                                }
                                .docx-content td, .docx-content th {
                                    padding: 8px;
                                    border: 1px solid #ddd;
                                    min-width: 100px;
                                    word-break: break-word;
                                }
                                .docx-content tr:nth-child(even) {
                                    background-color: #f9f9f9;
                                }
                                .docx-content h1 { 
                                    font-size: clamp(20px, 5vw, 24px);
                                    margin: 20px 0;
                                }
                                .docx-content h2 { 
                                    font-size: clamp(18px, 4vw, 20px);
                                    margin: 18px 0;
                                }
                                .docx-content h3 { 
                                    font-size: clamp(16px, 3vw, 18px);
                                    margin: 16px 0;
                                }
                                .docx-content p {
                                    margin: 10px 0;
                                    font-size: clamp(14px, 2vw, 16px);
                                }
                                @media screen and (max-width: 768px) {
                                    .docx-content {
                                        padding: 10px;
                                    }
                                    .docx-content td, .docx-content th {
                                        padding: 4px;
                                        font-size: 14px;
                                    }
                                }
                            </style>
                            """

                            final_content = css + "\n".join(html_content)
                            return JsonResponse(
                                {
                                    "status": "success",
                                    "type": "docx",
                                    "content": final_content,
                                }
                            )

                    except Exception as e:
                        logger.error(f"Word 文档处理失败: {str(e)}")
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": f"Word 文档处理失败: {str(e)}",
                            }
                        )

            # 如果是二进制文件，提供下载链接
            return JsonResponse(
                {"status": "success", "type": "binary", "content": f"/media/{path}"}
            )

        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": f"获取文件内容失败: {str(e)}"}
            )

    return JsonResponse({"status": "error", "message": "不支持的请求方法"})


@login_required
@require_http_methods(["POST"])
def add_grade_to_file(request):
    """添加评分到文件末尾"""
    try:
        logger.info("开始处理添加评分到文件请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"status": "error", "message": "请先登录"}, status=403)

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse(
                {"status": "error", "message": "无权限访问"}, status=403
            )

        # 获取文件路径和评分
        path = request.POST.get("path")
        grade = request.POST.get("grade")

        if not path or not grade:
            logger.error("未提供文件路径或评分")
            return JsonResponse({"status": "error", "message": "未提供文件路径或评分"})

        logger.info(f"请求添加评分到文件，路径: {path}, 评分: {grade}")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, path)

        logger.info(f"尝试修改文件: {full_path}")

        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"status": "error", "message": "文件不存在"})

        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f"无权限修改文件: {full_path}")
            return JsonResponse({"status": "error", "message": "无权限修改文件"})

        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # 根据文件类型处理
        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 添加评分
            try:
                doc = Document(full_path)

                # 智能检测评定分数位置
                grade_inserted = False

                logger.info(f"开始检查文档中的表格，共 {len(doc.tables)} 个表格")

                # 首先检查表格中是否有"评定分数"
                for table_index, table in enumerate(doc.tables):
                    logger.info(
                        f"检查第 {table_index + 1} 个表格，共 {len(table.rows)} 行"
                    )
                    for row_index, row in enumerate(table.rows):
                        logger.info(
                            f"检查第 {row_index + 1} 行，共 {len(row.cells)} 个单元格"
                        )
                        for cell_index, cell in enumerate(row.cells):
                            cell_text = cell.text.strip()
                            logger.info(f'单元格 {cell_index + 1} 内容: "{cell_text}"')
                            if "评定分数" in cell_text:
                                logger.info(
                                    f'找到包含"评定分数"的单元格: 表格{table_index + 1}, 行{row_index + 1}, 单元格{cell_index + 1}'
                                )

                                # 检查是否有下一个单元格
                                if cell_index + 1 < len(row.cells):
                                    # 在下一个单元格中插入评分
                                    next_cell = row.cells[cell_index + 1]
                                    next_cell.text = grade
                                    grade_inserted = True
                                    logger.info(
                                        f"在评定分数后的单元格中插入评分: {grade}"
                                    )
                                    break
                                else:
                                    logger.warning("没有下一个单元格可以插入评分")
                        if grade_inserted:
                            break
                    if grade_inserted:
                        break

                # 如果表格中没有找到，再检查段落中是否有"评定分数"
                if not grade_inserted:
                    for i, paragraph in enumerate(doc.paragraphs):
                        if "评定分数" in paragraph.text:
                            logger.info(
                                '在段落中找到"评定分数"，但无法在表格中插入评分'
                            )
                            break

                # 如果没有找到"评定分数"或无法在表格中插入，则按原来的逻辑处理
                if not grade_inserted:
                    # 检查最后一段是否已经是评分
                    if doc.paragraphs and doc.paragraphs[-1].text.startswith(
                        "老师评分："
                    ):
                        # 如果是评分，则删除它
                        doc._body._body.remove(doc.paragraphs[-1]._p)

                    # 添加一个空段落
                    doc.add_paragraph()
                    # 添加评分段落
                    doc.add_paragraph(f"老师评分：{grade}")
                    logger.info(f"在文件末尾添加评分: {grade}")

                # 保存文档
                doc.save(full_path)
                logger.info(f"成功添加评分到 Word 文档: {full_path}")
                # 新增：登记成绩到平时成绩登记表
                try:
                    from huali_edu.grade_registration import GradeRegistration

                    grader = GradeRegistration()
                    rel_path = os.path.relpath(full_path, base_dir)
                    path_parts = rel_path.split(os.sep)
                    if len(path_parts) >= 3:
                        repo_dir = path_parts[0]
                        homework_dir = path_parts[1]
                        file_name = path_parts[2]
                        student_name = os.path.splitext(file_name)[0]
                        repo_abs_path = os.path.join(base_dir, repo_dir)
                        from pathlib import Path

                        excel_files = list(
                            Path(repo_abs_path).glob("平时成绩登记表-*.xlsx")
                        )
                        if excel_files:
                            excel_path = str(excel_files[0])
                            grader.write_grade_to_excel(
                                excel_path=excel_path,
                                student_name=student_name,
                                homework_dir_name=homework_dir,
                                grade=grade,
                            )
                            logger.info(
                                f"已登记成绩到登记表: {excel_path}, 学生: {student_name}, 作业: {homework_dir}, 成绩: {grade}"
                            )
                        else:
                            logger.warning(
                                f"未找到登记表: {repo_abs_path}/平时成绩登记表-*.xlsx"
                            )
                    else:
                        logger.warning(f"路径结构无法推断登记表信息: {rel_path}")
                except Exception as e:
                    logger.error(f"登记成绩到登记表失败: {str(e)}")
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "评分已添加",
                        "file_type": "docx",
                        "inserted_in_table": grade_inserted,
                    }
                )
            except Exception as e:
                logger.error(f"添加评分到 Word 文档失败: {str(e)}")
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"添加评分到 Word 文档失败: {str(e)}",
                    }
                )
        else:
            # 对于其他文件，尝试以文本方式添加
            try:
                with open(full_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 检查最后一行是否已经是评分
                    if lines and lines[-1].strip().startswith("老师评分："):
                        # 如果是评分，则删除它
                        lines = lines[:-1]

                    # 移动到文件末尾
                    f.seek(0)
                    f.truncate()

                    # 写入所有行（除了最后一个评分）
                    f.writelines(lines)

                    # 添加新行和评分
                    f.write(f"\n老师评分：{grade}\n")

                logger.info(f"成功添加评分到文件: {full_path}")
                # 新增：登记成绩到平时成绩登记表
                try:
                    from huali_edu.grade_registration import GradeRegistration

                    grader = GradeRegistration()
                    rel_path = os.path.relpath(full_path, base_dir)
                    path_parts = rel_path.split(os.sep)
                    if len(path_parts) >= 3:
                        repo_dir = path_parts[0]
                        homework_dir = path_parts[1]
                        file_name = path_parts[2]
                        student_name = os.path.splitext(file_name)[0]
                        repo_abs_path = os.path.join(base_dir, repo_dir)
                        from pathlib import Path

                        excel_files = list(
                            Path(repo_abs_path).glob("平时成绩登记表-*.xlsx")
                        )
                        if excel_files:
                            excel_path = str(excel_files[0])
                            grader.write_grade_to_excel(
                                excel_path=excel_path,
                                student_name=student_name,
                                homework_dir_name=homework_dir,
                                grade=grade,
                            )
                            logger.info(
                                f"已登记成绩到登记表: {excel_path}, 学生: {student_name}, 作业: {homework_dir}, 成绩: {grade}"
                            )
                        else:
                            logger.warning(
                                f"未找到登记表: {repo_abs_path}/平时成绩登记表-*.xlsx"
                            )
                    else:
                        logger.warning(f"路径结构无法推断登记表信息: {rel_path}")
                except Exception as e:
                    logger.error(f"登记成绩到登记表失败: {str(e)}")
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "评分已添加到文件末尾",
                        "file_type": "text",
                    }
                )
            except Exception as e:
                logger.error(f"添加评分到文件失败: {str(e)}")
                return JsonResponse(
                    {"status": "error", "message": f"添加评分到文件失败: {str(e)}"}
                )

    except Exception as e:
        logger.error(f"添加评分到文件失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
@require_http_methods(["POST"])
def save_grade(request):
    """保存评分"""
    try:
        logger.info("开始处理保存评分请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"status": "error", "message": "请先登录"}, status=403)

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse(
                {"status": "error", "message": "无权限访问"}, status=403
            )

        # 获取文件路径和评分
        path = request.POST.get("path")
        grade = request.POST.get("grade")

        if not path or not grade:
            logger.error("未提供文件路径或评分")
            return JsonResponse({"status": "error", "message": "未提供文件路径或评分"})

        logger.info(f"请求保存评分，路径: {path}, 评分: {grade}")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, path)

        logger.info(f"尝试修改文件: {full_path}")

        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"status": "error", "message": "文件不存在"})

        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f"无权限修改文件: {full_path}")
            return JsonResponse({"status": "error", "message": "无权限修改文件"})

        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # 根据文件类型处理
        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 添加评分
            try:
                doc = Document(full_path)
                # 添加一个空段落
                doc.add_paragraph()
                # 添加评分段落
                doc.add_paragraph(f"老师评分：{grade}")
                # 保存文档
                doc.save(full_path)
                logger.info(f"成功添加评分到 Word 文档: {full_path}")
                return JsonResponse(
                    {"status": "success", "message": "评分已保存", "file_type": "docx"}
                )
            except Exception as e:
                logger.error(f"添加评分到 Word 文档失败: {str(e)}")
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"添加评分到 Word 文档失败: {str(e)}",
                    }
                )
        else:
            # 对于其他文件，尝试以文本方式添加
            try:
                with open(full_path, "a", encoding="utf-8") as f:
                    f.write(f"\n老师评分：{grade}\n")
                logger.info(f"成功添加评分到文件: {full_path}")
                return JsonResponse(
                    {"status": "success", "message": "评分已保存", "file_type": "text"}
                )
            except Exception as e:
                logger.error(f"添加评分到文件失败: {str(e)}")
                return JsonResponse(
                    {"status": "error", "message": f"添加评分到文件失败: {str(e)}"}
                )

    except Exception as e:
        logger.error(f"保存评分失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
@require_http_methods(["POST"])
def remove_grade(request):
    """删除文件中的评分"""
    try:
        logger.info("开始处理删除评分请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"status": "error", "message": "请先登录"}, status=403)

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse(
                {"status": "error", "message": "无权限访问"}, status=403
            )

        # 获取文件路径
        path = request.POST.get("path")
        if not path:
            logger.error("未提供文件路径")
            return JsonResponse({"status": "error", "message": "未提供文件路径"})

        logger.info(f"请求删除评分，路径: {path}")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, path)

        logger.info(f"尝试修改文件: {full_path}")

        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"status": "error", "message": "文件不存在"})

        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f"无权限修改文件: {full_path}")
            return JsonResponse({"status": "error", "message": "无权限修改文件"})

        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # 根据文件类型处理
        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 删除评分
            try:
                doc = Document(full_path)

                # 检查最后一段是否是评分
                if doc.paragraphs and doc.paragraphs[-1].text.startswith("老师评分："):
                    # 如果是评分，则删除它
                    doc._body._body.remove(doc.paragraphs[-1]._p)
                    # 如果前一段是空行，也删除它
                    if doc.paragraphs and not doc.paragraphs[-1].text.strip():
                        doc._body._body.remove(doc.paragraphs[-1]._p)
                    # 保存文档
                    doc.save(full_path)
                    logger.info(f"成功删除 Word 文档中的评分: {full_path}")
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "评分已删除",
                            "file_type": "docx",
                        }
                    )
                else:
                    logger.info(f"Word 文档中没有找到评分: {full_path}")
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "文件中没有找到评分",
                            "file_type": "docx",
                        }
                    )
            except Exception as e:
                logger.error(f"删除 Word 文档中的评分失败: {str(e)}")
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"删除 Word 文档中的评分失败: {str(e)}",
                    }
                )
        else:
            # 对于其他文件，尝试以文本方式删除
            try:
                with open(full_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 检查最后一行是否是评分
                    if lines and lines[-1].strip().startswith("老师评分："):
                        # 如果是评分，则删除它
                        lines = lines[:-1]
                        # 如果前一行是空行，也删除它
                        if lines and not lines[-1].strip():
                            lines = lines[:-1]

                        # 移动到文件开头并截断
                        f.seek(0)
                        f.truncate()
                        # 写入剩余内容
                        f.writelines(lines)

                        logger.info(f"成功删除文件中的评分: {full_path}")
                        return JsonResponse(
                            {
                                "status": "success",
                                "message": "评分已删除",
                                "file_type": "text",
                            }
                        )
                    else:
                        logger.info(f"文件中没有找到评分: {full_path}")
                        return JsonResponse(
                            {
                                "status": "success",
                                "message": "文件中没有找到评分",
                                "file_type": "text",
                            }
                        )
            except Exception as e:
                logger.error(f"删除文件中的评分失败: {str(e)}")
                return JsonResponse(
                    {"status": "error", "message": f"删除文件中的评分失败: {str(e)}"}
                )

    except Exception as e:
        logger.error(f"删除评分失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
@require_http_methods(["POST"])
def save_teacher_comment(request):
    """保存教师评价到文件末尾"""
    try:
        logger.info("开始处理保存教师评价请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"success": False, "message": "请先登录"})

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse({"success": False, "message": "无权限访问"})

        # 获取请求数据
        file_path = request.POST.get("file_path")
        comment = request.POST.get("comment")

        if not file_path or not comment:
            logger.error("未提供文件路径或评价内容")
            return JsonResponse({"success": False, "message": "缺少必要参数"})

        logger.info(f"请求保存教师评价，路径: {file_path}, 评价: {comment}")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"success": False, "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, file_path)

        logger.info(f"尝试修改文件: {full_path}")

        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"success": False, "message": "文件不存在"})

        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f"无权限修改文件: {full_path}")
            return JsonResponse({"success": False, "message": "无权限修改文件"})

        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # 根据文件类型处理
        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 添加评价
            try:
                doc = Document(full_path)

                # 删除所有现有的教师评价段落
                paragraphs_to_remove = []
                for i, paragraph in enumerate(doc.paragraphs):
                    if paragraph.text.startswith("教师评价："):
                        paragraphs_to_remove.append(i)

                # 从后往前删除，避免索引变化
                for i in reversed(paragraphs_to_remove):
                    doc._body._body.remove(doc.paragraphs[i]._p)

                # 确保文档末尾有足够的空间
                # 添加分隔线
                separator = doc.add_paragraph()
                separator.text = "=" * 50
                separator.alignment = WD_ALIGN_PARAGRAPH.CENTER

                # 添加空行
                doc.add_paragraph()

                # 添加教师评价标题
                title = doc.add_paragraph()
                title.text = "教师评价"
                title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                # 使用默认样式，避免样式不存在的问题
                try:
                    title.style = doc.styles["Heading 1"]
                except Exception:
                    # 如果Heading 1样式不存在，使用默认样式
                    pass

                # 添加空行
                doc.add_paragraph()

                # 添加教师评价内容
                comment_para = doc.add_paragraph()
                comment_para.text = comment
                comment_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                # 添加空行
                doc.add_paragraph()

                # 添加时间戳
                timestamp = doc.add_paragraph()
                timestamp.text = (
                    f"评价时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
                )
                timestamp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                # 使用默认样式，避免样式不存在的问题
                try:
                    timestamp.style = doc.styles["Caption"]
                except Exception:
                    # 如果Caption样式不存在，使用默认样式
                    pass

                # 保存文档
                doc.save(full_path)
                logger.info(f"成功添加教师评价到 Word 文档: {full_path}")
                return JsonResponse({"success": True, "message": "教师评价已保存"})
            except Exception as e:
                logger.error(f"添加教师评价到 Word 文档失败: {str(e)}")
                return JsonResponse(
                    {"success": False, "message": f"添加教师评价失败: {str(e)}"}
                )
        else:
            # 对于其他文件，尝试以文本方式添加
            try:
                with open(full_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 检查最后一行是否已经是教师评价
                    if lines and lines[-1].strip().startswith("教师评价："):
                        # 如果是评价，则删除它
                        lines = lines[:-1]

                    # 移动到文件末尾
                    f.seek(0)
                    f.truncate()

                    # 写入所有行（除了最后一个评价）
                    f.writelines(lines)

                    # 添加新行和评价
                    f.write(f"\n教师评价：{comment}\n")

                logger.info(f"成功添加教师评价到文件: {full_path}")
                return JsonResponse({"success": True, "message": "教师评价已保存"})
            except Exception as e:
                logger.error(f"添加教师评价到文件失败: {str(e)}")
                return JsonResponse(
                    {"success": False, "message": f"添加教师评价失败: {str(e)}"}
                )

    except Exception as e:
        logger.error(f"保存教师评价失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"success": False, "message": f"保存失败: {str(e)}"})


@login_required
@require_http_methods(["GET"])
def get_teacher_comment(request):
    """从文件中获取教师评价"""
    try:
        logger.info("开始处理获取教师评价请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"success": False, "message": "请先登录"})

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse({"success": False, "message": "无权限访问"})

        # 获取请求数据
        file_path = request.GET.get("file_path")

        if not file_path:
            logger.error("未提供文件路径")
            return JsonResponse({"success": False, "message": "缺少文件路径参数"})

        logger.info(f"请求获取教师评价，路径: {file_path}")

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"success": False, "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, file_path)

        logger.info(f"尝试读取文件: {full_path}")

        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"success": False, "message": "文件不存在"})

        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # 根据文件类型处理
        if ext == ".docx":
            # 对于 Word 文档，使用 python-docx 读取评价
            try:
                doc = Document(full_path)

                # 查找教师评价内容
                teacher_comment = None
                found_title = False

                for paragraph in doc.paragraphs:
                    # 查找"教师评价"标题
                    if paragraph.text.strip() == "教师评价":
                        found_title = True
                        continue

                    # 如果找到了标题，下一个非空段落就是评价内容
                    if found_title and paragraph.text.strip():
                        teacher_comment = paragraph.text.strip()
                        break

                if teacher_comment:
                    logger.info(f"找到教师评价: {teacher_comment}")
                    return JsonResponse({"success": True, "comment": teacher_comment})
                else:
                    logger.info("文件中没有找到教师评价")
                    return JsonResponse({"success": True, "comment": "暂无评价"})

            except Exception as e:
                logger.error(f"读取 Word 文档中的教师评价失败: {str(e)}")
                return JsonResponse(
                    {"success": False, "message": f"读取教师评价失败: {str(e)}"}
                )
        else:
            # 对于其他文件，尝试以文本方式读取
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 查找教师评价行
                    teacher_comment = None
                    for line in lines:
                        if line.strip().startswith("教师评价："):
                            teacher_comment = (
                                line.strip().replace("教师评价：", "").strip()
                            )
                            break

                    if teacher_comment:
                        logger.info(f"找到教师评价: {teacher_comment}")
                        return JsonResponse(
                            {"success": True, "comment": teacher_comment}
                        )
                    else:
                        logger.info("文件中没有找到教师评价")
                        return JsonResponse({"success": True, "comment": "暂无评价"})

            except Exception as e:
                logger.error(f"读取文件中的教师评价失败: {str(e)}")
                return JsonResponse(
                    {"success": False, "message": f"读取教师评价失败: {str(e)}"}
                )

    except Exception as e:
        logger.error(f"获取教师评价失败: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"success": False, "message": f"获取失败: {str(e)}"})


def test_grading_no_auth(request):
    """无需登录权限的评分功能测试页面"""
    return render(request, "test_grading_no_auth.html")


@login_required
@require_http_methods(["GET", "POST"])
def batch_grade_registration(request):
    """批量登分功能"""
    try:
        logger.info("开始处理批量登分请求")

        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error("用户未认证")
            return JsonResponse({"status": "error", "message": "请先登录"}, status=403)

        if not request.user.is_staff:
            logger.error("用户无权限")
            return JsonResponse(
                {"status": "error", "message": "无权限访问"}, status=403
            )

        if request.method == "GET":
            # 获取仓库列表
            return _get_repository_list(request)
        elif request.method == "POST":
            # 执行批量登分
            return _execute_batch_grade_registration(request)

    except Exception as e:
        logger.error(f"批量登分处理失败: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"批量登分处理失败: {str(e)}"}, status=500
        )


def _get_repository_list(request):
    """获取仓库列表"""
    try:
        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)

        if not os.path.exists(base_dir):
            logger.error(f"仓库基础目录不存在: {base_dir}")
            return JsonResponse(
                {"status": "error", "message": f"仓库基础目录不存在: {base_dir}"}
            )

        # 获取基础目录下的所有子目录（仓库）
        repositories = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                # 检查是否包含平时成绩登记表
                excel_files = glob.glob(
                    os.path.join(item_path, "平时成绩登记表-*.xlsx")
                )
                if excel_files:
                    repositories.append(
                        {
                            "name": item,
                            "path": item,
                            "excel_count": len(excel_files),
                            "excel_files": [os.path.basename(f) for f in excel_files],
                        }
                    )

        logger.info(f"找到 {len(repositories)} 个包含成绩登记表的仓库")
        return JsonResponse({"status": "success", "repositories": repositories})

    except Exception as e:
        logger.error(f"获取仓库列表失败: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"获取仓库列表失败: {str(e)}"}
        )


def _execute_batch_grade_registration(request):
    """执行批量登分"""
    try:
        repository_name = request.POST.get("repository")
        if not repository_name:
            return JsonResponse({"status": "error", "message": "未选择仓库"})

        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 构建完整的仓库路径
        base_dir = os.path.expanduser(config.repo_base_dir)
        repository_path = os.path.join(base_dir, repository_name)

        if not os.path.exists(repository_path):
            return JsonResponse(
                {"status": "error", "message": f"仓库路径不存在: {repository_path}"}
            )

        logger.info(f"开始批量登分，仓库: {repository_path}")

        # 导入并执行批量登分逻辑
        from huali_edu.grade_registration import GradeRegistration

        grader = GradeRegistration()
        grader.repo_path = Path(repository_path)

        # 执行批量登分
        grader.process_docx_files(repository_path)

        logger.info(f"批量登分完成，仓库: {repository_path}")
        return JsonResponse(
            {"status": "success", "message": f"批量登分完成，仓库: {repository_name}"}
        )

    except Exception as e:
        logger.error(f"执行批量登分失败: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"执行批量登分失败: {str(e)}"}
        )


@login_required
@require_http_methods(["GET"])
def batch_grade_page(request):
    """批量登分页面"""
    try:
        # 检查用户权限
        if not request.user.is_authenticated:
            return HttpResponseForbidden("请先登录")

        if not request.user.is_staff:
            return HttpResponseForbidden("无权限访问")

        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir="~/jobs")

        return render(
            request,
            "batch_grade.html",
            {"config": config, "base_dir": os.path.expanduser(config.repo_base_dir)},
        )

    except Exception as e:
        logger.error(f"批量登分页面加载失败: {str(e)}")
        return HttpResponseServerError("页面加载失败".encode("utf-8"))


@method_decorator(csrf_exempt, name='dispatch')
class UploadAndScoreHomeworkView(View):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        # 保存文件
        save_path = os.path.join('media', file.name)
        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        # 读取Word内容
        try:
            doc = Document(save_path)
            content = '\n'.join([para.text for para in doc.paragraphs])
        except Exception as e:
            return JsonResponse({'error': f'Word解析失败: {str(e)}'}, status=500)
        # 调用火山引擎AI评分
        score, comment = volcengine_score_homework(content)
        return JsonResponse({'score': score, 'comment': comment})

def convert_score_to_grade(score):
    """将百分制分数转换为等级"""
    if score is None:
        return "N/A"
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "E"

def _perform_ai_scoring_for_file(full_path, base_dir):
    """对单个文件执行AI评分的核心逻辑"""
    try:
        logger.info(f"=== 开始AI评分文件: {os.path.basename(full_path)} ===")
        
        # 提取文件内容为纯文本
        _, ext = os.path.splitext(full_path)
        logger.info(f"文件扩展名: {ext}")
        
        content = ""
        if ext.lower() == ".docx":
            try:
                logger.info("尝试读取Word文档内容...")
                with open(full_path, "rb") as docx_file:
                    # 使用convert_to_html然后提取纯文本
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value
                    # 使用python-docx作为备选方案
                    try:
                        from docx import Document
                        doc = Document(full_path)
                        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                        logger.info(f"使用python-docx读取Word文档内容，长度: {len(content)}")
                    except Exception as docx_error:
                        logger.warning(f"python-docx读取失败: {docx_error}")
                        # 如果python-docx也失败，尝试从HTML中提取文本
                        import re
                        content = re.sub(r'<[^>]+>', '', html_content)
                        logger.info(f"从HTML中提取文本，长度: {len(content)}")
            except Exception as e:
                logger.error(f"读取Word文件失败: {e}")
                raise ValueError(f"无法读取Word文件内容: {e}")
        else:
            try:
                logger.info("尝试读取文本文件内容...")
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(f"文本文件内容长度: {len(content)}")
            except Exception as e:
                logger.error(f"读取文本文件失败: {e}")
                raise ValueError(f"无法读取文件内容: {e}")

        if not content.strip():
            logger.error("文件内容为空")
            raise ValueError("文件内容为空，无法评分")

        logger.info("开始调用火山引擎AI评分...")
        # 调用AI评分
        score, comment = volcengine_score_homework(content)
        logger.info(f"AI评分结果 - 分数: {score}, 评语长度: {len(comment) if comment else 0}")
        
        grade = convert_score_to_grade(score)
        logger.info(f"转换后的等级: {grade}")

        logger.info("开始写入AI评价到文件...")
        # 将AI评价和评分写入文件和Excel
        # 1. 写入评语
        save_teacher_comment_logic(full_path, f"【AI评价】\n{comment}")
        logger.info("AI评价已写入文件")
        
        logger.info("开始写入评分到文件...")
        # 2. 写入等级
        add_grade_to_file_logic(full_path, grade, base_dir)
        logger.info("评分已写入文件")

        logger.info("AI评分流程完成")
        return {"success": True, "score": score, "grade": grade, "comment": comment}
    except Exception as e:
        logger.error(f"AI评分文件 '{os.path.basename(full_path)}' 失败: {e}")
        return {"success": False, "error": str(e)}

@login_required
@require_http_methods(["POST"])
def ai_score_view(request):
    """使用AI评分并保存结果的视图（单个文件）"""
    try:
        logger.info("=== 开始处理单个文件AI评分请求 ===")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求POST数据: {request.POST}")
        
        path = request.POST.get("path")
        logger.info(f"文件路径: {path}")
        
        if not path:
            logger.error("未提供文件路径")
            return JsonResponse({"status": "error", "message": "未提供文件路径"}, status=400)

        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"}, status=500)

        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, path)
        
        logger.info(f"基础目录: {base_dir}")
        logger.info(f"完整文件路径: {full_path}")

        if not os.path.exists(full_path):
            logger.error(f"文件不存在: {full_path}")
            return JsonResponse({"status": "error", "message": "文件不存在"}, status=404)

        logger.info("开始执行AI评分...")
        result = _perform_ai_scoring_for_file(full_path, base_dir)
        logger.info(f"AI评分结果: {result}")

        if result["success"]:
            logger.info("AI评分成功")
            return JsonResponse({
                "status": "success",
                "message": "AI评分完成",
                "score": result["score"],
                "grade": result["grade"],
                "comment": result["comment"]
            })
        else:
            logger.error(f"AI评分失败: {result['error']}")
            return JsonResponse({"status": "error", "message": result["error"]}, status=500)

    except Exception as e:
        logger.error(f"AI评分视图异常: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"status": "error", "message": "服务器内部错误"}, status=500)

@login_required
@require_http_methods(["POST"])
def batch_ai_score_view(request):
    """对指定目录下的所有文件进行批量AI评分"""
    try:
        logger.info("开始处理批量AI评分请求")
        path = request.POST.get("path")
        if not path:
            return JsonResponse({"status": "error", "message": "未提供目录路径"}, status=400)

        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"}, status=500)

        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, path)

        if not os.path.isdir(full_path):
            return JsonResponse({"status": "error", "message": "提供的路径不是一个目录"}, status=400)

        results = []
        success_count = 0
        error_count = 0

        for filename in os.listdir(full_path):
            file_path = os.path.join(full_path, filename)
            # 只处理文件，不处理子目录
            if os.path.isfile(file_path) and (filename.endswith('.docx') or filename.endswith('.txt')):
                result = _perform_ai_scoring_for_file(file_path, base_dir)
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
                results.append({"file": filename, **result})

        return JsonResponse({
            "status": "success",
            "message": f"批量评分完成，成功 {success_count} 个，失败 {error_count} 个。",
            "results": results
        })

    except Exception as e:
        logger.error(f"""批量AI评分视图异常: {str(e)}
{traceback.format_exc()}""")
        return JsonResponse({"status": "error", "message": "服务器内部错误"}, status=500)

def save_teacher_comment_logic(full_path, comment):
    # (此为save_teacher_comment视图的逻辑提取，用于复用)
    _, ext = os.path.splitext(full_path)
    if ext.lower() == ".docx":
        doc = Document(full_path)
        # ... (此处省略了删除旧评价和添加复杂格式的逻辑，简化为直接添加)
        doc.add_paragraph(f"教师评价：{comment}")
        doc.save(full_path)
    else:
        with open(full_path, "a", encoding="utf-8") as f:
            f.write(f"\n教师评价：{comment}\n")

def add_grade_to_file_logic(full_path, grade, base_dir):
    # (此为add_grade_to_file视图的逻辑提取，用于复用)
    _, ext = os.path.splitext(full_path)
    if ext.lower() == ".docx":
        doc = Document(full_path)
        # ... (省略了在表格中查找的复杂逻辑，简化为在末尾添加)
        doc.add_paragraph(f"老师评分：{grade}")
        doc.save(full_path)
    else:
        with open(full_path, "a", encoding="utf-8") as f:
            f.write(f"\n老师评分：{grade}\n")
    
    # 登记到Excel
    try:
        from huali_edu.grade_registration import GradeRegistration
        grader = GradeRegistration()
        rel_path = os.path.relpath(full_path, base_dir)
        path_parts = rel_path.split(os.sep)
        if len(path_parts) >= 3:
            repo_dir = path_parts[0]
            homework_dir = path_parts[1]
            file_name = path_parts[2]
            student_name = os.path.splitext(file_name)[0]
            repo_abs_path = os.path.join(base_dir, repo_dir)
            excel_files = list(Path(repo_abs_path).glob("平时成绩登记表-*.xlsx"))
            if excel_files:
                excel_path = str(excel_files[0])
                grader.write_grade_to_excel(
                    excel_path=excel_path,
                    student_name=student_name,
                    homework_dir_name=homework_dir,
                    grade=grade,
                )
                logger.info(f"AI评分已登记到Excel: {excel_path}")
            else:
                logger.warning(f"未找到对应的Excel成绩登记表: {repo_abs_path}")
    except Exception as e:
        logger.error(f"登记AI评分到Excel失败: {e}")
        # 即使登记失败，也应该认为评分本身是成功的，所以不抛出异常

def volcengine_score_homework(content):
    logger.info("=== 开始调用火山引擎AI评分 ===")
    logger.info(f"输入内容长度: {len(content)}")
    logger.info(f"输入内容前100字符: {content[:100]}...")

    # 使用火山引擎Ark API
    api_key = "e7a701b6-3bc7-470a-8d1f-2a289dd015da"
    client = Ark(api_key=api_key)
    
    prompt = f"请为以下学生作业打分（满分100分），并给出百字以内的简短评语：\n{content}"
    logger.info(f"发送给AI的提示词长度: {len(prompt)}")
    
    try:
        logger.info("正在调用火山引擎API...")
        
        # 调用API
        resp = client.chat.completions.create(
            model="deepseek-r1-250528",
            messages=[{"content": prompt, "role": "user"}],
        )
        
        logger.info(f"火山引擎API响应类型: {type(resp)}")
        logger.info(f"火山引擎API响应: {resp}")
        
        # 提取响应内容
        result = resp.choices[0].message.content
        logger.info(f"成功提取AI回复内容，长度: {len(result)}")
            
    except Exception as e:
        logger.error(f"调用火山引擎AI评分失败: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        result = ""
    
    # 简单提取分数和评语（可根据实际返回格式优化）
    import re
    logger.info(f"开始从回复中提取分数，回复内容: {result}")
    score_match = re.search(r'(\d{1,3})分', result)
    if score_match:
        score = int(score_match.group(1))
        logger.info(f"成功提取分数: {score}")
    else:
        score = None
        logger.warning("未能从回复中提取到分数")
    
    comment = result
    logger.info(f"AI评分完成 - 分数: {score}, 评语长度: {len(comment)}")
    return score, comment