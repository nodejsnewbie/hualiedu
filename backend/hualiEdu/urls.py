from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from grading import api_views

urlpatterns = [
    path("", api_views.health_view, name="health"),
    path("admin/", admin.site.urls),
    path("grading/", include("grading.urls")),
    path("toolbox/", include("toolbox.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
