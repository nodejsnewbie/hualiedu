import glob
import os
import shutil
import subprocess
import threading
import zipfile

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from grading.grade_registry_writer import GradeFileProcessor
from grading.models import Repository

from .models import ConversionLog, FileConversionTask
from .utils import AssignmentImportError, import_assignment_scores_to_gradebook
from .views import convert_ppt_to_pdf_task


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


def _serialize_task(task: FileConversionTask) -> dict:
    return {
        "id": task.id,
        "task_type": task.task_type,
        "task_type_display": task.get_task_type_display(),
        "status": task.status,
        "status_display": task.get_status_display(),
        "source_directory": task.source_directory,
        "output_directory": task.output_directory,
        "total_files": task.total_files,
        "processed_files": task.processed_files,
        "success_files": task.success_files,
        "failed_files": task.failed_files,
        "error_message": task.error_message,
        "progress_percentage": task.progress_percentage,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _serialize_log(log: ConversionLog) -> dict:
    return {
        "id": log.id,
        "file_name": log.file_name,
        "status": log.status,
        "status_display": log.get_status_display(),
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat(),
    }


def _unique_extract_dir(base_dir: str, name: str) -> str:
    candidate = os.path.join(base_dir, name)
    if not os.path.exists(candidate):
        return candidate
    index = 1
    while True:
        next_candidate = f"{candidate}_{index}"
        if not os.path.exists(next_candidate):
            return next_candidate
        index += 1


def _find_7z_executable() -> str | None:
    env_path = os.environ.get("SEVEN_ZIP_PATH", "").strip()
    if env_path and os.path.exists(env_path):
        return env_path

    candidate = shutil.which("7z") or shutil.which("7za")
    if candidate:
        return candidate

    common_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


def batch_unzip_api(request):
    source_dir = request.POST.get("source_directory", "").strip()
    file_type = request.POST.get("file_type", "all").strip().lower()
    if not source_dir:
        return JsonResponse({"status": "error", "message": "请填写源目录"}, status=400)
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return JsonResponse({"status": "error", "message": "源目录不存在"}, status=400)

    allowed_exts = {".zip", ".rar"}
    if file_type == "zip":
        allowed_exts = {".zip"}
    elif file_type == "rar":
        allowed_exts = {".rar"}
    elif file_type != "all":
        return JsonResponse({"status": "error", "message": "不支持的文件类型"}, status=400)

    archive_files = []
    for filename in sorted(os.listdir(source_dir)):
        if filename.startswith("~$"):
            continue
        lower_name = filename.lower()
        _, ext = os.path.splitext(lower_name)
        if ext in allowed_exts:
            archive_files.append(filename)

    if not archive_files:
        return JsonResponse({"status": "error", "message": "目录中未找到匹配的压缩文件"}, status=400)

    processed = []
    errors = []

    for filename in archive_files:
        file_path = os.path.join(source_dir, filename)
        base_name, ext = os.path.splitext(filename)
        extract_dir = _unique_extract_dir(source_dir, base_name)
        try:
            os.makedirs(extract_dir, exist_ok=True)
            if ext.lower() == ".zip":
                with zipfile.ZipFile(file_path) as zf:
                    zf.extractall(extract_dir)
            elif ext.lower() == ".rar":
                seven_zip = _find_7z_executable()
                if not seven_zip:
                    raise RuntimeError("未找到 7z，无法解压 RAR")
                result = subprocess.run(
                    [seven_zip, "x", "-y", f"-o{extract_dir}", file_path],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or "7z 解压失败")
            else:
                raise RuntimeError("不支持的压缩格式")
            processed.append(
                {
                    "file_name": filename,
                    "extract_dir": extract_dir,
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "file_name": filename,
                    "error": f"解压失败: {str(exc)}",
                }
            )

    result = {
        "source_directory": source_dir,
        "file_type": file_type,
        "total_files": len(archive_files),
        "success_count": len(processed),
        "error_count": len(errors),
        "processed": processed,
        "errors": errors,
    }

    return JsonResponse({"status": "success", "result": result})


@login_required
@require_http_methods(["GET"])
def repository_list_api(request):
    repositories_qs = Repository.objects.filter(owner=request.user, is_active=True).order_by(
        "-created_at"
    )
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
    return JsonResponse({"status": "success", "repositories": repository_options})


@login_required
@require_http_methods(["POST"])
def assignment_grade_import_api(request):
    repo_id = request.POST.get("selected_repo_id") or ""
    course_name = request.POST.get("selected_course", "").strip()
    class_relative_path = request.POST.get("class_directory", "").strip()

    if not repo_id:
        return JsonResponse({"status": "error", "message": "请选择仓库"}, status=400)
    if not course_name:
        return JsonResponse({"status": "error", "message": "请选择课程"}, status=400)
    if not class_relative_path:
        return JsonResponse({"status": "error", "message": "请选择班级目录"}, status=400)

    try:
        repository = Repository.objects.get(id=repo_id, owner=request.user, is_active=True)
    except Repository.DoesNotExist:
        return JsonResponse({"status": "error", "message": "仓库不存在或无权限访问"}, status=404)

    base_dir = os.path.abspath(repository.get_full_path())
    course_path = os.path.normpath(os.path.join(base_dir, course_name))
    if not course_path.startswith(base_dir) or not os.path.isdir(course_path):
        return JsonResponse({"status": "error", "message": "课程目录不存在"}, status=400)

    class_dir = os.path.normpath(os.path.join(course_path, class_relative_path))
    if not class_dir.startswith(course_path) or not os.path.isdir(class_dir):
        return JsonResponse({"status": "error", "message": "班级目录不存在"}, status=400)

    gradebook_file = os.path.join(class_dir, "成绩登记册.xlsx")
    if not os.path.exists(gradebook_file):
        return JsonResponse({"status": "error", "message": "班级目录中未找到成绩登记册.xlsx"}, status=400)

    assignment_files = []
    for filename in sorted(os.listdir(class_dir)):
        if filename.startswith("~$"):
            continue
        if filename == "成绩登记册.xlsx":
            continue
        if not filename.lower().endswith(".xlsx"):
            continue
        file_path = os.path.join(class_dir, filename)
        homework_number = GradeFileProcessor.extract_homework_number_from_filename(file_path)
        if homework_number is not None:
            assignment_files.append((homework_number, file_path, filename))

    if not assignment_files:
        return JsonResponse({"status": "error", "message": "未找到作业成绩文件"}, status=400)

    processed = []
    errors = []
    for homework_number, file_path, display_name in sorted(assignment_files, key=lambda item: item[0]):
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
                    "assignment_column_letter": stats["assignment_column_letter"],
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
        except Exception:
            errors.append(
                {
                    "file_name": display_name,
                    "assignment_number": homework_number,
                    "error": "写入失败，请查看日志",
                }
            )

    result = {
        "repository_name": repository.name,
        "course_name": course_name,
        "class_directory": class_dir,
        "gradebook_file": gradebook_file,
        "total_files": len(assignment_files),
        "success_count": len(processed),
        "error_count": len(errors),
        "processed": processed,
        "errors": errors,
    }

    return JsonResponse({"status": "success", "result": result})


@login_required
@require_http_methods(["GET", "POST"])
def task_list_create_api(request):
    if request.method == "GET":
        limit = request.GET.get("limit")
        tasks_qs = FileConversionTask.objects.filter(user=request.user).order_by("-created_at")
        if limit:
            try:
                tasks_qs = tasks_qs[: int(limit)]
            except (TypeError, ValueError):
                tasks_qs = tasks_qs[:20]
        tasks = [_serialize_task(task) for task in tasks_qs]
        return JsonResponse({"status": "success", "tasks": tasks})

    task_type = request.POST.get("task_type", "ppt_to_pdf").strip()
    source_dir = request.POST.get("source_directory", "").strip()
    output_dir = request.POST.get("output_directory", "").strip()

    if task_type != "ppt_to_pdf":
        return JsonResponse({"status": "error", "message": "不支持的任务类型"}, status=400)
    if not source_dir or not output_dir:
        return JsonResponse({"status": "error", "message": "请填写源目录与输出目录"}, status=400)
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return JsonResponse({"status": "error", "message": "源目录不存在"}, status=400)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as exc:
            return JsonResponse(
                {"status": "error", "message": f"无法创建输出目录: {str(exc)}"}, status=400
            )

    ppt_files = glob.glob(os.path.join(source_dir, "*.ppt")) + glob.glob(
        os.path.join(source_dir, "*.pptx")
    )
    if not ppt_files:
        return JsonResponse({"status": "error", "message": "源目录中未找到PPT文件"}, status=400)

    task = FileConversionTask.objects.create(
        user=request.user,
        task_type="ppt_to_pdf",
        source_directory=source_dir,
        output_directory=output_dir,
        total_files=len(ppt_files),
        status="pending",
    )

    thread = threading.Thread(target=convert_ppt_to_pdf_task, args=(task.id,))
    thread.daemon = True
    thread.start()

    return JsonResponse({"status": "success", "task": _serialize_task(task)})


@login_required
@require_http_methods(["GET"])
def task_detail_api(request, task_id):
    try:
        task = FileConversionTask.objects.get(id=task_id, user=request.user)
    except FileConversionTask.DoesNotExist:
        return JsonResponse({"status": "error", "message": "任务不存在"}, status=404)

    logs = ConversionLog.objects.filter(task=task).order_by("-created_at")
    return JsonResponse(
        {
            "status": "success",
            "task": _serialize_task(task),
            "logs": [_serialize_log(log) for log in logs],
        }
    )


@login_required
@require_http_methods(["POST"])
def task_delete_api(request, task_id):
    try:
        task = FileConversionTask.objects.get(id=task_id, user=request.user)
    except FileConversionTask.DoesNotExist:
        return JsonResponse({"status": "error", "message": "任务不存在"}, status=404)
    task.delete()
    return JsonResponse({"status": "success", "message": "任务已删除"})
