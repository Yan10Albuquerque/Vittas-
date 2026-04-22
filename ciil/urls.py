from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('admin/', admin.site.urls),
    path('', include('usuario.urls')),
    path('agenda/', include('agenda.urls')),
    path('pacientes/', include('paciente.urls')),
    path('medicos/', include('medico.urls')),
    path('', include('base.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('enfermagem/', include('enfermagem.urls')),
]
