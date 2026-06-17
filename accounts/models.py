from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class OwnedQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(user=user)


class OwnedModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    objects = OwnedQuerySet.as_manager()

    class Meta:
        abstract = True


class User(AbstractUser):
    experience_points = models.PositiveIntegerField(
        default=0,
        verbose_name="pontos de experiência",
    )
    level = models.PositiveIntegerField(
        default=1,
        verbose_name="nível",
    )

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        return self.username
