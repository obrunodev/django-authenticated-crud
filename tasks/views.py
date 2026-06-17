from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from accounts.decorators import owner_required
from tasks.forms import TaskForm
from tasks.models import Task
from tasks.services import complete_task, reopen_task


def _get_filtered_tasks(request: HttpRequest):
    tasks = Task.objects.for_user(request.user)

    q = request.GET.get("q", "").strip()
    if q:
        tasks = tasks.filter(title__icontains=q) | tasks.filter(description__icontains=q)

    status = request.GET.get("status", "pending")
    if status == "completed":
        tasks = tasks.filter(is_completed=True)
        tasks = tasks.order_by("-completed_at", "-created_at")
    elif status == "pending":
        tasks = tasks.filter(is_completed=False)
        tasks = tasks.order_by("-created_at")
    else:
        tasks = tasks.order_by("is_completed", "-created_at")

    return tasks.distinct(), q, status


@login_required
def task_list_view(request: HttpRequest) -> HttpResponse:
    """Lista as tarefas do usuário com busca, status e paginação."""
    tasks, q, status = _get_filtered_tasks(request)

    paginator = Paginator(tasks, 5)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "form": TaskForm(),
    }

    if "HX-Request" in request.headers:
        return render(request, "tasks/partials/task_list.html", context)

    return render(request, "tasks/task_list_page.html", context)


@login_required
@require_POST
def task_create_view(request: HttpRequest) -> HttpResponse:
    """Cria uma nova tarefa e retorna a lista atualizada."""
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()

        tasks, q, status = _get_filtered_tasks(request)
        paginator = Paginator(tasks, 5)
        page_obj = paginator.get_page(1)

        context = {
            "page_obj": page_obj,
            "q": q,
            "status": status,
            "form": TaskForm(),
        }

        response = render(request, "tasks/partials/task_list.html", context)
        response["HX-Trigger"] = "task-updated"
        return response

    tasks, q, status = _get_filtered_tasks(request)
    paginator = Paginator(tasks, 5)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "form": form,
    }
    return render(request, "tasks/partials/task_list.html", context)


@login_required
@owner_required(Task)
@require_POST
def task_toggle_view(request: HttpRequest, task: Task) -> HttpResponse:
    """Alterna o status de conclusão da tarefa usando a camada de serviço."""
    if task.is_completed:
        reopen_task(task)
    else:
        complete_task(task)

    tasks, q, status = _get_filtered_tasks(request)
    paginator = Paginator(tasks, 5)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "form": TaskForm(),
    }

    response = render(request, "tasks/partials/task_list.html", context)
    response["HX-Trigger"] = "task-updated"
    return response


@login_required
@owner_required(Task)
def task_edit_view(request: HttpRequest, task: Task) -> HttpResponse:
    """Edita uma tarefa inline.

    GET: Retorna o formulário de edição inline.
    POST: Salva as alterações e retorna a linha da tarefa atualizada.
    """
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            response = render(request, "tasks/partials/task_row.html", {"task": task})
            response["HX-Trigger"] = "task-updated"
            return response

        return render(request, "tasks/partials/task_edit.html", {"form": form, "task": task})

    form = TaskForm(instance=task)
    return render(request, "tasks/partials/task_edit.html", {"form": form, "task": task})


@login_required
@owner_required(Task)
def task_detail_view(request: HttpRequest, task: Task) -> HttpResponse:
    """Retorna apenas o fragmento visual da linha da tarefa (útil para cancelar edição)."""
    return render(request, "tasks/partials/task_row.html", {"task": task})


@login_required
@owner_required(Task)
def task_delete_view(request: HttpRequest, task: Task) -> HttpResponse:
    """Exclui a tarefa. Deduz a XP se a tarefa estava concluída."""
    if task.is_completed:
        reopen_task(task)

    task.delete()

    tasks, q, status = _get_filtered_tasks(request)
    paginator = Paginator(tasks, 5)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "form": TaskForm(),
    }
    response = render(request, "tasks/partials/task_list.html", context)
    response["HX-Trigger"] = "task-updated"
    return response
