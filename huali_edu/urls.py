from django.contrib import admin
from django.urls import path, include
from grading.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('grading/', include('grading.urls')),
] 