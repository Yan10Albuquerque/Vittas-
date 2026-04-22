from django.urls import path
from .views import *

app_name = 'enfermagem'

urlpatterns = [
    path('autorizacoes/', AutorizacaoListView, name='autorizacao_list_public'),
    path('autorizacao-list/', AutorizacaoListView, name='autorizacao_list'),
    path('nova-autorizacao/', NovaAutorizacaoView, name='nova_autorizacao'),
    path('<int:pk>/autorizacao-delete/', AutorizacaoDeleteView, name='autorizacao_delete'),
    path('<int:pk>/editar/', AutorizacaoUpdateView, name='autorizacao_update'),
    path('aprovados/', AprovadosListView, name='aprovados_list'),
    path('aprovados/<int:pk>/agendar/', agendar, name='agendamento_create'),
    path('aprovados/<int:pk>/horarios-disponiveis/', horarios_disponiveis_view, name='horarios_disponiveis'),
    path('agendamentos/<int:pk>/cancelar/', cancelar_agendamento, name='agendamento_cancelar'),
    path('agendamentos/<int:pk>/realizar/', realizar_agendamento, name='agendamento_realizar'),
    path('procedimentos/', ProcedimentoListView, name='procedimento_list'),
    path('novo-procedimento/', ProcedimentoCreateView, name='procedimento_create'),
    path('<int:pk>/procedimento-update/', ProcedimentoUpdateView, name='procedimento_update'),
    path('<int:pk>/procedimento-delete/', ProcedimentoDeleteView, name='procedimento_delete'),
]
