from datetime import datetime, timedelta

from django.utils import timezone

from base.statuses import (
    get_status_agendamento_em_andamento,
    get_status_agendamento_finalizado,
    get_status_agendamento_padrao,
)

from .models import Agenda


def _normalize_status_text(value):
    return (value or "").strip().lower()


def is_automatic_status(status_obj):
    if not status_obj:
        return True

    descricao = _normalize_status_text(status_obj.descricao)
    return descricao in {
        "agendado",
        "em andamento",
        "em atendimento",
        "finalizado",
    }


def get_slot_end_datetime(consulta, next_hora=None):
    start_dt = datetime.combine(consulta.data, consulta.hora)
    if next_hora:
        end_dt = datetime.combine(consulta.data, next_hora)
        if end_dt > start_dt:
            return end_dt
    return start_dt + timedelta(minutes=30)


def get_expected_status_for_agenda(consulta, request, next_hora=None):
    if consulta.status != Agenda.Status.AGENDADO or not consulta.paciente_id:
        return consulta.status_agendamento

    agendado = get_status_agendamento_padrao(request)
    em_andamento = get_status_agendamento_em_andamento(request)
    finalizado = get_status_agendamento_finalizado(request)
    now = timezone.localtime()
    start_dt = timezone.make_aware(datetime.combine(consulta.data, consulta.hora))
    end_dt = timezone.make_aware(get_slot_end_datetime(consulta, next_hora))

    if now >= end_dt:
        return finalizado or consulta.status_agendamento or agendado
    if now >= start_dt:
        return em_andamento or consulta.status_agendamento or agendado
    return agendado or consulta.status_agendamento


def sync_agenda_status(consulta, request, next_hora=None, actor_name=None):
    if not is_automatic_status(consulta.status_agendamento):
        return consulta.status_agendamento

    expected_status = get_expected_status_for_agenda(consulta, request, next_hora=next_hora)
    if expected_status and consulta.status_agendamento_id != expected_status.pk:
        consulta.status_agendamento = expected_status
        update_fields = ["status_agendamento", "dtalt"]
        if actor_name:
            consulta.usalt = actor_name
            update_fields.append("usalt")
        consulta.save(update_fields=update_fields)
    return consulta.status_agendamento
