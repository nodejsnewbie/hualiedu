import glob
import logging
import os
import subprocess
import threading

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import ConversionLog, FileConversionTask

logger = logging.getLogger(__name__)


@login_required
def toolbox_index(request):
    """工具箱首页"""
    return render(request, "toolbox/index.html")


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
