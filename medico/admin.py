from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Medico, MedicoEspecialidade, MedicoAgenda


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'crm', 'cpf', 'status', 'clinica')
    search_fields = ('nome', 'crm', 'cpf', 'clinica__nome')
    list_filter = ('status', 'clinica')


@admin.register(MedicoEspecialidade)
class MedicoEspecialidadeAdmin(SimpleHistoryAdmin):
    list_display = ('medico', 'especialidade', 'status', 'dtcad')
    search_fields = ('medico__nome', 'especialidade__descricao', 'descricao')
    list_filter = ('status', 'especialidade', 'dtcad')
    readonly_fields = ('uscad', 'dtcad')


@admin.register(MedicoAgenda)
class MedicoAgendaAdmin(SimpleHistoryAdmin):
    list_display = ('medico', 'hora', 'status', 'dtcad')
    search_fields = ('medico__nome',)
    list_filter = ('status', 'dtcad')
    readonly_fields = ('uscad', 'dtcad')
