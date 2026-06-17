from django.urls import path

from accounts.views import (
    dashboard_view,
    login_view,
    logout_view,
    register_view,
    stats_view,
)

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("stats/", stats_view, name="stats"),
]
