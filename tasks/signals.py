from django.contrib.auth import get_user_model
from django.db import transaction
from django.dispatch import Signal, receiver

from tasks.models import Task

User = get_user_model()

# Definição de custom signals
task_completed = Signal()  # Fornece: task
task_reopened = Signal()  # Fornece: task


@receiver(task_completed)
def handle_task_completed(sender, task: Task, **kwargs) -> None:
    """Aplica as regras de gamificação (XP e nível) quando uma tarefa é concluída."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=task.user.id)
        total_xp = user.experience_points + task.xp_reward
        levels_gained = total_xp // 100

        user.experience_points = total_xp % 100
        user.level += levels_gained
        user.save(update_fields=["experience_points", "level"])


@receiver(task_reopened)
def handle_task_reopened(sender, task: Task, **kwargs) -> None:
    """Deduz a XP correspondente do usuário ao reabrir uma tarefa."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=task.user.id)
        total_xp = user.experience_points - task.xp_reward
        if total_xp < 0:
            if user.level > 1:
                levels_lost = (-total_xp + 99) // 100
                user.level = max(1, user.level - levels_lost)
                user.experience_points = total_xp % 100
            else:
                user.experience_points = 0
        else:
            user.experience_points = total_xp
        user.save(update_fields=["experience_points", "level"])
