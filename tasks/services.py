from django.db import transaction
from django.utils import timezone

from tasks.models import Task
from tasks.signals import task_completed, task_reopened


def complete_task(task: Task) -> None:
    """Marca uma tarefa como concluída e dispara o sinal correspondente.

    Se a tarefa já estiver concluída, não faz nada.
    """
    if task.is_completed:
        return

    with transaction.atomic():
        task.is_completed = True
        task.completed_at = timezone.now()
        task.save()

        task_completed.send(sender=Task, task=task)


def reopen_task(task: Task) -> None:
    """Marca uma tarefa como pendente e dispara o sinal correspondente.

    Se a tarefa não estiver concluída, não faz nada.
    """
    if not task.is_completed:
        return

    with transaction.atomic():
        task.is_completed = False
        task.completed_at = None
        task.save()

        task_reopened.send(sender=Task, task=task)
