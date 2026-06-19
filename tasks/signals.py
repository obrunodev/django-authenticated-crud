import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.dispatch import Signal, receiver

from tasks.models import Task

User = get_user_model()

# Definição de custom signals
task_completed = Signal()  # Fornece: task
task_reopened = Signal()  # Fornece: task

logger = logging.getLogger("critical_actions")


@receiver(task_completed)
def handle_task_completed(sender, task: Task, **kwargs) -> None:
    """Aplica as regras de gamificação (XP e nível) quando uma tarefa é concluída."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=task.user.id)
        previous_xp = user.experience_points
        previous_level = user.level

        total_xp = user.experience_points + task.xp_reward
        levels_gained = total_xp // 100

        user.experience_points = total_xp % 100
        user.level += levels_gained
        user.save(update_fields=["experience_points", "level"])

        logger.info(
            f"Usuário {user.username} ganhou {task.xp_reward} XP ao concluir a tarefa '{task.title}'",
            extra={
                "action": "xp_gained",
                "user_id": user.id,
                "username": user.username,
                "task_id": task.id,
                "task_title": task.title,
                "xp_change": task.xp_reward,
                "previous_xp": previous_xp,
                "new_xp": user.experience_points,
                "previous_level": previous_level,
                "new_level": user.level,
            },
        )


@receiver(task_reopened)
def handle_task_reopened(sender, task: Task, **kwargs) -> None:
    """Deduz a XP correspondente do usuário ao reabrir uma tarefa."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=task.user.id)
        previous_xp = user.experience_points
        previous_level = user.level

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

        logger.info(
            f"Usuário {user.username} perdeu {task.xp_reward} XP ao reabrir a tarefa '{task.title}'",
            extra={
                "action": "xp_lost",
                "user_id": user.id,
                "username": user.username,
                "task_id": task.id,
                "task_title": task.title,
                "xp_change": -task.xp_reward,
                "previous_xp": previous_xp,
                "new_xp": user.experience_points,
                "previous_level": previous_level,
                "new_level": user.level,
            },
        )
