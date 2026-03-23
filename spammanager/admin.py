from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser, Client
from .models import Message, Mailing, MailingAttempt


# Кастомный UserAdmin для CustomUser
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["email", "name", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["email", "name"]
    ordering = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личная информация", {"fields": ("name", "comment")}),
        (
            "Права доступа",
            {"fields": ("is_active", "is_staff", "groups", "user_permissions")},
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


# Регистрируем модели
admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "owner", "created_at"]
    list_filter = ["owner", "created_at"]
    search_fields = ["email", "full_name"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "owner", "created_at"]
    list_filter = ["owner", "created_at"]
    search_fields = ["subject"]


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ["id", "start_time", "end_time", "status", "owner", "is_active"]
    list_filter = ["status", "is_active", "owner"]
    search_fields = ["message__subject"]
    filter_horizontal = ["recipients"]
    readonly_fields = ["status"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("message", "owner")


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ["mailing", "attempt_time", "status", "recipient"]
    list_filter = ["status", "mailing"]
    search_fields = ["server_response"]
    readonly_fields = ["attempt_time"]
