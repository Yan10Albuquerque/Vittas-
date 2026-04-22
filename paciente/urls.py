from django.urls import path
from . import views

app_name = 'paciente'

urlpatterns = [
    path('api/', views.paciente_api, name='paciente_api'),
    path('', views.PacienteListView.as_view(), name='paciente_list'),
    path('novo/', views.PacienteCreateView.as_view(), name='paciente_create'),
    path('<int:pk>/editar/', views.PacienteUpdateView.as_view(), name='paciente_update'),
    path('<int:pk>/excluir/', views.PacienteDeleteView.as_view(), name='paciente_delete'),
    path('api/cep/<str:cep>', views.consultar_cep_api, name='consultar_cep_api'),
]
