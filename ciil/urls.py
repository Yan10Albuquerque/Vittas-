from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views import View


class RootRedirectView(View):
    def get(self, request, *args, **kwargs):
        if getattr(request, "user", None) and request.user.is_authenticated:
            return redirect("usuario:home")
        return redirect("usuario:login")

urlpatterns = [
    path('', RootRedirectView.as_view()),
    path('admin/', admin.site.urls),
    path('', include('usuario.urls')),
    path('agenda/', include('agenda.urls')),
    path('pacientes/', include('paciente.urls')),
    path('medicos/', include('medico.urls')),
    path('', include('base.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('enfermagem/', include('enfermagem.urls')),
]
