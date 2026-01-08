from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.templatetags.static import static as static_templatetag

from grading.views import index

urlpatterns = (
    [
        path("", index, name="home"),
        path(
            "favicon.ico",
            RedirectView.as_view(
                url=static_templatetag("grading/images/favicon.ico"),
                permanent=False,
            ),
        ),
        path("admin/", admin.site.urls),
        path("grading/", include("grading.urls")),
        path("toolbox/", include("toolbox.urls")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
