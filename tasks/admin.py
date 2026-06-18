from django.contrib import admin

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "is_completed",
        "is_deleted",
        "xp_reward",
        "created_at",
        "completed_at",
        "deleted_at",
    )
    list_filter = ("is_completed", "is_deleted", "created_at", "completed_at", "user")
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "updated_at", "completed_at", "deleted_at")
    list_select_related = ("user",)

    def get_queryset(self, request):
        return Task.objects.all_with_deleted()
