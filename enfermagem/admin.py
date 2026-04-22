from django.contrib import admin
from .models import Autorizacao, Procedimento, AgendaEnfermagem

@admin.register(Autorizacao)
class AutorizacaoAdmin(admin.ModelAdmin):    
    list_display = ('paciente', 'procedimento', 'status', 'data_solicitacao')
    list_filter = ('status',)
    search_fields = ('paciente__nome', 'procedimento__descricao')

@admin.register(Procedimento)
class ProcedimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')

    
@admin.register(AgendaEnfermagem)
class AgendaEnfermagemAdmin(admin.ModelAdmin):
    list_display = ('autorizacao', 'data_agendamento', 'status')
    list_filter = ('status',)
    search_fields = ('autorizacao__paciente__nome', 'autorizacao__procedimento__nome')
    
