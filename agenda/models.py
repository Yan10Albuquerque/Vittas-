from django.db import models
from simple_history.models import HistoricalRecords
from base.history import resolve_history_user


class Agenda(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = 'D', 'Disponível'
        AGENDADO = 'A', 'Agendado'
        BLOQUEADO = 'B', 'Bloqueado'

    data = models.DateField(verbose_name='Data')
    hora = models.TimeField(verbose_name='Hora')
    clinica = models.ForeignKey(
        'usuario.Clinica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='agendas_consulta',
        verbose_name='Clínica',
    )
    paciente = models.ForeignKey(
        'paciente.Paciente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Paciente',
    )
    convenio = models.ForeignKey(
        'base.Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Convênio',
    )
    tipo_consulta = models.ForeignKey(
        'base.TipoConsulta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Consulta',
    )
    especialidade = models.ForeignKey(
        'base.Especialidade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Especialidade',
    )
    status_agendamento = models.ForeignKey(
        'base.StatusAgendamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Status do Agendamento',
    )
    medico = models.ForeignKey(
        'medico.Medico',
        on_delete=models.CASCADE,
        related_name='consultas_agenda',
        verbose_name='Médico',
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.DISPONIVEL,
        verbose_name='Status do Horário',
    )
    uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name='Usuário Cadastro')
    dtcad = models.DateTimeField(auto_now_add=True, verbose_name='Data Cadastro')
    usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name='Usuário Alteração')
    dtalt = models.DateTimeField(auto_now=True, verbose_name='Data Alteração')
    history = HistoricalRecords(get_user=resolve_history_user)

    def __str__(self):
        return f'{self.medico.nome} - {self.data:%d/%m/%Y} {self.hora:%H:%M}'

    class Meta:
        db_table = 'agenda'
        verbose_name = 'Agenda de Consulta'
        verbose_name_plural = 'Agendas de Consultas'
        ordering = ['data', 'hora']
        constraints = [
            models.UniqueConstraint(
                fields=['data', 'hora', 'medico'],
                name='agenda_unique_horario_medico',
            )
        ]
