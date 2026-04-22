from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Clinica


@admin.register(Clinica)
class ClinicaAdmin(SimpleHistoryAdmin, UserAdmin):
    model = Clinica
    ordering = ("nome_fantasia",)
    list_display = ("nome_fantasia", "email", "plano", "status", "is_staff", "is_superuser")
    list_filter = ("plano", "status", "is_staff", "is_superuser")
    search_fields = ("nome_fantasia", "razao_social", "email", "cnpj")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados da clínica", {"fields": ("nome_fantasia", "razao_social", "cnpj", "telefone", "plano")}),
        ("Status e acesso", {"fields": ("status", "reseta_senha", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Auditoria", {"fields": ("last_login", "uscad", "dtcad", "usalt", "dtalt")}),
    )
    readonly_fields = ("last_login", "dtcad", "dtalt")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nome_fantasia", "plano", "password1", "password2", "status", "is_staff"),
            },
        ),
    )
