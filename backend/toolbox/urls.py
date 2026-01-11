from django.urls import path

from . import api_views, views

app_name = "toolbox"

urlpatterns = [
    path("api/tasks/<int:task_id>/status/", views.task_status_api, name="task_status_api"),
    path("api/tasks/", api_views.task_list_create_api, name="task_list_create_api"),
    path("api/tasks/<int:task_id>/", api_views.task_detail_api, name="task_detail_api"),
    path("api/tasks/<int:task_id>/delete/", api_views.task_delete_api, name="task_delete_api"),
    path("api/repositories/", api_views.repository_list_api, name="repository_list_api"),
    path("api/batch-unzip/", api_views.batch_unzip_api, name="batch_unzip_api"),
    path(
        "api/assignment-grade-import/",
        api_views.assignment_grade_import_api,
        name="assignment_grade_import_api",
    ),
    path("api/browse-directory/", views.browse_directory_api, name="browse_directory_api"),
    path("api/class-directory-tree/", views.class_directory_tree_api, name="class_directory_tree"),
    # 批量登分功能
    path("batch-grade/api/", views.batch_grade_api, name="batch_grade_api"),
]
