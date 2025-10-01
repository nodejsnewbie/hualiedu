"""
测试专用设置
"""

from hualiEdu.settings import *

# 测试数据库设置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # 使用内存数据库加快测试速度
    }
}

# 禁用缓存
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# 测试时禁用日志输出
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# 测试媒体文件设置
MEDIA_ROOT = "/tmp/test_media"
STATIC_ROOT = "/tmp/test_static"

# 禁用密码验证器以加快测试
AUTH_PASSWORD_VALIDATORS = []

# 测试时使用简单的密码哈希器
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# 禁用邮件发送
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 测试时的安全设置
SECRET_KEY = "test-secret-key-for-testing-only"
DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# 禁用CSRF保护以简化测试
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# 测试时的API设置
ARK_API_KEY = "test-api-key"
ARK_MODEL = "test-model"

# 禁用中间件中可能影响测试的部分
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "grading.middleware.MultiTenantMiddleware",  # 保留多租户中间件用于测试
]

# 测试时的文件上传设置
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB
