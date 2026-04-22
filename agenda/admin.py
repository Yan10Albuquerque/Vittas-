from django.contrib import admin
from .models import Agenda 

@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ('data', 'hora', 'clinica', 'paciente', 'status_agendamento', 'medico')
    list_filter = ('data', 'hora', 'clinica', 'paciente', 'status_agendamento', 'medico')
    search_fields = ('paciente__nome', 'medico__nome')
    ordering = ('data', 'hora')
   
    
    
    