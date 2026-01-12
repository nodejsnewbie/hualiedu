from django.urls import path

from . import api_views, assignment_views, views
from .admin import admin_site

app_name = "grading"

urlpatterns = [
    path("file/<path:file_path>", views.serve_file, name="serve_file"),
    # path("admin/", admin_site.urls),  # 使用主应用的admin
    path("writing/get_template_list", views.get_template_list, name="get_template_list"),
    path("get_courses_list/", views.get_courses_list_view, name="get_courses_list"),
    path("get_directory_tree/", views.get_directory_tree_view, name="get_directory_tree"),
    path("get_file_content/", views.get_file_content, name="get_file_content"),
    path("save_grade/", views.save_grade, name="save_grade"),
    path("add_grade_to_file/", views.add_grade_to_file, name="add_grade_to_file"),
    path("remove_grade/", views.remove_grade, name="remove_grade"),
    path("get_dir_file_count/", views.get_dir_file_count, name="get_dir_file_count"),
    path("save_teacher_comment/", views.save_teacher_comment, name="save_teacher_comment"),
    path("get_teacher_comment/", views.get_teacher_comment, name="get_teacher_comment"),
    path("get_file_grade_info/", views.get_file_grade_info_api, name="get_file_grade_info"),
    path("ai_score/", views.ai_score_view, name="ai_score"),
    path("batch_ai_score/", views.batch_ai_score_view, name="batch_ai_score"),
    path("batch-grade-registration/", views.batch_grade_registration, name="batch_grade_registration"),
    # 成绩登分册写入功能路由
    path("grade-registry-writer/", views.grade_registry_writer_view, name="grade_registry_writer"),
    path(
        "homework/<int:homework_id>/batch-grade-to-registry/",
        views.batch_grade_to_registry,
        name="batch_grade_to_registry",
    ),
    path(
        "batch-grade/progress/<str:tracking_id>/",
        views.batch_grade_progress,
        name="batch_grade_progress",
    ),
    # 高级批量AI评分相关路由
    path("batch-ai-score/", views.batch_ai_score_advanced_view, name="batch_ai_score_advanced"),
    path("batch-ai-score/get-classes/", views._get_class_list, name="get_class_list"),
    path("batch-ai-score/get-homework/", views._get_homework_list, name="get_homework_list"),
    # 评分类型管理
    path("change-grade-type/", views.change_grade_type_view, name="change_grade_type"),
    path("get-grade-type-config/", views.get_grade_type_config_view, name="get_grade_type_config"),
    path("api/grade-types/", views.grade_type_config_list_api, name="grade_type_config_list_api"),
    # 多租户管理
    # 租户管理员
    # 校历功能相关路由
    # 课程和班级管理路由 (API-only)
    path("semester-status-api/", views.semester_status_api, name="semester_status_api"),
    path("add-course/", views.add_course_view, name="add_course"),
    path("delete-course/", views.delete_course_view, name="delete_course"),
    path("add-schedule/", views.add_schedule_view, name="add_schedule"),
    path(
        "get-schedule-weeks/<int:schedule_id>/", views.get_schedule_weeks, name="get_schedule_weeks"
    ),
    path("get-schedule-data/", views.get_schedule_data, name="get_schedule_data"),
    # ============================================================================
    # 作业管理相关路由 (Assignment Management)
    # ============================================================================
    # 作业管理 (API-only)
    path("assignments/create/", assignment_views.assignment_create_view, name="assignment_create"),
    path(
        "assignments/<int:assignment_id>/edit/",
        assignment_views.assignment_edit_view,
        name="assignment_edit",
    ),
    path(
        "assignments/<int:assignment_id>/edit/",
        assignment_views.assignment_edit_view,
        name="assignment_update",
    ),
    path(
        "assignments/<int:assignment_id>/delete/",
        assignment_views.assignment_delete_view,
        name="assignment_delete",
    ),
    # 作业结构 API
    path(
        "api/assignments/structure/",
        assignment_views.get_assignment_structure_api,
        name="get_assignment_structure_api",
    ),
    path(
        "api/assignments/file/",
        assignment_views.get_assignment_file_api,
        name="get_assignment_file_api",
    ),
    path(
        "api/assignments/directories/",
        assignment_views.get_assignment_directories_api,
        name="get_assignment_directories_api",
    ),
    path("api/assignments/", assignment_views.assignment_list_api, name="assignment_list_api"),
    path("api/git-branches/", assignment_views.git_branches_api, name="git_branches_api"),
    # Helper APIs
    path("api/course-classes/", assignment_views.get_course_classes_api, name="get_course_classes"),
    path("api/auth/csrf/", api_views.csrf_view, name="api_csrf"),
    path("api/auth/login/", api_views.login_api, name="api_login"),
    path("api/auth/logout/", api_views.logout_api, name="api_logout"),
    path("api/auth/me/", api_views.me_api, name="api_me"),
    path("api/courses/", api_views.course_list_api, name="api_course_list"),
    path("api/courses/create/", api_views.course_create_api, name="api_course_create"),
    path("api/classes/", api_views.class_list_api, name="api_class_list"),
    path("api/classes/create/", api_views.class_create_api, name="api_class_create"),
    path("api/semesters/", api_views.semester_list_api, name="api_semester_list"),
    path("api/semesters/create/", api_views.semester_create_api, name="api_semester_create"),
    path(
        "api/semesters/<int:semester_id>/update/",
        api_views.semester_update_api,
        name="api_semester_update",
    ),
    path(
        "api/semesters/<int:semester_id>/delete/",
        api_views.semester_delete_api,
        name="api_semester_delete",
    ),
    path("api/course-management/", api_views.course_management_api, name="api_course_management"),
    path("api/tenants/", api_views.tenant_list_api, name="api_tenant_list"),
    path("api/tenant-dashboard/", api_views.tenant_dashboard_api, name="api_tenant_dashboard"),
    path("api/tenant-users/", api_views.tenant_users_api, name="api_tenant_users"),
    path("api/student/assignments/", api_views.student_assignment_list_api, name="api_student_assignments"),
    path(
        "api/student/upload/",
        assignment_views.upload_assignment_file_api,
        name="upload_assignment_file_api",
    ),
    path(
        "api/student/create-directory/",
        assignment_views.create_assignment_directory_api,
        name="create_assignment_directory_api",
    ),
    # ============================================================================
    # 仓库管理相关路由（已废弃，保留向后兼容）
    # Deprecated: Use assignment routes above instead
    # ============================================================================
    path("add-repository/", views.add_repository_view, name="add_repository"),
    path("update-repository/", views.update_repository_view, name="update_repository"),
    path("delete-repository/", views.delete_repository_view, name="delete_repository"),
    path("sync-repository/", views.sync_repository_view, name="sync_repository"),
    path(
        "get-repository-branches/",
        views.get_repository_branches_view,
        name="get_repository_branches",
    ),
    path(
        "validate-git-connection/",
        views.validate_git_connection_view,
        name="validate_git_connection",
    ),
    path(
        "validate-directory-structure/",
        views.validate_directory_structure_view,
        name="validate_directory_structure",
    ),
    path("api/repositories/", views.get_repository_list_api, name="get_repository_list_api"),
    # 课程和作业信息API
    path("api/course-info/", views.get_course_info_api, name="get_course_info_api"),
    path("api/update-course-type/", views.update_course_type_api, name="update_course_type_api"),
    path("api/homework-list/", views.get_homework_list_api, name="get_homework_list_api"),
    path("api/homework-info/", views.get_homework_info_api, name="get_homework_info_api"),
    path("api/homework-type/", views.get_homework_type_api, name="get_homework_type_api"),
    path(
        "api/update-homework-type/", views.update_homework_type_api, name="update_homework_type_api"
    ),
    # 缓存管理API
    path("api/cache/stats/", views.cache_stats_api, name="cache_stats_api"),
    path("api/cache/clear/", views.clear_cache_api, name="clear_cache_api"),
    path(
        "api/student/homework-list/",
        views.get_student_homework_list,
        name="get_student_homework_list",
    ),
    path("api/student/upload/", views.upload_homework, name="upload_homework"),
    path(
        "api/student/submission-history/",
        views.get_submission_history,
        name="get_submission_history",
    ),
    path("api/student/storage-space/", views.check_storage_space, name="check_storage_space"),
    # 评价模板API - 需求 5.2.1-5.2.12
    path(
        "api/comment-templates/recommended/",
        views.get_recommended_comment_templates,
        name="get_recommended_comment_templates",
    ),
    path(
        "api/comment-templates/record-usage/",
        views.record_comment_usage,
        name="record_comment_usage",
    ),
]
