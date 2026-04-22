from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, UpdateView

from base.tenancy import ClinicaModuloRequiredMixin, get_actor_name, get_clinica_atual
from .forms import ClinicaForm
from .models import Clinica


class LoginView(TemplateView):
    template_name = "login.html"


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    login_url = "/login/"


class ClinicaPerfilView(ClinicaModuloRequiredMixin, UpdateView):
    model = Clinica
    form_class = ClinicaForm
    template_name = "clinicas/form.html"
    success_url = reverse_lazy("usuario:clinica_perfil")
    login_url = "/login/"
    modulo_requerido = "configuracoes"

    def dispatch(self, request, *args, **kwargs):
        if not get_clinica_atual(request):
            return redirect("usuario:login")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_clinica_atual(self.request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        form.instance.dtalt = timezone.now()
        return super().form_valid(form)


def _get_redirect_url(request):
    default_redirect = getattr(settings, "LOGIN_REDIRECT_URL", "/home/")
    redirect_url = request.POST.get("next") or default_redirect
    if not url_has_allowed_host_and_scheme(
        url=redirect_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return default_redirect
    return redirect_url


def _get_password_reset_user(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user

    user_id = request.session.get("password_reset_user_id")
    if not user_id:
        return None
    return Clinica.objects.filter(pk=user_id, status=True).first()


@csrf_protect
@require_POST
def login_api(request):
    email = (request.POST.get("email") or "").strip()
    senha = request.POST.get("senha") or ""

    clinica = Clinica.objects.filter(email__iexact=email, status=True).first()
    if not clinica or not clinica.check_password(senha):
        return JsonResponse(
            {"status": "ERROR", "message": "Dados de acesso inválidos."},
            status=400,
        )

    if clinica.reseta_senha:
        request.session["password_reset_user_id"] = clinica.pk
        return JsonResponse({"status": "SENHA_EXPIRADA"})

    request.session.pop("password_reset_user_id", None)
    login(request, clinica)
    return JsonResponse({"status": "OK", "redirect_url": _get_redirect_url(request)})


@csrf_protect
@require_POST
def alterar_senha_api(request):
    senha_atual = request.POST.get("senha_atual") or ""
    nova_senha = request.POST.get("nova_senha") or ""

    clinica = _get_password_reset_user(request)
    if not clinica:
        return JsonResponse(
            {"status": "ERROR", "message": "Solicitação de troca de senha inválida."},
            status=400,
        )

    if not clinica.check_password(senha_atual):
        return JsonResponse(
            {"status": "ERROR", "message": "Senha atual inválida."},
            status=400,
        )

    clinica.set_password(nova_senha)
    clinica.reseta_senha = False
    clinica.save(update_fields=["password", "reseta_senha"])

    request.session.pop("password_reset_user_id", None)
    login(request, clinica)
    return JsonResponse({"status": "OK", "redirect_url": _get_redirect_url(request)})


@require_POST
def logout_view(request):
    logout(request)
    request.session.pop("password_reset_user_id", None)
    return JsonResponse({"status": "OK", "redirect_url": reverse_lazy("usuario:login")})
