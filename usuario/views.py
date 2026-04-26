from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from base.tenancy import ClinicaModuloRequiredMixin, get_actor_name, get_clinica_atual
from .forms import ClinicaForm, ColaboradorForm
from .models import Clinica, Colaborador


class LoginView(TemplateView):
    template_name = "login.html"


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    login_url = "/login/"


def _usuario_pode_gerenciar_equipe(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and getattr(user, "pode_gerenciar_equipe", False))


class EquipeManagementMixin(ClinicaModuloRequiredMixin):
    modulo_requerido = "configuracoes"
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        if not _usuario_pode_gerenciar_equipe(request):
            messages.error(request, "Seu perfil não possui permissão para gerenciar a equipe.")
            return redirect("usuario:home")
        return super().dispatch(request, *args, **kwargs)

    def get_clinica(self):
        return get_clinica_atual(self.request)


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


class ColaboradorListView(EquipeManagementMixin, ListView):
    model = Colaborador
    template_name = "usuarios/list.html"
    context_object_name = "colaboradores"

    def get_queryset(self):
        queryset = (
            Colaborador.objects.filter(clinica=self.get_clinica())
            .select_related("clinica")
            .order_by("nome")
        )
        busca = (self.request.GET.get("busca") or "").strip()
        if busca:
            queryset = queryset.filter(nome__icontains=busca)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinica = self.get_clinica()
        context["clinica"] = clinica
        context["limite_colaboradores"] = clinica.limite_colaboradores
        context["total_colaboradores_ativos"] = clinica.colaboradores_ativos().count()
        return context


class ColaboradorCreateView(EquipeManagementMixin, CreateView):
    model = Colaborador
    form_class = ColaboradorForm
    template_name = "usuarios/form.html"
    success_url = reverse_lazy("usuario:colaborador_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["clinica"] = self.get_clinica()
        return kwargs

    def form_valid(self, form):
        form.instance.uscad = get_actor_name(self.request)
        form.instance.usalt = get_actor_name(self.request)
        messages.success(self.request, "Colaborador cadastrado com sucesso.")
        return super().form_valid(form)


class ColaboradorUpdateView(EquipeManagementMixin, UpdateView):
    model = Colaborador
    form_class = ColaboradorForm
    template_name = "usuarios/form.html"
    success_url = reverse_lazy("usuario:colaborador_list")

    def get_queryset(self):
        return Colaborador.objects.filter(clinica=self.get_clinica())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["clinica"] = self.get_clinica()
        return kwargs

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        messages.success(self.request, "Colaborador atualizado com sucesso.")
        return super().form_valid(form)


class ColaboradorToggleStatusView(EquipeManagementMixin, UpdateView):
    model = Colaborador
    fields = []
    success_url = reverse_lazy("usuario:colaborador_list")

    def get_queryset(self):
        return Colaborador.objects.filter(clinica=self.get_clinica())

    def post(self, request, *args, **kwargs):
        colaborador = self.get_object()
        novo_status = not colaborador.status
        if novo_status and not colaborador.clinica.pode_adicionar_colaborador(colaborador_atual=colaborador):
            messages.error(
                request,
                "O plano Profissional permite até 5 colaboradores ativos.",
            )
            return redirect(self.success_url)

        colaborador.status = novo_status
        colaborador.usalt = get_actor_name(request)
        colaborador.save(update_fields=["status", "usalt", "dtalt"])
        messages.success(
            request,
            "Status do colaborador atualizado com sucesso.",
        )
        return redirect(self.success_url)


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


def _set_password_reset_user(request, user):
    request.session["password_reset_user_id"] = user.pk
    request.session["password_reset_user_type"] = getattr(user, "tipo_usuario", "CLINICA")


def _clear_password_reset_user(request):
    request.session.pop("password_reset_user_id", None)
    request.session.pop("password_reset_user_type", None)


def _get_password_reset_user(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user

    user_id = request.session.get("password_reset_user_id")
    if not user_id:
        return None
    user_type = request.session.get("password_reset_user_type", "CLINICA")
    if user_type == "COLABORADOR":
        return Colaborador.objects.select_related("clinica").filter(pk=user_id, status=True, clinica__status=True).first()
    return Clinica.objects.filter(pk=user_id, status=True).first()


def _authenticate_principal(request, email, senha):
    clinica = authenticate(
        request,
        email=email,
        password=senha,
        backend="usuario.auth_backends.ClinicaAuthBackend",
    )
    if clinica:
        return clinica

    colaborador = authenticate(
        request,
        email=email,
        password=senha,
        backend="usuario.auth_backends.ColaboradorAuthBackend",
    )
    if colaborador:
        return colaborador

    return None


@csrf_protect
@require_POST
def login_api(request):
    email = (request.POST.get("email") or "").strip()
    senha = request.POST.get("senha") or ""

    principal = _authenticate_principal(request, email, senha)
    if not principal:
        return JsonResponse(
            {"status": "ERROR", "message": "Dados de acesso inválidos."},
            status=400,
        )

    if principal.reseta_senha:
        _set_password_reset_user(request, principal)
        return JsonResponse({"status": "SENHA_EXPIRADA"})

    _clear_password_reset_user(request)
    if isinstance(principal, Clinica):
        principal.backend = "usuario.auth_backends.ClinicaAuthBackend"
    else:
        principal.backend = "usuario.auth_backends.ColaboradorAuthBackend"
    login(request, principal)
    return JsonResponse({"status": "OK", "redirect_url": _get_redirect_url(request)})


@csrf_protect
@require_POST
def alterar_senha_api(request):
    senha_atual = request.POST.get("senha_atual") or ""
    nova_senha = request.POST.get("nova_senha") or ""

    principal = _get_password_reset_user(request)
    if not principal:
        return JsonResponse(
            {"status": "ERROR", "message": "Solicitação de troca de senha inválida."},
            status=400,
        )

    if not principal.check_password(senha_atual):
        return JsonResponse(
            {"status": "ERROR", "message": "Senha atual inválida."},
            status=400,
        )

    principal.set_password(nova_senha)
    principal.reseta_senha = False
    principal.save(update_fields=["password", "reseta_senha"])

    _clear_password_reset_user(request)
    if isinstance(principal, Clinica):
        principal.backend = "usuario.auth_backends.ClinicaAuthBackend"
    else:
        principal.backend = "usuario.auth_backends.ColaboradorAuthBackend"
    login(request, principal)
    return JsonResponse({"status": "OK", "redirect_url": _get_redirect_url(request)})


@require_POST
def logout_view(request):
    logout(request)
    _clear_password_reset_user(request)
    return JsonResponse({"status": "OK", "redirect_url": reverse_lazy("usuario:login")})
