from django.urls import path

from . import views
from .admin import admin_site

app_name = "grading"

urlpatterns = [
    path("", views.index, name="index"),
    path("grading/", views.grading_page, name="grading"),
    path("test-js/", views.test_js, name="test_js"),
    path("test-grade-switch/", views.test_grade_switch, name="test_grade_switch"),
    path("debug-grading/", views.debug_grading, name="debug_grading"),
    path("simple-test/", views.simple_test, name="simple_test"),
    path("grading-simple/", views.grading_simple, name="grading_simple"),
    path("test-grading-no-auth/", views.test_grading_no_auth, name="test_grading_no_auth"),
    path("file/<path:file_path>", views.serve_file, name="serve_file"),
    path("admin/", admin_site.urls),
    path("writing/get_template_list", views.get_template_list, name="get_template_list"),
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
    # 批量登分相关路由
    path("batch-grade/", views.batch_grade_page, name="batch_grade_page"),
    path(
        "batch-grade/api/",
        views.batch_grade_registration,
        name="batch_grade_registration",
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
]
