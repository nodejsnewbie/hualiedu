from django.urls import path

from . import views

app_name = "toolbox"

urlpatterns = [
    path("", views.toolbox_index, name="index"),
    path(
        "assignment-grade-import/",
        views.assignment_grade_import_view,
        name="assignment_grade_import",
    ),
    path("ppt-to-pdf/", views.ppt_to_pdf_view, name="ppt_to_pdf"),
    path("tasks/", views.task_list_view, name="task_list"),
    path("tasks/<int:task_id>/", views.task_detail_view, name="task_detail"),
    path("tasks/<int:task_id>/delete/", views.delete_task_view, name="delete_task"),
    path("api/tasks/<int:task_id>/status/", views.task_status_api, name="task_status_api"),
    path("api/browse-directory/", views.browse_directory_api, name="browse_directory_api"),
    path("api/class-directory-tree/", views.class_directory_tree_api, name="class_directory_tree"),
    # 批量登分功能
    path("batch-grade/", views.batch_grade_page, name="batch_grade_page"),
    path("batch-grade/api/", views.batch_grade_api, name="batch_grade_api"),
]
