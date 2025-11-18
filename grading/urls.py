from django.urls import path

from . import tenant_views, views
from .admin import admin_site

app_name = "grading"

urlpatterns = [
    path("", views.index, name="index"),
    path("grading/", views.grading_page, name="grading_page"),
    path("test-js/", views.test_js, name="test_js"),
    path("test-grade-switch/", views.test_grade_switch, name="test_grade_switch"),
    path("debug-grading/", views.debug_grading, name="debug_grading"),
    path("simple-test/", views.simple_test, name="simple_test"),
    path("grading-simple/", views.grading_simple, name="grading_simple"),
    path("test-grading-no-auth/", views.test_grading_no_auth, name="test_grading_no_auth"),
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
    path("batch-ai-score-page/", views.batch_ai_score_page, name="batch_ai_score_page"),
    # 评分类型管理
    path("grade-type-management/", views.grade_type_management_view, name="grade_type_management"),
    path("change-grade-type/", views.change_grade_type_view, name="change_grade_type"),
    path("get-grade-type-config/", views.get_grade_type_config_view, name="get_grade_type_config"),
    # 多租户管理
    path("super-admin/", tenant_views.super_admin_dashboard, name="super_admin_dashboard"),
    path("super-admin/tenants/", tenant_views.tenant_management, name="tenant_management"),
    path("super-admin/tenants/create/", tenant_views.create_tenant, name="create_tenant"),
    path("super-admin/tenants/update/", tenant_views.update_tenant, name="update_tenant"),
    # 租户管理员
    path("tenant-admin/", tenant_views.tenant_admin_dashboard, name="tenant_admin_dashboard"),
    path("tenant-admin/users/", tenant_views.tenant_user_management, name="tenant_user_management"),
    path("tenant-admin/users/add/", tenant_views.add_user_to_tenant, name="add_user_to_tenant"),
    path(
        "tenant-admin/users/update/", tenant_views.update_user_profile, name="update_user_profile"
    ),
    path(
        "tenant-admin/users/remove/",
        tenant_views.remove_user_from_tenant,
        name="remove_user_from_tenant",
    ),
    path(
        "tenant-admin/config/",
        tenant_views.tenant_config_management,
        name="tenant_config_management",
    ),
    path(
        "tenant-admin/config/update/",
        tenant_views.update_tenant_config,
        name="update_tenant_config",
    ),
    # 校历功能相关路由
    path("calendar/", views.calendar_view, name="calendar_view"),
    path("course-management/", views.course_management_view, name="course_management"),
    path("semester-management/", views.semester_management_view, name="semester_management"),
    path("semester-status-api/", views.semester_status_api, name="semester_status_api"),
    path("semester-edit/<int:semester_id>/", views.semester_edit_view, name="semester_edit"),
    path("semester-add/", views.semester_add_view, name="semester_add"),
    path("semester-delete/<int:semester_id>/", views.semester_delete_view, name="semester_delete"),
    path("add-course/", views.add_course_view, name="add_course"),
    path("delete-course/", views.delete_course_view, name="delete_course"),
    path("add-schedule/", views.add_schedule_view, name="add_schedule"),
    path(
        "get-schedule-weeks/<int:schedule_id>/", views.get_schedule_weeks, name="get_schedule_weeks"
    ),
    path("get-schedule-data/", views.get_schedule_data, name="get_schedule_data"),
    # 仓库管理相关路由
    path("repository-management/", views.repository_management_view, name="repository_management"),
    path("add-repository/", views.add_repository_view, name="add_repository"),
    path("update-repository/", views.update_repository_view, name="update_repository"),
    path("delete-repository/", views.delete_repository_view, name="delete_repository"),
    path("sync-repository/", views.sync_repository_view, name="sync_repository"),
    path("api/repositories/", views.get_repository_list_api, name="get_repository_list_api"),
    # 课程和作业信息API
    path("api/course-info/", views.get_course_info_api, name="get_course_info_api"),
    path("api/update-course-type/", views.update_course_type_api, name="update_course_type_api"),
    path("api/homework-list/", views.get_homework_list_api, name="get_homework_list_api"),
    path("api/homework-info/", views.get_homework_info_api, name="get_homework_info_api"),
    path("api/homework-type/", views.get_homework_type_api, name="get_homework_type_api"),
    path("api/update-homework-type/", views.update_homework_type_api, name="update_homework_type_api"),
    # 测试页面
    path("jquery-test/", views.jquery_test, name="jquery_test"),
    path("test-clean/", views.test_clean, name="test_clean"),
    path("debug-simple/", views.debug_simple, name="debug_simple"),
]
