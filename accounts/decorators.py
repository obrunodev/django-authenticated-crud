import functools
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
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
