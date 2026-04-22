import unicodedata

from base.models import StatusAgendamento
from base.tenancy import filtrar_por_clinica


def _normalize_status_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip().lower()


def get_status_agendamento_padrao(request):
    return filtrar_por_clinica(
        StatusAgendamento.objects.filter(status=True, nivel=1).order_by("nivel", "descricao", "id"),
        request,
    ).first()


def get_status_agendamento_em_atendimento(request):
    statuses = filtrar_por_clinica(
        StatusAgendamento.objects.filter(status=True).order_by("nivel", "descricao", "id"),
        request,
    )

    exact_matches = {"em atendimento", "atendimento"}
    for status in statuses:
        descricao = _normalize_status_text(status.descricao)
        if descricao in exact_matches:
            return status

    for status in statuses:
        if "atendimento" in _normalize_status_text(status.descricao):
            return status

    return None
