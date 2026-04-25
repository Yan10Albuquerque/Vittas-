from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class Paciente(models.Model):
    clinica = models.ForeignKey(
        "usuario.Clinica",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="pacientes",
        verbose_name="Clínica",
    )
    cpf = models.CharField(max_length=15)
    nome = models.CharField(max_length=80)
    celular = models.CharField(max_length=15)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    documento = models.CharField(max_length=45, null=True, blank=True)
    nascimento = models.DateField()
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sexo = models.CharField(max_length=10, null=True, blank=True)
    profissao = models.CharField(max_length=45, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    logradouro = models.CharField(max_length=80, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField(max_length=45, null=True, blank=True)
    bairro = models.CharField(max_length=45, null=True, blank=True)
    cidade = models.CharField(max_length=45, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)
    mae = models.CharField(max_length=80, null=True, blank=True)
    pai = models.CharField(max_length=80, null=True, blank=True)
    convenio = models.ForeignKey(
        "base.Convenio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Convênio",
    )
    carteira_conv = models.CharField(max_length=25, null=True, blank=True)
    carteira_sus = models.CharField(max_length=45, null=True, blank=True)
    obs = models.CharField(max_length=100, null=True, blank=True)
    prontuario = models.TextField(blank=True, verbose_name="Prontuário")
    status = models.BooleanField(default=True, verbose_name="Ativo")
    uscad = models.CharField(max_length=25, null=True, blank=True)
    dtcad = models.DateTimeField(auto_now_add=True)
    usalt = models.CharField(max_length=25, null=True, blank=True)
    dtalt = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.nome

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["clinica", "cpf"], name="paciente_unique_cpf_por_clinica"
            )
        ]


class PacienteVacina(models.Model):
    clinica = models.ForeignKey(
        "usuario.Clinica",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="paciente_vacinas",
        verbose_name="Clínica",
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="vacinas",
        verbose_name="Paciente",
    )
    data_aplicacao = models.DateField(null=True, blank=True)
    descricao_vacina = models.CharField(max_length=100, null=True, blank=True)
    aplicador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacinas_aplicadas",
        verbose_name="Aplicador",
    )
    forma_pagamento = models.ForeignKey(
        "base.FormaPagamento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Forma de Pagamento",
    )
    valor = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    obs = models.CharField(max_length=1000, null=True, blank=True)
    uscad = models.CharField(max_length=25, null=True, blank=True)
    dtcad = models.DateTimeField(auto_now_add=True)
    usalt = models.CharField(max_length=25, null=True, blank=True)
    dtalt = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return (
            f"{self.paciente.nome} - {self.descricao_vacina or 'Vacina não informada'}"
        )

    class Meta:
        verbose_name = "Vacina do Paciente"
        verbose_name_plural = "Vacinas do Paciente"
