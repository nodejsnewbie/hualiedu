from django.urls import path

from . import views

app_name = "toolbox"

urlpatterns = [
    path("api/tasks/<int:task_id>/status/", views.task_status_api, name="task_status_api"),
    path("api/browse-directory/", views.browse_directory_api, name="browse_directory_api"),
    path("api/class-directory-tree/", views.class_directory_tree_api, name="class_directory_tree"),
    # 批量登分功能
    path("batch-grade/api/", views.batch_grade_api, name="batch_grade_api"),
]
