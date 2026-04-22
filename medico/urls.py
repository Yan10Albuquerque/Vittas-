from django.urls import path
from . import views

app_name = 'medico'

urlpatterns = [
    path('', views.MedicoListView.as_view(), name='medico_list'),
    path('novo/', views.MedicoCreateView.as_view(), name='medico_create'),
    path('<int:pk>/editar/', views.MedicoUpdateView.as_view(), name='medico_update'),
    path('<int:pk>/excluir/', views.MedicoDeleteView.as_view(), name='medico_delete'),
    path(
        '<int:pk>/especialidades/<int:vinculo_id>/excluir/',
        views.MedicoEspecialidadeDeleteView.as_view(),
        name='medico_especialidade_delete',
    ),
]
