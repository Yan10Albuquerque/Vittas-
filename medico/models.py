from django.db import models
from simple_history.models import HistoricalRecords


class Medico(models.Model):
	clinica = models.ForeignKey(
		'usuario.Clinica',
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name='medicos',
		verbose_name='Clínica',
	)
	cpf = models.CharField(max_length=14, null=True, blank=True, verbose_name="CPF")
	crm = models.CharField(max_length=20, verbose_name="CRM")
	nome = models.CharField(max_length=80, verbose_name="Nome")
	celular = models.CharField(max_length=15, null=True, blank=True, verbose_name="Celular")
	telefone = models.CharField(max_length=15, null=True, blank=True, verbose_name="Telefone")
	email = models.EmailField(max_length=100, null=True, blank=True, verbose_name="E-mail")
	obs = models.TextField(blank=True, verbose_name="Observações")
	status = models.BooleanField(default=True, verbose_name="Ativo")
	uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
	dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
	usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
	dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
	history = HistoricalRecords()

	def __str__(self):
		return f"{self.nome} - {self.crm}"

	class Meta:
		db_table = 'medico'
		verbose_name = 'Médico'
		verbose_name_plural = 'Médicos'
		ordering = ['nome']
		constraints = [
			models.UniqueConstraint(fields=['clinica', 'crm'], name='medico_unique_crm_por_clinica')
		]


class MedicoEspecialidade(models.Model):
	clinica = models.ForeignKey(
		'usuario.Clinica',
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name='medico_especialidades',
		verbose_name='Clínica',
	)
	medico = models.ForeignKey(
		'Medico',
		on_delete=models.CASCADE,
		related_name='especialidades',
		verbose_name="Médico",
	)
	especialidade = models.ForeignKey(
		'base.Especialidade',
		on_delete=models.PROTECT,
		verbose_name="Especialidade",
	)
	descricao = models.CharField(
		max_length=100,
		blank=True,
		verbose_name="Descrição/Observação",
	)
	status = models.BooleanField(default=True, verbose_name="Ativo")
	uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
	dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
	history = HistoricalRecords()

	def __str__(self):
		return f"{self.medico.nome} - {self.especialidade.descricao}"

	class Meta:
		db_table = 'medico_especialidade'
		verbose_name = 'Médico Especialidade'
		verbose_name_plural = 'Médicos Especialidades'
		ordering = ['medico__nome', 'especialidade__descricao']
		unique_together = [['medico', 'especialidade']]

class MedicoAgenda(models.Model):
	clinica = models.ForeignKey(
		'usuario.Clinica',
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name='medico_agendas',
		verbose_name='Clínica',
	)
	medico = models.ForeignKey(
		'Medico',
		on_delete=models.CASCADE,
		related_name='agendas',
		verbose_name="Médico",
	)
	hora = models.TimeField(verbose_name="Hora")
	status = models.BooleanField(default=True, verbose_name="Ativo")
	uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
	dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
	history = HistoricalRecords()

	def __str__(self):
		return f"{self.medico.nome} - {self.hora.strftime('%H:%M')}"

	class Meta:
		db_table = 'medico_agenda'
		verbose_name = 'Médico Agenda'
		verbose_name_plural = 'Médicos Agendas'
		ordering = ['medico__nome', 'hora']
