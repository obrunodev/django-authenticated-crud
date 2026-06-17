from django.db import models
from django.utils import timezone
from accounts.models import OwnedModel, OwnedQuerySet


class TaskQuerySet(OwnedQuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())


class TaskManager(models.Manager.from_queryset(TaskQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()


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
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="excluída",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="excluída em",
    )

    objects = TaskManager()

    class Meta:
        verbose_name = "tarefa"
        verbose_name_plural = "tarefas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

