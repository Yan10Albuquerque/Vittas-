from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path("", views.FinanceiroDashboardView.as_view(), name="dashboard"),
    path("lancamentos/", views.LancamentoFinanceiroListView.as_view(), name="lancamento_list"),
    path("lancamentos/novo/", views.LancamentoFinanceiroCreateView.as_view(), name="lancamento_create"),
    path("lancamentos/<int:pk>/editar/", views.LancamentoFinanceiroUpdateView.as_view(), name="lancamento_update"),
    path("lancamentos/<int:pk>/baixar/", views.baixar_lancamento, name="lancamento_baixar"),
    path("lancamentos/<int:pk>/cancelar/", views.cancelar_lancamento, name="lancamento_cancelar"),
    path("categorias/", views.CategoriaFinanceiraListView.as_view(), name="categoria_list"),
    path("categorias/nova/", views.CategoriaFinanceiraCreateView.as_view(), name="categoria_create"),
    path("categorias/<int:pk>/editar/", views.CategoriaFinanceiraUpdateView.as_view(), name="categoria_update"),
    path("vendas/", views.vendas, name="vendas"),
]
