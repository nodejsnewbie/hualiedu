from django.urls import path
from . import views

app_name = 'grading'

urlpatterns = [
    path('', views.grading_page, name='grading'),
    path('file/<path:file_path>', views.serve_file, name='serve_file'),
]