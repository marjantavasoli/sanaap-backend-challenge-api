from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Adds the role field to the default Django user admin.

    This is how an admin creates users and assigns roles (per the task),
    without needing a separate user-management API.
    """

    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Role", {"fields": ("role",)}),)
