import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import OwnedModel, OwnedQuerySet

logger = logging.getLogger("critical_actions")


class TaskQuerySet(OwnedQuerySet):
    def delete(self):
        tasks = list(self)
        for task in tasks:
            logger.info(
                f"Tarefa excluída: {task.title}",
                extra={
                    "action": "task_deleted",
                    "task_id": task.id,
                    "task_title": task.title,
                    "user_id": task.user.id,
                    "username": task.user.username,
                },
            )
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
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="prazo",
    )

    objects = TaskManager()

    class Meta:
        verbose_name = "tarefa"
        verbose_name_plural = "tarefas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.title and not self.title.strip():
            raise ValidationError(
                {"title": "O título não pode ser vazio ou conter apenas espaços."}
            )

        if self.pk:
            old_task = Task.objects.all_with_deleted().filter(pk=self.pk).first()
            if old_task and self.due_date != old_task.due_date:
                if self.due_date and self.due_date < timezone.localdate():
                    raise ValidationError(
                        {"due_date": "O prazo não pode ser uma data no passado."}
                    )
        else:
            if self.due_date and self.due_date < timezone.localdate():
                raise ValidationError(
                    {"due_date": "O prazo não pode ser uma data no passado."}
                )

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)

    @property
    def due_status(self) -> str:
        """Retorna o status do prazo: 'overdue', 'today', 'future' ou 'none'."""
        if not self.due_date:
            return "none"
        today = timezone.localdate()
        if self.due_date < today:
            return "overdue"
        elif self.due_date == today:
            return "today"
        else:
            return "future"

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])
        logger.info(
            f"Tarefa excluída: {self.title}",
            extra={
                "action": "task_deleted",
                "task_id": self.id,
                "task_title": self.title,
                "user_id": self.user.id,
                "username": self.user.username,
            },
        )
