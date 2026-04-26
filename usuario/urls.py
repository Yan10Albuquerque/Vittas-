from django.urls import path

from .views import (
    ClinicaPerfilView,
    ColaboradorCreateView,
    ColaboradorListView,
    ColaboradorToggleStatusView,
    ColaboradorUpdateView,
    HomeView,
    LoginView,
    alterar_senha_api,
    login_api,
    logout_view,
)

app_name = "usuario"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("home/", HomeView.as_view(), name="home"),
    path("clinica/", ClinicaPerfilView.as_view(), name="clinica_perfil"),
    path("clinicas/", ClinicaPerfilView.as_view(), name="clinicas_list"),
    path("equipe/", ColaboradorListView.as_view(), name="colaborador_list"),
    path("equipe/novo/", ColaboradorCreateView.as_view(), name="colaborador_create"),
    path("equipe/<int:pk>/editar/", ColaboradorUpdateView.as_view(), name="colaborador_update"),
    path("equipe/<int:pk>/status/", ColaboradorToggleStatusView.as_view(), name="colaborador_toggle_status"),
    path("api/login/", login_api, name="login_api"),
    path("api/alterar-senha/", alterar_senha_api, name="alterar_senha_api"),
    path("api/logout/", logout_view, name="logout_api"),
]
