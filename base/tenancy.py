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
    clinica = get_clinica_atual(request)
    if not clinica:
        return "sistema"
    return clinica.email or clinica.nome_fantasia or f"clinica-{clinica.pk}"


def plano_libera_modulo(request, modulo):
    if getattr(request.user, "is_superuser", False):
        return True

    clinica = get_clinica_atual(request)
    if not clinica or not clinica.status:
        return False
    return clinica.modulo_disponivel(modulo)


class ClinicaModuloRequiredMixin(LoginRequiredMixin):
    modulo_requerido = None

    def dispatch(self, request, *args, **kwargs):
        if self.modulo_requerido and not plano_libera_modulo(request, self.modulo_requerido):
            modulo_label = MODULO_LABELS.get(self.modulo_requerido, self.modulo_requerido)
            messages.error(
                request,
                f"O plano da clínica não libera o módulo {modulo_label}.",
            )
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
                modulo_label = MODULO_LABELS.get(modulo, modulo)
                messages.error(
                    request,
                    f"O plano da clínica não libera o módulo {modulo_label}.",
                )
                return redirect("usuario:home")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
