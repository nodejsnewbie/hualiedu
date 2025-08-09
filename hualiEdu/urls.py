from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from grading.views import index

urlpatterns = (
    [
        path("", index, name="home"),
        path("admin/", admin.site.urls),
        path("grading/", include("grading.urls")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
