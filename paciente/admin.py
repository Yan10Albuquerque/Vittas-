from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(SimpleHistoryAdmin):
	"""Expose patient history in the admin."""
	pass