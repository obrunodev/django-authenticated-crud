import functools
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render


def rate_limit_login(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Decorator to rate limit POST requests to the login view.

    Counts failed login attempts per IP. Clears on success (redirect status 302/303).
    """

    @functools.wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.method == "POST":
            # Get IP address
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR", "")

            # Formulate cache key based on IP
            cache_key = f"ratelimit:login:{ip}"

            # Get current count
            request_count = cache.get(cache_key, 0)

            # Check limit
            limit = settings.LOGIN_RATELIMIT_LIMIT
            period = settings.LOGIN_RATELIMIT_PERIOD

            if request_count >= limit:
                form = AuthenticationForm(request)
                form.cleaned_data = {}
                form.add_error(
                    None,
                    "Muitas tentativas de login. Por favor, tente novamente mais tarde.",
                )
                return render(
                    request, "accounts/login.html", {"form": form}, status=429
                )

            # Proceed with the login view
            response = view_func(request, *args, **kwargs)

            # If response is a redirect or user is authenticated, login succeeded -> clear count
            if response.status_code in (302, 303) or (
                request.user and request.user.is_authenticated
            ):
                cache.delete(cache_key)
            else:
                # Otherwise, increment the failed attempt count
                cache.set(cache_key, request_count + 1, period)

            return response

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def owner_required(model_class: type[models.Model]) -> Callable[..., HttpResponse]:
    """Decorator to ensure that the requested object belongs to the authenticated user.

    If the object is not owned by the user, raises Http404 for security.
    Expects view parameter 'pk', 'id', or 'task_id' to query the object.
    The retrieved object is passed to the view function instead of the id argument.
    """

    def decorator(
        view_func: Callable[..., HttpResponse],
    ) -> Callable[..., HttpResponse]:
        @functools.wraps(view_func)
        def _wrapped_view(
            request: HttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponse:
            # Try to get the object ID from kwargs
            pk_val = kwargs.get("pk") or kwargs.get("id") or kwargs.get("task_id")

            # If not found in kwargs, look in args
            if not pk_val and args:
                pk_val = args[0]
                args = args[1:]

            if not pk_val:
                raise Http404("ID do objeto não fornecido.")

            try:
                obj = model_class.objects.get(pk=pk_val, user=request.user)
            except model_class.DoesNotExist as err:
                raise Http404(
                    "Objeto não encontrado ou acesso não autorizado."
                ) from err

            # Pass the retrieved object to the view, replacing the pk/id kwargs/args
            kwargs.pop("pk", None)
            kwargs.pop("id", None)
            kwargs.pop("task_id", None)

            return view_func(request, obj, *args, **kwargs)

        return _wrapped_view

    return decorator
