import glob
import json
import logging
import os
import subprocess
import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from grading.grade_registry_writer import GradeFileProcessor
from grading.models import Repository

from .models import ConversionLog, FileConversionTask
from .utils import AssignmentImportError, import_assignment_scores_to_gradebook

logger = logging.getLogger(__name__)


def _list_repo_courses(repo_path: str) -> list[str]:
    courses = []
    try:
        for name in sorted(os.listdir(repo_path)):
            if name.startswith("."):
                continue
            full_path = os.path.join(repo_path, name)
            if os.path.isdir(full_path):
                courses.append(name)
    except OSError:
        return []
    return courses


@login_required
def toolbox_index(request):
    """工具箱首页"""
    tasks = FileConversionTask.objects.filter(user=request.user).order_by("-created_at")[:10]
    return render(request, "toolbox/index.html", {"tasks": tasks})


@login_required
def assignment_grade_import_view(request):
    """作业成绩写入成绩登分册"""
    repositories_qs = Repository.objects.filter(owner=request.user, is_active=True)
    repository_options = []
    for repo in repositories_qs:
        repo_path = os.path.abspath(repo.get_full_path())
        repository_options.append(
            {
                "id": str(repo.id),
                "name": repo.name,
                "path": repo_path,
                "courses": _list_repo_courses(repo_path),
            }
        )

    selected_repo = repository_options[0] if repository_options else None
    current_courses = selected_repo["courses"] if selected_repo else []

    form_data = {
        "class_directory": "",
        "class_directory_display": "",
        "selected_repo_id": selected_repo["id"] if selected_repo else "",
        "selected_repo_name": selected_repo["name"] if selected_repo else "",
        "selected_course": current_courses[0] if current_courses else "",
    }
    result = None

    if request.method == "POST" and repository_options:
        repo_id = request.POST.get("selected_repo_id") or ""
        selected_repo = next(
            (repo for repo in repository_options if repo["id"] == repo_id),
            repository_options[0],
        )
        form_data["selected_repo_id"] = selected_repo["id"]
        form_data["selected_repo_name"] = selected_repo["name"]
        current_courses = selected_repo["courses"]

        selected_course = request.POST.get("selected_course", "").strip()
        if selected_course not in current_courses:
            selected_course = current_courses[0] if current_courses else ""
        form_data["selected_course"] = selected_course

        class_relative_path = request.POST.get("class_directory", "").strip()
        form_data["class_directory"] = class_relative_path

        base_dir = selected_repo["path"]
        if not selected_course:
            messages.error(request, "该仓库下没有可用课程")
        else:
            course_path = os.path.normpath(os.path.join(base_dir, selected_course))
            if not course_path.startswith(base_dir) or not os.path.isdir(course_path):
                messages.error(request, "课程目录不存在或不是有效目录")
            else:
                class_dir = os.path.normpath(os.path.join(course_path, class_relative_path))

                if not class_relative_path:
                    messages.error(request, "请在课程目录中选择班级")
                elif not class_dir.startswith(course_path):
                    messages.error(request, "无效的班级目录")
                elif not os.path.isdir(class_dir):
                    messages.error(request, "班级目录不存在或不是有效目录")
                else:
                    form_data["class_directory_display"] = class_dir
                    gradebook_file = os.path.join(class_dir, "成绩登分册.xlsx")
                    if not os.path.exists(gradebook_file):
                        messages.error(
                            request, f"班级目录中未找到成绩登分册.xlsx（{gradebook_file}）"
                        )
                    else:
                        assignment_files = []
                        for filename in sorted(os.listdir(class_dir)):
                            if filename.startswith("~$"):
                                continue
                            if filename == "成绩登分册.xlsx":
                                continue
                            if not filename.lower().endswith(".xlsx"):
                                continue
                            file_path = os.path.join(class_dir, filename)
                            homework_number = (
                                GradeFileProcessor.extract_homework_number_from_filename(file_path)
                            )
                            if homework_number is not None:
                                assignment_files.append((homework_number, file_path, filename))

                        if not assignment_files:
                            messages.warning(
                                request,
                                "未在班级目录中找到形如“第X次作业.xlsx”的成绩文件",
                            )
                        else:
                            processed = []
                            errors = []
                            for homework_number, file_path, display_name in sorted(
                                assignment_files, key=lambda item: item[0]
                            ):
                                try:
                                    stats = import_assignment_scores_to_gradebook(
                                        file_path,
                                        gradebook_file,
                                        homework_number,
                                    )
                                    processed.append(
                                        {
                                            "file_name": display_name,
                                            "assignment_number": homework_number,
                                            "assignment_column_letter": stats[
                                                "assignment_column_letter"
                                            ],
                                            "updated_students": stats["updated_students"],
                                            "missing_in_gradebook": stats["missing_in_gradebook"],
                                            "missing_in_assignment": stats["missing_in_assignment"],
                                        }
                                    )
                                except AssignmentImportError as exc:
                                    errors.append(
                                        {
                                            "file_name": display_name,
                                            "assignment_number": homework_number,
                                            "error": str(exc),
                                        }
                                    )
                                except Exception as exc:  # pragma: no cover
                                    logger.exception(
                                        "导入作业成绩失败: %s", display_name, exc_info=exc
                                    )
                                    errors.append(
                                        {
                                            "file_name": display_name,
                                            "assignment_number": homework_number,
                                            "error": "写入失败，请查看日志",
                                        }
                                    )

                            if processed:
                                messages.success(
                                    request,
                                    f"成功写入 {len(processed)} 个作业成绩（班级：{class_dir}）",
                                )
                            if errors:
                                messages.warning(
                                    request,
                                    f"{len(errors)} 个作业文件写入失败，请查看结果详情",
                                )

                            result = {
                                "repository_name": selected_repo["name"],
                                "course_name": selected_course,
                                "class_directory": class_dir,
                                "gradebook_file": gradebook_file,
                                "total_files": len(assignment_files),
                                "success_count": len(processed),
                                "error_count": len(errors),
                                "processed": processed,
                                "errors": errors,
                            }

    context = {
        "form_data": form_data,
        "result": result,
        "repositories": repository_options,
        "courses": current_courses,
    }

    if repository_options:
        context["tree_api_url"] = reverse("toolbox:class_directory_tree")
        context["repositories_json"] = json.dumps(repository_options, ensure_ascii=False)

    return render(
        request,
        "toolbox/assignment_grade_import.html",
        context,
    )


@login_required
def ppt_to_pdf_view(request):
    """PPT转PDF页面"""
    if request.method == "POST":
        source_dir = request.POST.get("source_directory", "").strip()
        output_dir = request.POST.get("output_directory", "").strip()

        # 验证目录
        if not source_dir or not output_dir:
            messages.error(request, "请填写源目录和输出目录")
            return redirect("toolbox:ppt_to_pdf")

        if not os.path.exists(source_dir):
            messages.error(request, "源目录不存在")
            return redirect("toolbox:ppt_to_pdf")

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messages.error(request, f"无法创建输出目录: {str(e)}")
                return redirect("toolbox:ppt_to_pdf")

        # 检查PPT文件
        ppt_files = glob.glob(os.path.join(source_dir, "*.ppt")) + glob.glob(
            os.path.join(source_dir, "*.pptx")
        )
        if not ppt_files:
            messages.error(request, "源目录中没有找到PPT文件")
            return redirect("toolbox:ppt_to_pdf")

        # 创建转换任务
        task = FileConversionTask.objects.create(
            user=request.user,
            task_type="ppt_to_pdf",
            source_directory=source_dir,
            output_directory=output_dir,
            total_files=len(ppt_files),
            status="pending",
        )

        # 启动后台转换任务
        thread = threading.Thread(target=convert_ppt_to_pdf_task, args=(task.id,))
        thread.daemon = True
        thread.start()

        messages.success(request, f"转换任务已创建，共发现 {len(ppt_files)} 个PPT文件")
        return redirect("toolbox:task_detail", task_id=task.id)

    # 获取用户的任务列表
    tasks = FileConversionTask.objects.filter(user=request.user).order_by("-created_at")[:10]

    return render(request, "toolbox/ppt_to_pdf.html", {"tasks": tasks})


@login_required
def task_list_view(request):
    """任务列表页面"""
    tasks = FileConversionTask.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "toolbox/task_list.html", {"tasks": tasks})


@login_required
def task_detail_view(request, task_id):
    """任务详情页面"""
    try:
        task = FileConversionTask.objects.get(id=task_id, user=request.user)
        logs = ConversionLog.objects.filter(task=task).order_by("-created_at")
    except FileConversionTask.DoesNotExist:
        messages.error(request, "任务不存在")
        return redirect("toolbox:task_list")

    return render(request, "toolbox/task_detail.html", {"task": task, "logs": logs})


@login_required
@require_http_methods(["POST"])
def delete_task_view(request, task_id):
    """删除任务"""
    try:
        task = FileConversionTask.objects.get(id=task_id, user=request.user)
        task.delete()
        messages.success(request, "任务已删除")
    except FileConversionTask.DoesNotExist:
        messages.error(request, "任务不存在")

    return redirect("toolbox:task_list")


@login_required
def task_status_api(request, task_id):
    """获取任务状态的API"""
    try:
        task = FileConversionTask.objects.get(id=task_id, user=request.user)
        return JsonResponse(
            {
                "status": "success",
                "data": {
                    "id": task.id,
                    "status": task.status,
                    "total_files": task.total_files,
                    "processed_files": task.processed_files,
                    "success_files": task.success_files,
                    "failed_files": task.failed_files,
                    "progress_percentage": task.progress_percentage,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                },
            }
        )
    except FileConversionTask.DoesNotExist:
        return JsonResponse({"status": "error", "message": "任务不存在"})


@login_required
def browse_directory_api(request):
    """浏览目录的API"""
    try:
        path = request.GET.get("path", "/")

        # 安全检查：确保路径在允许的范围内
        if not os.path.exists(path) or not os.path.isdir(path):
            return JsonResponse({"status": "error", "message": "目录不存在或不是有效目录"})

        # 获取目录内容
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append({"name": item, "type": "directory", "path": item_path})
                elif item.lower().endswith((".ppt", ".pptx")):
                    items.append({"name": item, "type": "file", "path": item_path})
        except PermissionError:
            return JsonResponse({"status": "error", "message": "没有权限访问该目录"})

        # 按类型和名称排序
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

        return JsonResponse(
            {
                "status": "success",
                "data": {
                    "current_path": path,
                    "parent_path": os.path.dirname(path) if path != "/" else None,
                    "items": items,
                },
            }
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"浏览目录失败: {str(e)}"})


@login_required
def class_directory_tree_api(request):
    """返回用户仓库下的目录树（仅目录）"""
    repo_id = request.GET.get("repo_id")
    course_name = request.GET.get("course", "").strip()
    rel_path = request.GET.get("path", "").strip()

    if not repo_id:
        return JsonResponse({"children": []}, status=400)

    try:
        repository = Repository.objects.get(id=repo_id, owner=request.user, is_active=True)
    except Repository.DoesNotExist:
        return JsonResponse({"children": []}, status=404)

    base_dir = os.path.abspath(repository.get_full_path())
    if not course_name:
        return JsonResponse({"children": []}, status=400)

    course_path = os.path.normpath(os.path.join(base_dir, course_name))
    if not course_path.startswith(base_dir) or not os.path.isdir(course_path):
        return JsonResponse({"children": []}, status=400)

    target_path = os.path.normpath(os.path.join(course_path, rel_path))
    if not target_path.startswith(course_path):
        return JsonResponse({"children": []}, status=400)
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        return JsonResponse({"children": []})

    children = []
    for name in sorted(os.listdir(target_path)):
        if name.startswith("."):
            continue
        full_path = os.path.join(target_path, name)
        if not os.path.isdir(full_path):
            continue
        rel_child = os.path.relpath(full_path, course_path)
        rel_child = rel_child.replace("\\", "/")
        if rel_child == ".":
            rel_child = ""
        children.append(
            {
                "id": rel_child,
                "text": name,
                "children": _directory_has_subdirs(full_path),
                "data": {"relative_path": rel_child},
            }
        )

    return JsonResponse({"children": children})


def _directory_has_subdirs(path: str) -> bool:
    try:
        for item in os.listdir(path):
            if item.startswith("."):
                continue
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                return True
    except OSError:
        return False
    return False


def convert_ppt_to_pdf_task(task_id):
    """后台PPT转PDF任务"""
    try:
        task = FileConversionTask.objects.get(id=task_id)
        task.status = "processing"
        task.save()

        source_dir = task.source_directory
        output_dir = task.output_directory

        # 获取所有PPT文件
        ppt_files = glob.glob(os.path.join(source_dir, "*.ppt")) + glob.glob(
            os.path.join(source_dir, "*.pptx")
        )

        success_count = 0
        failed_count = 0

        for ppt_file in ppt_files:
            try:
                file_name = os.path.basename(ppt_file)
                pdf_file = os.path.join(output_dir, os.path.splitext(file_name)[0] + ".pdf")

                # 记录开始转换
                ConversionLog.objects.create(task=task, file_name=file_name, status="processing")

                # 使用libreoffice进行转换
                result = convert_ppt_to_pdf_libreoffice(ppt_file, pdf_file)

                if result["success"]:
                    success_count += 1
                    ConversionLog.objects.create(task=task, file_name=file_name, status="completed")
                    logger.info(f"成功转换: {file_name}")
                else:
                    failed_count += 1
                    ConversionLog.objects.create(
                        task=task,
                        file_name=file_name,
                        status="failed",
                        error_message=result["error"],
                    )
                    logger.error(f"转换失败: {file_name} - {result['error']}")

                task.processed_files += 1
                task.success_files = success_count
                task.failed_files = failed_count
                task.save()

            except Exception as e:
                failed_count += 1
                task.processed_files += 1
                task.failed_files = failed_count
                task.save()

                ConversionLog.objects.create(
                    task=task,
                    file_name=os.path.basename(ppt_file),
                    status="failed",
                    error_message=str(e),
                )
                logger.error(f"转换异常: {os.path.basename(ppt_file)} - {str(e)}")

        # 更新任务状态
        task.status = "completed" if failed_count == 0 else "failed"
        if failed_count > 0:
            task.error_message = f"成功转换 {success_count} 个文件，失败 {failed_count} 个文件"
        task.save()

        logger.info(f"任务完成: {task.id} - 成功: {success_count}, 失败: {failed_count}")

    except Exception as e:
        logger.error(f"任务执行异常: {task_id} - {str(e)}")
        try:
            task = FileConversionTask.objects.get(id=task_id)
            task.status = "failed"
            task.error_message = str(e)
            task.save()
        except Exception:
            pass


def convert_ppt_to_pdf_libreoffice(ppt_file, pdf_file):
    """使用LibreOffice转换PPT到PDF"""
    try:
        # 检查LibreOffice是否安装
        result = subprocess.run(["which", "libreoffice"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"success": False, "error": "LibreOffice未安装，请先安装LibreOffice"}

        # 使用LibreOffice进行转换
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            os.path.dirname(pdf_file),
            ppt_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and os.path.exists(pdf_file):
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": f"转换失败: {result.stderr}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "转换超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 批量登分功能 ====================


@login_required
@require_http_methods(["GET"])
def batch_grade_page(request):
    """批量登分页面"""
    try:
        # 检查用户权限
        if not request.user.is_staff:
            messages.error(request, "无权限访问")
            return redirect("toolbox:index")

        # 获取全局配置
        from grading.models import GlobalConfig

        repo_base_dir = GlobalConfig.get_value("default_repo_base_dir", "~/jobs")
        base_dir = os.path.expanduser(repo_base_dir)

        return render(
            request,
            "toolbox/batch_grade.html",
            {"config": None, "base_dir": base_dir},
        )

    except Exception as e:
        logger.error(f"批量登分页面加载失败: {str(e)}")
        messages.error(request, f"页面加载失败: {str(e)}")
        return redirect("toolbox:index")


@login_required
@require_http_methods(["GET", "POST"])
def batch_grade_api(request):
    """批量登分API"""
    try:
        # 检查用户权限
        if not request.user.is_staff:
            return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

        if request.method == "GET":
            # 获取仓库列表
            return _get_batch_grade_repository_list(request)
        elif request.method == "POST":
            # 执行批量登分
            return _execute_batch_grade(request)

    except Exception as e:
        logger.error(f"批量登分API处理失败: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"处理失败: {str(e)}"},
            status=500,
        )


def _get_batch_grade_repository_list(request):
    """获取包含成绩登记表的仓库列表"""
    try:
        from grading.models import GlobalConfig

        # 从全局配置获取仓库基础目录
        repo_base_dir = GlobalConfig.get_value("default_repo_base_dir")
        if not repo_base_dir:
            logger.error("未配置仓库基础目录")
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(repo_base_dir)

        if not os.path.exists(base_dir):
            logger.error(f"仓库基础目录不存在: {base_dir}")
            return JsonResponse({"status": "error", "message": f"仓库基础目录不存在: {base_dir}"})

        # 获取基础目录下的所有子目录（仓库）
        repositories = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                # 检查是否包含平时成绩登记表
                excel_files = glob.glob(os.path.join(item_path, "平时成绩登记表-*.xlsx"))
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
        return JsonResponse({"status": "error", "message": f"获取仓库列表失败: {str(e)}"})


def _execute_batch_grade(request):
    """执行批量登分"""
    try:
        from pathlib import Path

        from grading.models import GlobalConfig

        repository_name = request.POST.get("repository")
        if not repository_name:
            return JsonResponse({"status": "error", "message": "未选择仓库"})

        # 从全局配置获取仓库基础目录
        repo_base_dir = GlobalConfig.get_value("default_repo_base_dir")
        if not repo_base_dir:
            return JsonResponse({"status": "error", "message": "未配置仓库基础目录"})

        # 构建完整的仓库路径
        base_dir = os.path.expanduser(repo_base_dir)
        repository_path = os.path.join(base_dir, repository_name)

        if not os.path.exists(repository_path):
            return JsonResponse(
                {"status": "error", "message": f"仓库路径不存在: {repository_path}"}
            )

        logger.info(f"开始批量登分，仓库: {repository_path}")

        # 导入并执行批量登分逻辑
        try:
            from grading.grade_registry_writer import GradeRegistryWriter

            writer = GradeRegistryWriter()
            result = writer.batch_write_grades_from_repository(repository_path)

            logger.info(f"批量登分完成，仓库: {repository_path}")
            return JsonResponse({"status": "success", "message": f"批量登分完成", "data": result})
        except ImportError:
            logger.error("GradeRegistryWriter 模块未找到")
            return JsonResponse(
                {"status": "error", "message": "批量登分功能模块未找到，请检查系统配置"}
            )

    except Exception as e:
        logger.error(f"执行批量登分失败: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return JsonResponse({"status": "error", "message": f"执行批量登分失败: {str(e)}"})
