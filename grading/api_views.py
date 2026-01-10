import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from django.contrib.auth.models import User

from .models import Assignment, Course, Semester, Tenant, UserProfile
from .services.class_service import ClassService
from .services.course_service import CourseService
from .services.semester_manager import SemesterManager
from .services.semester_status import semester_status_service


@ensure_csrf_cookie
@require_GET
def csrf_view(request):
    return JsonResponse({"success": True})


@require_GET
def health_view(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_POST
def login_api(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    username = payload.get("username") or request.POST.get("username")
    password = payload.get("password") or request.POST.get("password")

    if not username or not password:
        return JsonResponse({"message": "Missing username or password."}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"message": "Invalid credentials."}, status=401)

    if not user.is_active:
        return JsonResponse({"message": "User is disabled."}, status=403)

    login(request, user)
    profile = UserProfile.objects.select_related("tenant").filter(user=user).first()
    return JsonResponse(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "is_tenant_admin": profile.is_tenant_admin if profile else False,
                "tenant": {
                    "id": profile.tenant.id,
                    "name": profile.tenant.name,
                }
                if profile
                else None,
            }
        }
    )


@csrf_exempt
@require_POST
def logout_api(request):
    logout(request)
    return JsonResponse({"success": True})


@require_GET
def me_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    profile = UserProfile.objects.select_related("tenant").filter(user=request.user).first()
    return JsonResponse(
        {
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "is_staff": request.user.is_staff,
                "is_superuser": request.user.is_superuser,
                "is_tenant_admin": profile.is_tenant_admin if profile else False,
                "tenant": {
                    "id": profile.tenant.id,
                    "name": profile.tenant.name,
                }
                if profile
                else None,
            }
        }
    )


@login_required
@require_GET
def course_list_api(request):
    course_service = CourseService()
    current_semester = Semester.objects.filter(is_active=True).first()
    tenant = getattr(request, "tenant", None)
    courses = course_service.list_courses(
        teacher=request.user, tenant=tenant, semester=current_semester
    )

    course_list = [
        {
            "id": course.id,
            "name": course.name,
            "course_type": course.course_type,
            "course_type_display": course.get_course_type_display(),
            "description": course.description,
            "location": getattr(course, "location", ""),
            "class_name": getattr(course, "class_name", ""),
        }
        for course in courses
    ]

    return JsonResponse(
        {
            "status": "success",
            "courses": course_list,
            "current_semester": {
                "id": current_semester.id,
                "name": current_semester.name,
                "start_date": current_semester.start_date.isoformat(),
                "end_date": current_semester.end_date.isoformat(),
                "week_count": current_semester.get_week_count(),
            }
            if current_semester
            else None,
        }
    )


@login_required
@require_POST
def course_create_api(request):
    course_service = CourseService()
    name = request.POST.get("name", "").strip()
    course_type = request.POST.get("course_type", "").strip()
    description = request.POST.get("description", "").strip()

    current_semester = Semester.objects.filter(is_active=True).first()
    if not current_semester:
        return JsonResponse({"status": "error", "message": "请先设置当前学期"}, status=400)

    tenant = getattr(request, "tenant", None)
    try:
        course = course_service.create_course(
            teacher=request.user,
            name=name,
            course_type=course_type,
            description=description,
            semester=current_semester,
            tenant=tenant,
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "success", "course_id": course.id})


@login_required
@require_GET
def class_list_api(request):
    class_service = ClassService()
    course_id = request.GET.get("course_id")
    tenant = getattr(request, "tenant", None)

    course = None
    if course_id:
        course = Course.objects.filter(id=course_id, teacher=request.user).first()
        if not course:
            return JsonResponse({"status": "error", "message": "课程不存在或无权限访问"}, status=404)
        classes = class_service.list_classes(course=course)
    else:
        teacher_courses = Course.objects.filter(teacher=request.user)
        classes = class_service.list_classes(tenant=tenant)
        classes = [cls for cls in classes if cls.course in teacher_courses]

    class_list = [
        {
            "id": cls.id,
            "name": cls.name,
            "student_count": cls.student_count,
            "created_at": cls.created_at.isoformat(),
            "course": {
                "id": cls.course.id,
                "name": cls.course.name,
            }
            if cls.course
            else None,
        }
        for cls in classes
    ]

    return JsonResponse(
        {
            "status": "success",
            "classes": class_list,
            "course": {
                "id": course.id,
                "name": course.name,
                "course_type": course.course_type,
                "course_type_display": course.get_course_type_display(),
                "description": course.description,
            }
            if course
            else None,
        }
    )


@login_required
@require_POST
def class_create_api(request):
    class_service = ClassService()
    course_id = request.POST.get("course_id", "").strip()
    name = request.POST.get("name", "").strip()
    student_count_str = request.POST.get("student_count", "0").strip()

    if not course_id:
        return JsonResponse({"status": "error", "message": "必须选择课程"}, status=400)

    course = Course.objects.filter(id=course_id, teacher=request.user).first()
    if not course:
        return JsonResponse({"status": "error", "message": "课程不存在或无权限访问"}, status=404)

    try:
        student_count = int(student_count_str)
    except ValueError:
        student_count = 0

    tenant = getattr(request, "tenant", None)
    class_obj = class_service.create_class(
        course=course, name=name, student_count=student_count, tenant=tenant
    )

    return JsonResponse({"status": "success", "class_id": class_obj.id})


@login_required
@require_GET
def semester_list_api(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    semester_manager = SemesterManager()
    semesters = semester_manager.get_sorted_semesters_for_display()
    current_semester = semester_manager.get_current_semester()

    semester_list = []
    for semester in semesters:
        semester_list.append(
            {
                "id": semester.id,
                "name": semester.name,
                "start_date": semester.start_date.isoformat(),
                "end_date": semester.end_date.isoformat(),
                "is_active": semester.is_active,
                "week_count": semester.get_week_count(),
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "semesters": semester_list,
            "current_semester_id": current_semester.id if current_semester else None,
            "dashboard_info": semester_status_service.get_dashboard_info(),
        }
    )


@login_required
@require_POST
def semester_create_api(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    name = request.POST.get("name")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    is_active = request.POST.get("is_active") == "true"

    if not name or not start_date or not end_date:
        return JsonResponse({"status": "error", "message": "请填写完整学期信息"}, status=400)

    semester = Semester.objects.create(
        name=name, start_date=start_date, end_date=end_date, is_active=is_active
    )

    if is_active:
        Semester.objects.exclude(pk=semester.pk).update(is_active=False)

    return JsonResponse({"status": "success", "semester_id": semester.id})


@login_required
@require_POST
def semester_update_api(request, semester_id):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    semester = Semester.objects.filter(id=semester_id).first()
    if not semester:
        return JsonResponse({"status": "error", "message": "学期不存在"}, status=404)

    name = request.POST.get("name", semester.name)
    start_date = request.POST.get("start_date", semester.start_date)
    end_date = request.POST.get("end_date", semester.end_date)
    is_active = request.POST.get("is_active")

    semester.name = name
    semester.start_date = start_date
    semester.end_date = end_date
    if is_active is not None:
        semester.is_active = is_active == "true"
    semester.save()

    if semester.is_active:
        Semester.objects.exclude(pk=semester.pk).update(is_active=False)

    return JsonResponse({"status": "success"})


@login_required
@require_POST
def semester_delete_api(request, semester_id):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    semester = Semester.objects.filter(id=semester_id).first()
    if not semester:
        return JsonResponse({"status": "error", "message": "学期不存在"}, status=404)

    if semester.is_active:
        return JsonResponse({"status": "error", "message": "无法删除当前学期"}, status=400)

    force_delete = request.POST.get("force_delete") == "true"
    related_courses = Course.objects.filter(semester=semester)
    courses_count = related_courses.count()

    if courses_count > 0 and not force_delete:
        return JsonResponse(
            {
                "status": "warning",
                "message": "该学期包含课程，需确认强制删除",
                "courses_count": courses_count,
            },
            status=409,
        )

    if force_delete:
        related_courses.delete()

    semester.delete()
    return JsonResponse({"status": "success"})


@login_required
@require_GET
def course_management_api(request):
    current_semester = Semester.objects.filter(is_active=True).first()
    if not current_semester:
        return JsonResponse({"status": "error", "message": "请先设置当前学期"}, status=400)

    courses = Course.objects.filter(teacher=request.user, semester=current_semester).prefetch_related(
        "schedules", "schedules__week_schedules"
    )

    course_list = []
    for course in courses:
        schedules = []
        for schedule in course.schedules.all():
            schedules.append(
                {
                    "id": schedule.id,
                    "weekday": schedule.weekday,
                    "weekday_display": schedule.get_weekday_display(),
                    "period": schedule.period,
                    "period_display": schedule.get_period_display(),
                    "start_week": schedule.start_week,
                    "end_week": schedule.end_week,
                    "week_text": schedule.get_week_schedule_text(),
                }
            )
        course_list.append(
            {
                "id": course.id,
                "name": course.name,
                "location": course.location,
                "class_name": course.class_name,
                "description": course.description,
                "schedules": schedules,
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "current_semester": {
                "id": current_semester.id,
                "name": current_semester.name,
                "start_date": current_semester.start_date.isoformat(),
                "end_date": current_semester.end_date.isoformat(),
                "week_count": current_semester.get_week_count(),
            },
            "courses": course_list,
        }
    )


@login_required
@require_GET
def tenant_list_api(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    tenants = Tenant.objects.all().order_by("-created_at")
    total_users = User.objects.count()
    active_tenants = tenants.filter(is_active=True).count()

    tenant_list = []
    for tenant in tenants:
        tenant_list.append(
            {
                "id": tenant.id,
                "name": tenant.name,
                "description": tenant.description,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at.isoformat(),
                "user_count": tenant.users.count(),
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "tenants": tenant_list,
            "total_users": total_users,
            "active_tenants": active_tenants,
        }
    )


@login_required
@require_GET
def tenant_dashboard_api(request):
    profile = UserProfile.objects.select_related("tenant").filter(user=request.user).first()
    if not profile or not profile.is_tenant_admin:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    tenant = profile.tenant
    user_count = UserProfile.objects.filter(tenant=tenant).count()
    repository_count = tenant.repositories.filter(is_active=True).count()

    return JsonResponse(
        {
            "status": "success",
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "description": tenant.description,
                "is_active": tenant.is_active,
            },
            "user_count": user_count,
            "repository_count": repository_count,
        }
    )


@login_required
@require_GET
def tenant_users_api(request):
    profile = UserProfile.objects.select_related("tenant").filter(user=request.user).first()
    if not profile or not profile.is_tenant_admin:
        return JsonResponse({"status": "error", "message": "无权限访问"}, status=403)

    tenant = profile.tenant
    users = UserProfile.objects.filter(tenant=tenant).select_related("user").order_by("-created_at")

    user_list = []
    for user_profile in users:
        user_list.append(
            {
                "id": user_profile.user.id,
                "profile_id": user_profile.id,
                "username": user_profile.user.username,
                "is_tenant_admin": user_profile.is_tenant_admin,
                "repo_base_dir": user_profile.repo_base_dir,
                "created_at": user_profile.created_at.isoformat(),
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "tenant": {"id": tenant.id, "name": tenant.name},
            "users": user_list,
        }
    )


@login_required
@require_GET
def student_assignment_list_api(request):
    profile = UserProfile.objects.select_related("tenant").filter(user=request.user).first()
    if not profile:
        return JsonResponse({"status": "error", "message": "用户未绑定租户"}, status=400)

    assignments = (
        Assignment.objects.filter(
            tenant=profile.tenant, storage_type="filesystem", is_active=True
        )
        .select_related("course", "class_obj")
        .order_by("-created_at")
    )

    assignment_list = [
        {
            "id": assignment.id,
            "name": assignment.name,
            "course_name": assignment.course.name if assignment.course else "",
            "class_name": assignment.class_obj.name if assignment.class_obj else "",
        }
        for assignment in assignments
    ]

    return JsonResponse({"status": "success", "assignments": assignment_list})
