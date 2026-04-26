from django.db import models
from simple_history.models import HistoricalRecords
from base.history import resolve_history_user

# Create your models here.

class Convenio(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='convenios',
    verbose_name='Clínica',
  )
  cnpj = models.CharField(max_length=20, null=True, blank=True)
  nome = models.CharField(max_length=80)
  telefone = models.CharField(max_length=15, null=True, blank=True)
  email = models.EmailField(max_length=100, null=True, blank=True)
  obs = models.TextField(blank=True, verbose_name="Observações")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.nome

  class Meta:
    db_table = 'convenio'
    verbose_name = 'Convênio'
    verbose_name_plural = 'Convênios'


class Especialidade(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='especialidades',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'especialidade'
    verbose_name = 'Especialidade'
    verbose_name_plural = 'Especialidades'
    ordering = ['descricao']


class FormaPagamento(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='formas_pagamento',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'fpagamento'
    verbose_name = 'Forma de Pagamento'
    verbose_name_plural = 'Formas de Pagamento'
    ordering = ['descricao']


class TipoConsulta(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='tipos_consulta',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'tipo_consulta'
    verbose_name = 'Tipo de Consulta'
    verbose_name_plural = 'Tipos de Consulta'
    ordering = ['descricao']


class TipoExame(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='tipos_exame',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  recorrencia = models.PositiveIntegerField(verbose_name="Recorrência (dias)")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'tipo_exame'
    verbose_name = 'Tipo de Exame'
    verbose_name_plural = 'Tipos de Exame'
    ordering = ['descricao']


class TipoMaterial(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='tipos_materiais',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'tipo_material'
    verbose_name = 'Tipo de Material'
    verbose_name_plural = 'Tipos de Material'
    ordering = ['descricao']


class StatusAgendamento(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='status_agendamento',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  cor = models.CharField(max_length=45, verbose_name="Cor")
  nivel = models.IntegerField(default=1, verbose_name="Nível")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'status_agendamento'
    verbose_name = 'Status de Agendamento'
    verbose_name_plural = 'Status de Agendamento'
    ordering = ['nivel', 'descricao']


class StatusAutorizacao(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='status_autorizacao',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  cor = models.CharField(max_length=45, verbose_name="Cor")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'status_autorizacao'
    verbose_name = 'Status de Autorização'
    verbose_name_plural = 'Status de Autorização'
    ordering = ['descricao']


class StatusProcedimento(models.Model):
  clinica = models.ForeignKey(
    'usuario.Clinica',
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name='status_procedimento',
    verbose_name='Clínica',
  )
  descricao = models.CharField(max_length=45, verbose_name="Descrição")
  cor = models.CharField(max_length=45, verbose_name="Cor")
  status = models.BooleanField(default=True, verbose_name="Ativo")
  uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
  dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
  usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
  dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
  history = HistoricalRecords(get_user=resolve_history_user)

  def __str__(self):
    return self.descricao

  class Meta:
    db_table = 'status_procedimento'
    verbose_name = 'Status de Procedimento'
    verbose_name_plural = 'Status de Procedimento'
    ordering = ['descricao']
