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
SESSION_COOKIE_SECURE = settings.SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE = settings.CSRF_COOKIE_SECURE
SECURE_HSTS_SECONDS = settings.SECURE_HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS = settings.SECURE_HSTS_INCLUDE_SUBDOMAINS
SECURE_HSTS_PRELOAD = settings.SECURE_HSTS_PRELOAD
if settings.SECURE_PROXY_SSL_HEADER_NAME and settings.SECURE_PROXY_SSL_HEADER_VALUE:
    SECURE_PROXY_SSL_HEADER = (
        settings.SECURE_PROXY_SSL_HEADER_NAME,
        settings.SECURE_PROXY_SSL_HEADER_VALUE,
    )
else:
    SECURE_PROXY_SSL_HEADER = None
SECURE_REFERRER_POLICY = settings.SECURE_REFERRER_POLICY
