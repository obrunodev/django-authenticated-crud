from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (*UserAdmin.list_display, "level", "experience_points")
    list_filter = (*UserAdmin.list_filter, "level")
    fieldsets = (
        *UserAdmin.fieldsets,
        ("Gamificação", {"fields": ("level", "experience_points")}),
    )
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        ("Gamificação", {"fields": ("level", "experience_points")}),
    )
