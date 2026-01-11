from urllib.parse import urlparse

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class LocalhostCsrfViewMiddleware(CsrfViewMiddleware):
    def _origin_verified(self, request):
        if super()._origin_verified(request):
            return True
        if not settings.DEBUG:
            return False
        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return False
        try:
            parsed = urlparse(origin)
        except ValueError:
            return False
        return parsed.hostname in {"localhost", "127.0.0.1"}


class LocalhostCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.DEBUG:
            return response
        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return response
        try:
            parsed = urlparse(origin)
        except ValueError:
            return response
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            return response
        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
        return response
