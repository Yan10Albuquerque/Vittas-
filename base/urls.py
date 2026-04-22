from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    path('convenios/', views.ConvenioListView.as_view(), name='convenio_list'),
    path('convenios/novo/', views.ConvenioCreateView.as_view(), name='convenio_create'),
    path('convenios/<int:pk>/editar/', views.ConvenioUpdateView.as_view(), name='convenio_update'),
    path('convenios/<int:pk>/excluir/', views.ConvenioDeleteView.as_view(), name='convenio_delete'),
    
    path('especialidades/', views.EspecialidadeListView.as_view(), name='especialidade_list'),
    path('especialidades/novo/', views.EspecialidadeCreateView.as_view(), name='especialidade_create'),
    path('especialidades/<int:pk>/editar/', views.EspecialidadeUpdateView.as_view(), name='especialidade_update'),
    path('especialidades/<int:pk>/excluir/', views.EspecialidadeDeleteView.as_view(), name='especialidade_delete'),
    
    path('formas-pagamento/', views.FormaPagamentoListView.as_view(), name='forma_pagamento_list'),
    path('formas-pagamento/novo/', views.FormaPagamentoCreateView.as_view(), name='forma_pagamento_create'),
    path('formas-pagamento/<int:pk>/editar/', views.FormaPagamentoUpdateView.as_view(), name='forma_pagamento_update'),
    path('formas-pagamento/<int:pk>/excluir/', views.FormaPagamentoDeleteView.as_view(), name='forma_pagamento_delete'),
    
    path('tipos-consulta/', views.TipoConsultaListView.as_view(), name='tipo_consulta_list'),
    path('tipos-consulta/novo/', views.TipoConsultaCreateView.as_view(), name='tipo_consulta_create'),
    path('tipos-consulta/<int:pk>/editar/', views.TipoConsultaUpdateView.as_view(), name='tipo_consulta_update'),
    path('tipos-consulta/<int:pk>/excluir/', views.TipoConsultaDeleteView.as_view(), name='tipo_consulta_delete'),
    
    path('tipos-exame/', views.TipoExameListView.as_view(), name='tipo_exame_list'),
    path('tipos-exame/novo/', views.TipoExameCreateView.as_view(), name='tipo_exame_create'),
    path('tipos-exame/<int:pk>/editar/', views.TipoExameUpdateView.as_view(), name='tipo_exame_update'),
    path('tipos-exame/<int:pk>/excluir/', views.TipoExameDeleteView.as_view(), name='tipo_exame_delete'),

    path('status-agendamento/', views.StatusAgendamentoListView.as_view(), name='status_agendamento_list'),
    path('status-agendamento/novo/', views.StatusAgendamentoCreateView.as_view(), name='status_agendamento_create'),
    path('status-agendamento/<int:pk>/editar/', views.StatusAgendamentoUpdateView.as_view(), name='status_agendamento_update'),
    path('status-agendamento/<int:pk>/excluir/', views.StatusAgendamentoDeleteView.as_view(), name='status_agendamento_delete'),
    
    path('migracao-tecnologica/', views.MigracaoTecnologicaView.as_view(), name='migracao_tecnologica'),
]
