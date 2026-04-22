from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Convenio, Especialidade, FormaPagamento, TipoConsulta, TipoExame, 
    TipoMaterial, StatusAgendamento, StatusAutorizacao, StatusProcedimento
)

@admin.register(Convenio)
class ConvenioAdmin(SimpleHistoryAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'status', 'dtcad']
    search_fields = ['nome', 'cnpj']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj', 'telefone', 'email', 'status')
        }),
        ('Observações', {
            'fields': ('obs',)
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Especialidade)
class EspecialidadeAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TipoConsulta)
class TipoConsultaAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TipoExame)
class TipoExameAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'recorrencia', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'recorrencia', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TipoMaterial)
class TipoMaterialAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatusAgendamento)
class StatusAgendamentoAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'cor', 'nivel', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'nivel', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'cor', 'nivel', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatusAutorizacao)
class StatusAutorizacaoAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'cor', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'cor', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatusProcedimento)
class StatusProcedimentoAdmin(SimpleHistoryAdmin):
    list_display = ['descricao', 'cor', 'status', 'dtcad']
    search_fields = ['descricao']
    list_filter = ['status', 'dtcad']
    readonly_fields = ['uscad', 'dtcad', 'usalt', 'dtalt']
    
    fieldsets = (
        ('Informações', {
            'fields': ('descricao', 'cor', 'status')
        }),
        ('Auditoria', {
            'fields': ('uscad', 'dtcad', 'usalt', 'dtalt'),
            'classes': ('collapse',)
        }),
    )
