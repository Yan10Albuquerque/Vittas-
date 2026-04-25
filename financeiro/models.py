from decimal import Decimal

from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class CategoriaFinanceira(models.Model):
    class Tipo(models.TextChoices):
        RECEITA = "RECEITA", "Receita"
        DESPESA = "DESPESA", "Despesa"

    clinica = models.ForeignKey(
        "usuario.Clinica",
        on_delete=models.PROTECT,
        related_name="categorias_financeiras",
        verbose_name="Clínica",
    )
    descricao = models.CharField(max_length=80, verbose_name="Descrição")
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.RECEITA,
        verbose_name="Tipo",
    )
    cor = models.CharField(max_length=20, default="badge-primary", verbose_name="Cor")
    status = models.BooleanField(default=True, verbose_name="Ativa")
    uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
    dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
    usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
    dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Categoria Financeira"
        verbose_name_plural = "Categorias Financeiras"
        ordering = ["tipo", "descricao"]
        constraints = [
            models.UniqueConstraint(
                fields=["clinica", "tipo", "descricao"],
                name="financeiro_categoria_unique_por_clinica",
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao}"


class LancamentoFinanceiro(models.Model):
    class Tipo(models.TextChoices):
        RECEITA = "RECEITA", "Receita"
        DESPESA = "DESPESA", "Despesa"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"
        ATRASADO = "ATRASADO", "Atrasado"
        CANCELADO = "CANCELADO", "Cancelado"
        PARCIAL = "PARCIAL", "Parcial"

    class Origem(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        VACINA = "VACINA", "Vacina"
        PROCEDIMENTO = "PROCEDIMENTO", "Procedimento"
        CONSULTA = "CONSULTA", "Consulta"
        OUTRO = "OUTRO", "Outro"

    clinica = models.ForeignKey(
        "usuario.Clinica",
        on_delete=models.PROTECT,
        related_name="lancamentos_financeiros",
        verbose_name="Clínica",
    )
    paciente = models.ForeignKey(
        "paciente.Paciente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_financeiros",
        verbose_name="Paciente",
    )
    convenio = models.ForeignKey(
        "base.Convenio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_financeiros",
        verbose_name="Convênio",
    )
    vacina = models.OneToOneField(
        "paciente.PacienteVacina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamento_financeiro",
        verbose_name="Vacina",
    )
    categoria = models.ForeignKey(
        CategoriaFinanceira,
        on_delete=models.PROTECT,
        related_name="lancamentos",
        verbose_name="Categoria",
    )
    forma_pagamento = models.ForeignKey(
        "base.FormaPagamento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_financeiros",
        verbose_name="Forma de Pagamento",
    )
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.RECEITA,
        verbose_name="Tipo",
    )
    origem = models.CharField(
        max_length=20,
        choices=Origem.choices,
        default=Origem.MANUAL,
        verbose_name="Origem",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )
    descricao = models.CharField(max_length=120, verbose_name="Descrição")
    nome_cliente = models.CharField(max_length=80, null=True, blank=True, verbose_name="Cliente")
    data_lancamento = models.DateField(default=timezone.localdate, verbose_name="Data do Lançamento")
    competencia = models.DateField(default=timezone.localdate, verbose_name="Competência")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    valor_recebido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Recebido/Pago",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
    dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
    usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
    dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Lançamentos Financeiros"
        ordering = ["-data_vencimento", "-id"]

    def __str__(self):
        return f"{self.descricao} - {self.valor}"

    @property
    def status_badge_class(self):
        mapa = {
            self.Status.PENDENTE: "badge-ghost text-base-content",
            self.Status.PAGO: "badge-success text-success-content",
            self.Status.ATRASADO: "badge-error text-error-content",
            self.Status.CANCELADO: "badge-neutral text-neutral-content",
            self.Status.PARCIAL: "badge-warning text-warning-content",
        }
        return mapa.get(self.status, "badge-ghost")

    @property
    def status_badge_label(self):
        return self.get_status_display()

    @property
    def cliente_display(self):
        if self.paciente_id and self.paciente:
            return self.paciente.nome
        if self.convenio_id and self.convenio:
            return self.convenio.nome
        return self.nome_cliente or "-"

    @property
    def valor_em_aberto(self):
        recebido = self.valor_recebido or Decimal("0.00")
        aberto = self.valor - recebido
        return aberto if aberto > 0 else Decimal("0.00")

    def atualizar_status(self):
        if self.status == self.Status.CANCELADO:
            return

        recebido = self.valor_recebido or Decimal("0.00")
        hoje = timezone.localdate()

        if recebido >= self.valor and self.valor > 0:
            self.status = self.Status.PAGO
            if not self.data_pagamento:
                self.data_pagamento = hoje
            return

        if recebido > 0:
            self.status = self.Status.PARCIAL
            return

        if self.data_vencimento and self.data_vencimento < hoje:
            self.status = self.Status.ATRASADO
        else:
            self.status = self.Status.PENDENTE

    def save(self, *args, **kwargs):
        if not self.nome_cliente:
            if self.paciente_id and self.paciente:
                self.nome_cliente = self.paciente.nome
            elif self.convenio_id and self.convenio:
                self.nome_cliente = self.convenio.nome

        if not self.valor_recebido and self.status == self.Status.PAGO:
            self.valor_recebido = self.valor

        self.atualizar_status()
        return super().save(*args, **kwargs)
