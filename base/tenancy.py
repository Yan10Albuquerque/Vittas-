from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


MODULO_LABELS = {
    "agenda": "Agenda",
    "cadastros": "Cadastros",
    "configuracoes": "Configurações",
    "enfermagem": "Enfermagem",
    "financeiro": "Financeiro",
    "pacientes": "Pacientes",
}


def get_clinica_atual(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None

    if getattr(request.user, "tipo_usuario", "") == "COLABORADOR":
        return request.user.clinica
    return request.user


def get_clinica_id(request):
    clinica = get_clinica_atual(request)
    return clinica.id if clinica else None


def filtrar_por_clinica(queryset, request):
    clinica_id = get_clinica_id(request)
    if clinica_id and hasattr(queryset.model, "clinica_id"):
        return queryset.filter(clinica_id=clinica_id)
    return queryset


def set_clinica(instance, request):
    clinica = get_clinica_atual(request)
    if clinica and hasattr(instance, "clinica_id") and not instance.clinica_id:
        instance.clinica = clinica


def get_actor_name(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return "sistema"
    return getattr(user, "email", "") or getattr(user, "nome_exibicao", "") or f"user-{user.pk}"


def plano_libera_modulo(request, modulo):
    if getattr(request.user, "is_superuser", False):
        return True

    user = getattr(request, "user", None)
    clinica = get_clinica_atual(request)
    if not user or not clinica or not clinica.status:
        return False
    if hasattr(user, "modulo_disponivel"):
        return user.modulo_disponivel(modulo)
    return clinica.modulo_disponivel(modulo)


def get_modulo_bloqueado_message(request, modulo):
    modulo_label = MODULO_LABELS.get(modulo, modulo)
    user = getattr(request, "user", None)
    clinica = get_clinica_atual(request)

    if not user or not getattr(user, "is_authenticated", False):
        return f"É necessário fazer login para acessar o módulo {modulo_label}."

    if not clinica or not clinica.status:
        return "A clínica vinculada a este acesso está inativa."

    if not clinica.modulo_disponivel(modulo):
        return f"O plano da clínica não libera o módulo {modulo_label}."

    return f"Seu perfil não possui permissão para acessar o módulo {modulo_label}."


class ClinicaModuloRequiredMixin(LoginRequiredMixin):
    modulo_requerido = None

    def dispatch(self, request, *args, **kwargs):
        if self.modulo_requerido and not plano_libera_modulo(request, self.modulo_requerido):
            messages.error(request, get_modulo_bloqueado_message(request, self.modulo_requerido))
            return redirect("usuario:home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return filtrar_por_clinica(queryset, self.request)


def modulo_requerido(modulo):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not plano_libera_modulo(request, modulo):
                messages.error(request, get_modulo_bloqueado_message(request, modulo))
                return redirect("usuario:home")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
