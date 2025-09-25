from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from . import models


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (
            _("General"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password",
                )
            },
        ),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups")},
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            _("General"),
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = (
        "email",
        "first_name",
        "last_name",
        "last_login",
        "date_joined",
        "is_active",
    )

    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    list_filter = ("is_active",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)

        return qs

    def has_module_permission(self, request):
        return request.user.is_superuser
