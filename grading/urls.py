from django.urls import path
from . import views
from .admin import admin_site

app_name = 'grading'

urlpatterns = [
    path('', views.grading_page, name='grading'),
    path('test-js/', views.test_js, name='test_js'),
    path('test-grade-switch/', views.test_grade_switch, name='test_grade_switch'),
    path('debug-grading/', views.debug_grading, name='debug_grading'),
    path('simple-test/', views.simple_test, name='simple_test'),
    path('grading-simple/', views.grading_simple, name='grading_simple'),
    path('test-grading-no-auth/', views.test_grading_no_auth, name='test_grading_no_auth'),
    path('file/<path:file_path>', views.serve_file, name='serve_file'),
    path('admin/', admin_site.urls),
    path('writing/get_template_list', views.get_template_list, name='get_template_list'),
    path('get_directory_tree/', views.get_directory_tree, name='get_directory_tree'),
    path('get_file_content/', views.get_file_content, name='get_file_content'),
    path('save_grade/', views.save_grade, name='save_grade'),
    path('add_grade_to_file/', views.add_grade_to_file, name='add_grade_to_file'),
    path('remove_grade/', views.remove_grade, name='remove_grade'),
    path('get_dir_file_count/', views.get_dir_file_count, name='get_dir_file_count'),
    path('save_teacher_comment/', views.save_teacher_comment, name='save_teacher_comment'),
    path('get_teacher_comment/', views.get_teacher_comment, name='get_teacher_comment'),
]