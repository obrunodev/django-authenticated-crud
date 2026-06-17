from django.db import models
from accounts.models import OwnedModel


class Task(OwnedModel):
    title = models.CharField(
        max_length=255,
        verbose_name="título",
    )
    description = models.TextField(
        blank=True,
        verbose_name="descrição",
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="concluída",
    )
    xp_reward = models.PositiveIntegerField(
        default=10,
        verbose_name="recompensa de XP",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="criada em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="atualizada em",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="concluída em",
    )

    class Meta:
        verbose_name = "tarefa"
        verbose_name_plural = "tarefas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
