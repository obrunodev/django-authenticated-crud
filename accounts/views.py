import logging

from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import rate_limit_login
from accounts.forms import UserRegisterForm

logger = logging.getLogger("critical_actions")


@rate_limit_login
def login_view(request: HttpRequest) -> HttpResponse:
    """Realiza o login de um usuário existente usando formulário tradicional."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            logger.info(
                f"Usuário autenticado: {user.username}",
                extra={
                    "action": "login_success",
                    "user_id": user.id,
                    "username": user.username,
                },
            )
            return redirect("dashboard")
        else:
            username = request.POST.get("username", "")
            logger.warning(
                f"Falha na tentativa de login para o usuário: {username}",
                extra={
                    "action": "login_failed",
                    "username": username,
                },
            )
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def register_view(request: HttpRequest) -> HttpResponse:
    """Registra um novo usuário no sistema e faz login automático."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(
                f"Novo usuário registrado: {user.username}",
                extra={
                    "action": "user_registered",
                    "user_id": user.id,
                    "username": user.username,
                },
            )
            auth_login(request, user)
            logger.info(
                f"Usuário autenticado: {user.username}",
                extra={
                    "action": "login_success",
                    "user_id": user.id,
                    "username": user.username,
                },
            )
            return redirect("dashboard")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """Realiza o logout do usuário. Suporta redirecionamento HTMX (HX-Redirect)."""
    if request.user.is_authenticated:
        logger.info(
            f"Usuário desconectado: {request.user.username}",
            extra={
                "action": "logout_success",
                "user_id": request.user.id,
                "username": request.user.username,
            },
        )
    auth_logout(request)
    if "HX-Request" in request.headers:
        response = HttpResponse()
        response["HX-Redirect"] = redirect("login").url
        return response
    return redirect("login")


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Exibe o painel do usuário autenticado com suas estatísticas."""
    return render(request, "accounts/dashboard.html")


@login_required
def stats_view(request: HttpRequest) -> HttpResponse:
    """Retorna o fragmento HTML contendo as estatísticas de gamificação do usuário."""
    return render(request, "accounts/partials/stats.html")
