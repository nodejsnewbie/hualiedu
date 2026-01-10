"""
作业管理视图 (Assignment Management Views)

本模块提供作业配置的Web界面，包括创建、列表、编辑和删除功能。

视图列表：
1. assignment_list_view: 作业配置列表页面
2. assignment_create_view: 创建作业配置页面
3. assignment_edit_view: 编辑作业配置页面
4. assignment_delete_view: 删除作业配置（软删除）
5. get_assignment_structure_api: 获取作业目录结构API
6. get_assignment_file_api: 获取作业文件内容API

设计原则：
- 用户友好：使用"作业管理"而非"仓库管理"术语
- 简化操作：隐藏Git同步等技术操作
- 教师隔离：每个教师只能看到自己创建的作业配置
- 实时访问：Git方式直接从远程仓库读取，无需同步

术语变更：
- Repository → Assignment（作业配置）
- Repository Management → Assignment Management（作业管理）
- Sync → 移除（不再需要同步操作）

实现需求：
- Requirements 1.1-1.4: 术语更新和用户友好界面
- Requirements 2.1-2.5: 作业配置创建和验证
- Requirements 3.1-3.6: 远程仓库直接访问
- Requirements 5.1-5.5: 作业配置管理
- Requirements 6.1-6.5: 简化界面，移除技术操作
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from grading.assignment_utils import ValidationError
from grading.models import Assignment, Class, Course
from grading.services.assignment_management_service import AssignmentManagementService

logger = logging.getLogger(__name__)


@login_required
def assignment_list_view(request):
    """作业管理列表页面

    显示教师创建的所有作业配置，支持多维度筛选和统计。

    实现需求:
    - Requirements 1.1: 在导航菜单中显示"作业管理"
    - Requirements 1.2: 显示页面标题为"作业管理"
    - Requirements 5.1: 显示该教师创建的所有作业配置列表
    - Requirements 5.2: 包含作业名称、提交方式、关联课程、班级和创建时间
    - Requirements 7.4: 支持按课程和班级筛选

    功能特性：
    1. 教师隔离：只显示当前教师创建的作业配置
    2. 多维度筛选：
       - 按课程筛选：course_id参数
       - 按班级筛选：class_id参数
       - 按存储类型筛选：storage_type参数（git/filesystem）
    3. 统计信息：
       - 总作业数
       - 激活的作业数
       - Git类型作业数
       - 文件系统类型作业数
       - 涉及的课程数和班级数
    4. 动态筛选选项：
       - 课程列表：只显示教师有作业的课程
       - 班级列表：根据选择的课程动态更新

    URL参数：
        course_id (int, optional): 课程ID，用于筛选特定课程的作业
        class_id (int, optional): 班级ID，用于筛选特定班级的作业
        storage_type (str, optional): 存储类型，"git"或"filesystem"

    返回：
        HttpResponse: 渲染的作业列表页面

    模板变量：
        assignments: 作业配置查询集
        courses: 教师的课程列表（用于筛选）
        classes: 教师的班级列表（用于筛选）
        summary: 统计信息字典
        selected_course_id: 当前选择的课程ID
        selected_class_id: 当前选择的班级ID
        selected_storage_type: 当前选择的存储类型
        page_title: 页面标题

    错误处理：
        如果发生异常，显示错误消息并重定向到首页
    """
    try:
        service = AssignmentManagementService()

        # 获取筛选参数
        course_id = request.GET.get("course_id")
        class_id = request.GET.get("class_id")
        storage_type = request.GET.get("storage_type")

        # 转换参数类型
        course_id = int(course_id) if course_id else None
        class_id = int(class_id) if class_id else None

        # 获取作业列表
        assignments = service.list_assignments(
            teacher=request.user, course_id=course_id, class_id=class_id, storage_type=storage_type
        )

        # 获取筛选选项
        courses = service.get_teacher_courses(request.user)
        classes = service.get_teacher_classes(request.user, course_id=course_id)

        # 获取统计信息
        summary = service.get_assignment_summary(request.user)

        context = {
            "assignments": assignments,
            "courses": courses,
            "classes": classes,
            "summary": summary,
            "selected_course_id": course_id,
            "selected_class_id": class_id,
            "selected_storage_type": storage_type,
            "page_title": "作业管理",
        }

        return render(request, "grading/assignment_list.html", context)

    except Exception as e:
        logger.error(f"作业管理页面加载失败: {str(e)}", exc_info=True)
        messages.error(request, f"页面加载失败: {str(e)}")
        return redirect("grading:index")


@login_required
@require_http_methods(["GET"])
def assignment_list_api(request):
    """Assignment list data API for React frontend."""
    try:
        service = AssignmentManagementService()

        course_id = request.GET.get("course_id")
        class_id = request.GET.get("class_id")
        storage_type = request.GET.get("storage_type")

        course_id = int(course_id) if course_id else None
        class_id = int(class_id) if class_id else None

        assignments = service.list_assignments(
            teacher=request.user, course_id=course_id, class_id=class_id, storage_type=storage_type
        )
        courses = service.get_teacher_courses(request.user)
        classes = service.get_teacher_classes(request.user, course_id=course_id)
        summary = service.get_assignment_summary(request.user)

        assignment_list = []
        for assignment in assignments:
            assignment_list.append(
                {
                    "id": assignment.id,
                    "name": assignment.name,
                    "storage_type": assignment.storage_type,
                    "description": assignment.description,
                    "course": {
                        "id": assignment.course.id if assignment.course else None,
                        "name": assignment.course.name if assignment.course else "",
                    },
                    "class_obj": {
                        "id": assignment.class_obj.id if assignment.class_obj else None,
                        "name": assignment.class_obj.name if assignment.class_obj else "",
                    },
                    "git_url": assignment.git_url,
                    "git_branch": assignment.git_branch,
                    "base_path": assignment.base_path,
                    "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                    "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None,
                }
            )

        course_list = [{"id": course.id, "name": course.name} for course in courses]
        class_list = [{"id": cls.id, "name": cls.name} for cls in classes]

        return JsonResponse(
            {
                "status": "success",
                "assignments": assignment_list,
                "courses": course_list,
                "classes": class_list,
                "summary": summary,
                "selected_course_id": course_id,
                "selected_class_id": class_id,
                "selected_storage_type": storage_type,
            }
        )
    except Exception as e:
        logger.error(f"Assignment list API failed: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Failed to load assignments."}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def assignment_create_view(request):
    """创建作业配置

    提供表单界面让教师创建新的作业配置，支持Git和文件上传两种方式。

    实现需求:
    - Requirements 2.1: 提供两个清晰的选项："Git 仓库"和"文件上传"
    - Requirements 2.2: 只显示该方式相关的配置字段
    - Requirements 2.3: 文件上传方式要求输入课程名称、班级名称
    - Requirements 2.4: Git 仓库方式要求输入 Git 仓库 URL 和分支名称
    - Requirements 2.5: 验证所有必填字段已填写

    GET请求：
        显示创建表单，包含：
        - 存储类型选择器（Git仓库/文件上传）
        - 课程选择器（下拉列表）
        - 班级选择器（下拉列表，根据课程动态更新）
        - 作业名称输入框
        - 作业描述输入框（可选）
        - Git配置字段（仅Git方式显示）：
          * Git仓库URL（必填）
          * Git分支（默认main）
          * Git用户名（可选）
          * Git密码（可选）

    POST请求：
        处理表单提交，创建作业配置：
        1. 验证必填字段
        2. 验证课程和班级的有效性和关联关系
        3. 根据存储类型验证特定字段
        4. 调用AssignmentManagementService创建作业
        5. 返回JSON响应

    表单字段：
        name (str, required): 作业名称
        storage_type (str, required): 存储类型，"git"或"filesystem"
        description (str, optional): 作业描述
        course_id (int, required): 课程ID
        class_id (int, required): 班级ID

        Git方式额外字段：
        git_url (str, required): Git仓库URL
        git_branch (str, optional): Git分支，默认"main"
        git_username (str, optional): Git用户名
        git_password (str, optional): Git密码（会自动加密）

    返回：
        GET: HttpResponse - 渲染的创建表单页面
        POST: JsonResponse - 创建结果
            成功: {
                'status': 'success',
                'message': '创建成功消息',
                'assignment_id': 作业ID,
                'redirect_url': 重定向URL
            }
            失败: {
                'status': 'error',
                'message': '错误消息'
            }

    错误处理：
        - 验证错误：返回用户友好的错误消息
        - 权限错误：返回403状态码
        - 系统错误：记录日志并返回通用错误消息

    安全性：
        - 只能创建属于当前租户的作业配置
        - Git密码自动加密存储
        - 路径名称自动清理特殊字符
        - 防止重复创建（同一教师、课程、班级、名称）
    """
    if request.method == "GET":
        return JsonResponse({"status": "error", "message": "GET not supported on this endpoint."}, status=405)

        # 显示创建表单
        try:
            # 获取教师的课程和班级列表
            tenant = request.user.profile.tenant
            courses = Course.objects.filter(tenant=tenant).order_by("name")

            classes = Class.objects.filter(tenant=tenant).order_by("name")

            context = {
                "courses": courses,
                "classes": classes,
                "page_title": "创建作业配置",
            }

            return render(request, "grading/assignment_create.html", context)

        except Exception as e:
            logger.error(f"加载创建作业页面失败: {str(e)}", exc_info=True)
            messages.error(request, f"页面加载失败: {str(e)}")
            return redirect("grading:assignment_list")

    else:  # POST
        try:
            service = AssignmentManagementService()

            # 获取表单数据
            name = request.POST.get("name", "").strip()
            storage_type = request.POST.get("storage_type", "").strip()
            description = request.POST.get("description", "").strip()
            course_id = request.POST.get("course_id")
            class_id = request.POST.get("class_id")

            # 验证必填字段
            if not name:
                return JsonResponse({"status": "error", "message": "作业名称不能为空"})

            if not storage_type or storage_type not in ["git", "filesystem"]:
                return JsonResponse({"status": "error", "message": "请选择提交方式"})

            if not course_id:
                return JsonResponse({"status": "error", "message": "请选择课程"})

            if not class_id:
                return JsonResponse({"status": "error", "message": "请选择班级"})

            # 获取课程和班级对象
            try:
                course = Course.objects.get(id=course_id, tenant=request.user.profile.tenant)
                class_obj = Class.objects.get(id=class_id, tenant=request.user.profile.tenant)
            except (Course.DoesNotExist, Class.DoesNotExist):
                return JsonResponse({"status": "error", "message": "课程或班级不存在"})

            # 准备创建参数
            create_params = {"description": description}

            # 根据存储类型添加特定参数
            if storage_type == "git":
                git_url = request.POST.get("git_url", "").strip()
                git_branch = request.POST.get("git_branch", "main").strip()
                git_username = request.POST.get("git_username", "").strip()
                git_password = request.POST.get("git_password", "").strip()

                if not git_url:
                    return JsonResponse({"status": "error", "message": "Git仓库URL不能为空"})

                create_params.update(
                    {
                        "git_url": git_url,
                        "git_branch": git_branch or "main",
                        "git_username": git_username,
                        "git_password": git_password,
                    }
                )

            # 创建作业配置
            assignment = service.create_assignment(
                teacher=request.user,
                course=course,
                class_obj=class_obj,
                name=name,
                storage_type=storage_type,
                **create_params,
            )

            logger.info(
                f"Teacher {request.user.username} created assignment: "
                f"{assignment.name} (id={assignment.id})"
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": f"作业配置 '{assignment.name}' 创建成功",
                    "assignment_id": assignment.id,
                    "redirect_url": "/grading/assignments/",
                }
            )

        except ValidationError as e:
            logger.warning(f"作业创建验证失败: {e.user_message}")
            return JsonResponse({"status": "error", "message": e.user_message})
        except Exception as e:
            logger.error(f"创建作业失败: {str(e)}", exc_info=True)
            return JsonResponse({"status": "error", "message": f"创建失败: {str(e)}"})


@login_required
@require_http_methods(["GET", "POST"])
def assignment_edit_view(request, assignment_id):
    """编辑作业配置

    实现需求:
    - Requirements 5.3: 允许查看和编辑配置详情
    - Requirements 5.4: 保留已提交的学生作业数据
    """
    try:
        # 获取作业配置
        assignment = get_object_or_404(
            Assignment, id=assignment_id, owner=request.user, tenant=request.user.profile.tenant
        )

        if request.method == "GET":
        return JsonResponse({"status": "error", "message": "GET not supported on this endpoint."}, status=405)

            # 显示编辑表单
            context = {
                "assignment": assignment,
                "page_title": f"编辑作业配置 - {assignment.name}",
            }

            return render(request, "grading/assignment_edit.html", context)

        else:  # POST
            service = AssignmentManagementService()

            # 获取更新字段
            update_fields = {}

            # 基本字段
            if "name" in request.POST:
                update_fields["name"] = request.POST.get("name", "").strip()

            if "description" in request.POST:
                update_fields["description"] = request.POST.get("description", "").strip()

            if "is_active" in request.POST:
                update_fields["is_active"] = request.POST.get("is_active") == "true"

            # Git特定字段
            if assignment.storage_type == "git":
                if "git_url" in request.POST:
                    update_fields["git_url"] = request.POST.get("git_url", "").strip()

                if "git_branch" in request.POST:
                    update_fields["git_branch"] = request.POST.get("git_branch", "").strip()

                if "git_username" in request.POST:
                    update_fields["git_username"] = request.POST.get("git_username", "").strip()

                if "git_password" in request.POST:
                    git_password = request.POST.get("git_password", "").strip()
                    if git_password:  # 只在提供了新密码时更新
                        update_fields["git_password"] = git_password

            # 执行更新
            assignment = service.update_assignment(
                assignment=assignment, teacher=request.user, **update_fields
            )

            logger.info(
                f"Teacher {request.user.username} updated assignment {assignment.id}: "
                f"fields={list(update_fields.keys())}"
            )

            return JsonResponse(
                {"status": "success", "message": f"作业配置 '{assignment.name}' 更新成功"}
            )

    except ValidationError as e:
        logger.warning(f"作业更新验证失败: {e.user_message}")
        return JsonResponse({"status": "error", "message": e.user_message})
    except PermissionError as e:
        logger.warning(f"权限错误: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=403)
    except Exception as e:
        logger.error(f"更新作业失败: {str(e)}", exc_info=True)
        
            messages.error(request, f"加载失败: {str(e)}")
            return redirect("grading:assignment_list")
        else:
            return JsonResponse({"status": "error", "message": f"更新失败: {str(e)}"})


@login_required
@require_http_methods(["POST"])
def assignment_delete_view(request, assignment_id):
    """删除作业配置

    实现需求:
    - Requirements 5.5: 提示确认并说明对已提交作业的影响
    """
    try:
        # 获取作业配置
        assignment = get_object_or_404(
            Assignment, id=assignment_id, owner=request.user, tenant=request.user.profile.tenant
        )

        service = AssignmentManagementService()

        # 检查是否已确认
        confirm = request.POST.get("confirm", "false").lower() == "true"

        # 执行删除
        result = service.delete_assignment(
            assignment=assignment, teacher=request.user, confirm=confirm
        )

        if result["deleted"]:
            logger.info(f"Teacher {request.user.username} deleted assignment {assignment_id}")

        return JsonResponse(result)

    except PermissionError as e:
        logger.warning(f"权限错误: {str(e)}")
        return JsonResponse({"success": False, "message": str(e)}, status=403)
    except Exception as e:
        logger.error(f"删除作业失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "message": f"删除失败: {str(e)}"})


# ============================================================================
# 作业结构 API 视图
# ============================================================================


@login_required
@require_http_methods(["GET"])
def get_assignment_structure_api(request):
    """获取作业目录结构 API

    RESTful API端点，用于获取作业的目录结构。
    支持Git远程仓库和本地文件系统两种方式。

    实现需求:
    - Requirements 3.2: 直接从远程 Git 仓库读取该课程的目录结构
    - Requirements 3.3: 列出该课程下的所有作业目录和学生提交情况
    - Requirements 3.5: 向教师用户显示友好的错误消息
    - Requirements 3.6: 无需本地克隆，直接访问远程仓库

    技术实现：
    Git方式：
        - 使用git ls-tree命令直接读取远程仓库目录
        - 无需本地克隆，节省存储空间
        - 内存缓存提高访问速度（5分钟缓存）
        - 支持递归读取子目录

    文件系统方式：
        - 使用os.listdir读取本地目录
        - 路径安全验证，防止路径遍历
        - 支持递归读取子目录

    URL参数：
        assignment_id (int, required): 作业配置ID
        path (str, optional): 相对路径，默认为根目录
            例如: "第一次作业" 或 "第一次作业/计算机1班"

    返回：
        JsonResponse: 目录结构信息
        成功: {
            'success': True,
            'path': '当前路径',
            'entries': [
                {
                    'name': '文件/目录名',
                    'type': 'file' 或 'dir',
                    'size': 文件大小（字节），
                    'modified': 修改时间（时间戳）
                },
                ...
            ]
        }
        失败: {
            'success': False,
            'error': '友好的错误消息'
        }

    错误处理：
        - 作业不存在：返回错误消息
        - 无权限访问：返回错误消息
        - 远程仓库访问失败：返回友好的错误消息（不暴露技术细节）
        - 路径不存在：返回错误消息
        - 网络错误：返回友好的错误消息

    使用场景：
        1. 评分界面：教师查看学生提交的作业文件
        2. 作业管理：教师浏览作业目录结构
        3. 文件选择：选择要查看或下载的文件

    性能优化：
        - Git方式使用内存缓存，减少远程访问
        - 支持分页（未来扩展）
        - 异步加载子目录（前端实现）
    """
    try:
        assignment_id = request.GET.get("assignment_id")
        path = request.GET.get("path", "")

        if not assignment_id:
            return JsonResponse({"success": False, "error": "未提供作业ID"})

        # 获取作业配置
        try:
            assignment = Assignment.objects.get(
                id=assignment_id, owner=request.user, tenant=request.user.profile.tenant
            )
        except Assignment.DoesNotExist:
            return JsonResponse({"success": False, "error": "作业配置不存在或无权限访问"})

        # 获取目录结构
        service = AssignmentManagementService()
        result = service.get_assignment_structure(assignment, path)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"获取作业结构失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": "获取作业结构失败，请稍后重试"})


@login_required
@require_http_methods(["GET"])
def get_assignment_file_api(request):
    """获取作业文件内容 API

    实现需求:
    - Requirements 3.4: 直接从远程仓库获取作业文件内容
    """
    try:
        assignment_id = request.GET.get("assignment_id")
        file_path = request.GET.get("file_path", "")

        if not assignment_id:
            return JsonResponse({"success": False, "error": "未提供作业ID"})

        if not file_path:
            return JsonResponse({"success": False, "error": "未提供文件路径"})

        # 获取作业配置
        try:
            assignment = Assignment.objects.get(
                id=assignment_id, owner=request.user, tenant=request.user.profile.tenant
            )
        except Assignment.DoesNotExist:
            return JsonResponse({"success": False, "error": "作业配置不存在或无权限访问"})

        # 获取存储适配器
        service = AssignmentManagementService()
        adapter = service._get_storage_adapter(assignment)

        # 验证路径安全性
        service.validate_class_directory_isolation(assignment, file_path)

        # 读取文件内容
        try:
            content = adapter.read_file(file_path)

            # 尝试解码为文本
            try:
                text_content = content.decode("utf-8")
                is_text = True
            except UnicodeDecodeError:
                # 二进制文件，返回base64编码
                import base64

                text_content = base64.b64encode(content).decode("ascii")
                is_text = False

            return JsonResponse(
                {
                    "success": True,
                    "content": text_content,
                    "is_text": is_text,
                    "file_path": file_path,
                }
            )

        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}", exc_info=True)
            return JsonResponse({"success": False, "error": f"读取文件失败: {str(e)}"})

    except ValidationError as e:
        return JsonResponse({"success": False, "error": e.user_message})
    except Exception as e:
        logger.error(f"获取文件内容失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": "获取文件内容失败，请稍后重试"})


# ============================================================================
# 学生作业提交视图
# ============================================================================


@login_required
def student_submission_view(request):
    """学生作业提交页面

    实现需求:
    - Requirements 9.1: 显示该学生所在班级的课程列表
    - Requirements 9.2: 显示现有的作业次数目录列表和"创建新作业"按钮
    """
    try:
        service = AssignmentManagementService()

        # 获取学生的课程列表
        courses = service.get_student_courses(request.user)

        context = {
            "courses": courses,
            "page_title": "作业提交",
        }

        return render(request, "grading/student_submission.html", context)

    except Exception as e:
        logger.error(f"学生作业提交页面加载失败: {str(e)}", exc_info=True)
        messages.error(request, f"页面加载失败: {str(e)}")
        return redirect("grading:index")


@login_required
@require_http_methods(["POST"])
def upload_assignment_file_api(request):
    """文件上传 API

    实现需求:
    - Requirements 9.5: 自动在文件名中添加或验证学生姓名
    - Requirements 9.6: 支持常见文档格式
    - Requirements 9.7: 重复上传同一作业时覆盖之前的文件
    """
    try:
        assignment_id = request.POST.get("assignment_id")
        assignment_number = request.POST.get("assignment_number", "").strip()

        if not assignment_id:
            return JsonResponse({"success": False, "message": "未提供作业ID"})

        if not assignment_number:
            return JsonResponse({"success": False, "message": "未提供作业次数"})

        # 获取上传的文件
        if "file" not in request.FILES:
            return JsonResponse({"success": False, "message": "未提供文件"})

        uploaded_file = request.FILES["file"]

        # 获取作业配置
        try:
            # 学生可以访问任何文件系统类型的作业配置
            # 注意：这里不限制owner，因为学生需要向教师的作业提交
            assignment = Assignment.objects.get(
                id=assignment_id, storage_type="filesystem", is_active=True  # 只支持文件系统类型
            )
        except Assignment.DoesNotExist:
            return JsonResponse({"success": False, "message": "作业配置不存在或不支持文件上传"})

        # 上传文件
        service = AssignmentManagementService()
        result = service.upload_student_file(
            assignment=assignment,
            student=request.user,
            file=uploaded_file,
            assignment_number_path=assignment_number,
        )

        logger.info(
            f"Student {request.user.username} uploaded file to assignment {assignment_id}: "
            f"{result.get('file_name')}"
        )

        return JsonResponse(result)

    except ValidationError as e:
        logger.warning(f"文件上传验证失败: {e.user_message}")
        return JsonResponse({"success": False, "message": e.user_message})
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "message": f"上传失败: {str(e)}"})


@login_required
@require_http_methods(["POST"])
def create_assignment_directory_api(request):
    """创建作业目录 API

    实现需求:
    - Requirements 9.3: 根据当前已有的作业次数自动生成下一个作业目录名称
    - Requirements 9.4: 遵循统一的命名规范
    - Requirements 9.8: 立即显示该目录并允许上传文件
    """
    try:
        assignment_id = request.POST.get("assignment_id")
        auto_generate = request.POST.get("auto_generate", "true").lower() == "true"
        custom_name = request.POST.get("custom_name", "").strip()

        if not assignment_id:
            return JsonResponse({"success": False, "message": "未提供作业ID"})

        # 获取作业配置
        try:
            assignment = Assignment.objects.get(
                id=assignment_id, storage_type="filesystem", is_active=True
            )
        except Assignment.DoesNotExist:
            return JsonResponse({"success": False, "message": "作业配置不存在或不支持此操作"})

        # 创建目录
        service = AssignmentManagementService()
        result = service.create_assignment_number_directory(
            assignment=assignment,
            auto_generate_name=auto_generate,
            custom_name=custom_name if not auto_generate else None,
        )

        logger.info(
            f"Created assignment directory for assignment {assignment_id}: "
            f"{result.get('directory_name')}"
        )

        return JsonResponse(result)

    except ValidationError as e:
        logger.warning(f"创建目录验证失败: {e.user_message}")
        return JsonResponse({"success": False, "message": e.user_message})
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "message": f"创建失败: {str(e)}"})


@login_required
@require_http_methods(["GET"])
def get_assignment_directories_api(request):
    """获取作业次数目录列表 API

    实现需求:
    - Requirements 9.2: 显示现有的作业次数目录列表
    """
    try:
        assignment_id = request.GET.get("assignment_id")

        if not assignment_id:
            return JsonResponse({"success": False, "message": "未提供作业ID"})

        # 获取作业配置
        try:
            assignment = Assignment.objects.get(id=assignment_id, is_active=True)
        except Assignment.DoesNotExist:
            return JsonResponse({"success": False, "message": "作业配置不存在"})

        # 获取目录列表
        service = AssignmentManagementService()
        directories = service.get_assignment_directories(assignment)

        return JsonResponse({"success": True, "directories": directories})

    except Exception as e:
        logger.error(f"获取目录列表失败: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "message": "获取目录列表失败，请稍后重试"})


# ============================================================================
# Helper API Views
# ============================================================================


@login_required
@require_http_methods(["GET"])
def get_course_classes_api(request):
    """获取课程的班级列表 API

    用于动态加载课程对应的班级选项。

    实现需求:
    - Requirements 7.2: 实现课程和班级选择器
    """
    try:
        course_id = request.GET.get("course_id")

        if not course_id:
            return JsonResponse({"status": "error", "message": "缺少课程ID参数"})

        # 获取课程
        try:
            course = Course.objects.get(id=course_id, tenant=request.user.profile.tenant)
        except Course.DoesNotExist:
            return JsonResponse({"status": "error", "message": "课程不存在"})

        # 获取该课程的班级列表
        classes = (
            Class.objects.filter(course=course, tenant=request.user.profile.tenant)
            .order_by("name")
            .values("id", "name")
        )

        return JsonResponse({"status": "success", "classes": list(classes)})

    except Exception as e:
        logger.error(f"获取课程班级列表失败: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": f"获取班级列表失败: {str(e)}"})
