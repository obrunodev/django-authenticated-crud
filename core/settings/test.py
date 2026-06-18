from core.settings.local import *  # noqa: F403

# Utiliza um hasher mais rápido e menos seguro para acelerar os testes
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
