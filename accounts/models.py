from django.contrib.auth.models import AbstractUser
from django.db import models


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
