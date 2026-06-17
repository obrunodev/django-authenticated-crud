from django.db import transaction
from django.utils import timezone
from tasks.models import Task


def complete_task(task: Task) -> None:
    """Marca uma tarefa como concluída e aplica as regras de gamificação (XP e nível).

    Se a tarefa já estiver concluída, não faz nada.
    """
    if task.is_completed:
        return

    with transaction.atomic():
        task.is_completed = True
        task.completed_at = timezone.now()
        task.save()

        user = task.user
        total_xp = user.experience_points + task.xp_reward
        levels_gained = total_xp // 100

        user.experience_points = total_xp % 100
        user.level += levels_gained
        user.save()


def reopen_task(task: Task) -> None:
    """Marca uma tarefa como pendente e deduz a XP correspondente do usuário.

    Se o XP ficar abaixo de 0, deduz os níveis necessários, limitando ao nível 1,
    e ajusta a pontuação de XP restante de forma proporcional.
    Se a tarefa não estiver concluída, não faz nada.
    """
    if not task.is_completed:
        return

    with transaction.atomic():
        task.is_completed = False
        task.completed_at = None
        task.save()

        user = task.user
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
        user.save()
