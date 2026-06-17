from django.urls import path

from tasks.views import (
    task_create_view,
    task_delete_view,
    task_detail_view,
    task_edit_view,
    task_list_view,
    task_toggle_view,
)

app_name = "tasks"

urlpatterns = [
    path("", task_list_view, name="list"),
    path("create/", task_create_view, name="create"),
    path("<int:pk>/toggle/", task_toggle_view, name="toggle"),
    path("<int:pk>/edit/", task_edit_view, name="edit"),
    path("<int:pk>/detail/", task_detail_view, name="detail"),
    path("<int:pk>/delete/", task_delete_view, name="delete"),
]
