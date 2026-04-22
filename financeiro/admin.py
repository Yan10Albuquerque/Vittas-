from django.contrib import admin

from .models import CategoriaFinanceira, LancamentoFinanceiro


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("descricao", "tipo", "clinica", "status")
    list_filter = ("tipo", "status", "clinica")
    search_fields = ("descricao",)


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("descricao", "tipo", "status", "cliente_display", "valor", "data_vencimento", "clinica")
    list_filter = ("tipo", "status", "origem", "clinica")
    search_fields = ("descricao", "nome_cliente", "paciente__nome", "convenio__nome")
