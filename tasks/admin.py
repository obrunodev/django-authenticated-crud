from django.contrib import admin
from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "is_completed",
        "xp_reward",
        "created_at",
        "completed_at",
    )
    list_filter = ("is_completed", "created_at", "completed_at", "user")
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    list_select_related = ("user",)

