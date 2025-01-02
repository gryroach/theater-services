from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


class UserAdmin(BaseUserAdmin):
    list_display = (
        "login",
        "first_name",
        "last_name",
        "is_active",
        "is_admin",
        "is_moderator",
    )
    search_fields = ("login", "first_name", "last_name")
    readonly_fields = ("id",)

    fieldsets = (
        (None, {"fields": ("login", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_admin", "is_moderator")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "login",
                    "password1",
                    "password2",
                    "is_active",
                    "is_admin",
                    "is_moderator",
                ),
            },
        ),
    )

    ordering = ("login",)


admin.site.register(User, UserAdmin)
