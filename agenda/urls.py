from django.urls import path

from .views import (
    AgendaConsultasView,
    agenda_api,
    finalizar_atendimento,
    iniciar_atendimento,
    medico_especialidades_api,
)

app_name = 'agenda'

urlpatterns = [
    path('consultas/', AgendaConsultasView.as_view(), name='agenda_consultas'),
    path('consultas/<int:pk>/iniciar/', iniciar_atendimento, name='agenda_iniciar_atendimento'),
    path('consultas/<int:pk>/finalizar/', finalizar_atendimento, name='agenda_finalizar_atendimento'),
    path('api/', agenda_api, name='agenda_api'),
    path('api/medicos/<int:medico_id>/especialidades/', medico_especialidades_api, name='medico_especialidades_api'),
]
