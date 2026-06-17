from django.core.exceptions import ImproperlyConfigured

from core.config import settings
from core.settings.base import *  # noqa: F403

if settings.DEBUG:
    raise ImproperlyConfigured("DEBUG must be False when using production settings.")

if not settings.DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL is required when using production settings."
    )

DATABASES = {"default": settings.database_config()}

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

SECURE_SSL_REDIRECT = settings.SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
