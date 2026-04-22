from datetime import datetime, time

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from paciente.models import Paciente

class Procedimento(models.Model):
    clinica = models.ForeignKey(
        'usuario.Clinica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='procedimentos_enfermagem',
        verbose_name='Clínica',
    )
    id = models.AutoField(
        primary_key=True,
        editable=False,
        unique=True,
        null=False,
        blank=False,
        verbose_name="ID",
    )
    nome = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        default="",
        verbose_name="Nome do Procedimento",
    )
    descricao = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        default="",
        verbose_name="Descrição do Procedimento",
    )

    def __str__(self):
        return f"{self.nome} - {self.descricao}"


class Autorizacao(models.Model):

    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("APROVADA", "Aprovada"),
        ("NEGADA", "Negada"),
    ]
    clinica = models.ForeignKey(
        'usuario.Clinica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='autorizacoes_enfermagem',
        verbose_name='Clínica',
    )
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDENTE")
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def get_status_class(self):
        classes = {
            "PENDENTE": "badge bg-warning text-dark",
            "APROVADA": "badge bg-success",
            "NEGADA": "badge badge-error ",
        }
        return classes.get(self.status, "badge bg-secondary")

    def __str__(self):
        return f"{self.paciente} - {self.procedimento}"


class AgendaEnfermagem(models.Model):
    STATUS_AGENDA = [
        ("AGENDADO", "Agendado"),
        ("REALIZADO", "Realizado"),
        ("CANCELADO", "Cancelado"),
    ]
    clinica = models.ForeignKey(
        'usuario.Clinica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='agendamentos_enfermagem',
        verbose_name='Clínica',
    )
    autorizacao = models.ForeignKey(Autorizacao, on_delete=models.PROTECT)
    data_agendamento = models.DateTimeField()
    hora_agendamento = models.TimeField(default=time(9, 0))
    status = models.CharField(max_length=20, choices=STATUS_AGENDA, default="AGENDADO")
    observacoes = models.TextField(blank=True, null=True)

    @property
    def data_agendada(self):
        if isinstance(self.data_agendamento, datetime):
            return self.data_agendamento.date()
        return self.data_agendamento

    @property
    def data_hora_agendada(self):
        data_base = self.data_agendada
        if not data_base or not self.hora_agendamento:
            return None

        data_hora = datetime.combine(data_base, self.hora_agendamento)
        if timezone.is_naive(data_hora):
            return timezone.make_aware(data_hora, timezone.get_current_timezone())
        return timezone.localtime(data_hora)

    def clean(self):
        super().clean()

        if not self.autorizacao_id:
            return

        erros = {}
        data_base = self.data_agendada
        hora_base = self.hora_agendamento
        status_ativos = ["AGENDADO", "REALIZADO"]

        if self.autorizacao.status != "APROVADA":
            erros["autorizacao"] = "Somente autorizações aprovadas podem ser agendadas."

        if not data_base:
            erros["data_agendamento"] = "Informe a data do agendamento."

        if not hora_base:
            erros["hora_agendamento"] = "Informe o horário do agendamento."

        if data_base and data_base.weekday() >= 5:
            erros["data_agendamento"] = (
                "Os agendamentos da enfermagem devem ser feitos de segunda a sexta-feira."
            )

        if hora_base:
            horario_valido = (
                9 <= hora_base.hour < 18
                and hora_base.minute == 0
                and hora_base.second == 0
            )
            if not horario_valido:
                erros["hora_agendamento"] = (
                    "Os horários permitidos vão de 09:00 até 17:00, com intervalo de 1 hora."
                )

        if self.status == "AGENDADO":
            data_hora = self.data_hora_agendada
            if data_hora and data_hora < timezone.localtime():
                erros["data_agendamento"] = (
                    "Não é possível agendar em data ou horário passados."
                )

        if data_base and hora_base:
            conflito_horario = AgendaEnfermagem.objects.filter(
                data_agendamento__date=data_base,
                hora_agendamento=hora_base,
                status="AGENDADO",
            )
            if self.pk:
                conflito_horario = conflito_horario.exclude(pk=self.pk)
            if conflito_horario.exists():
                erros["hora_agendamento"] = (
                    "Este horário já está ocupado na agenda de enfermagem."
                )

        agendamento_existente = AgendaEnfermagem.objects.filter(
            autorizacao=self.autorizacao,
            status__in=status_ativos,
        )
        if self.pk:
            agendamento_existente = agendamento_existente.exclude(pk=self.pk)
        if agendamento_existente.exists():
            erros["autorizacao"] = "Esta autorização já possui um agendamento ativo."

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.autorizacao} - {self.data_agendamento} {self.hora_agendamento}"

    class Meta:
        ordering = ["data_agendamento", "hora_agendamento"]
