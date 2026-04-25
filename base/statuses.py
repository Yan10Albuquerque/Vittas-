import unicodedata

from base.models import StatusAgendamento
from base.tenancy import filtrar_por_clinica


DEFAULT_STATUS_AGENDAMENTO = (
    {"descricao": "Agendado", "cor": "btn-primary", "nivel": 1},
    {"descricao": "Em Andamento", "cor": "btn-warning", "nivel": 2},
    {"descricao": "Finalizado", "cor": "btn-success", "nivel": 2},
    {"descricao": "Faltou", "cor": "btn-neutral", "nivel": 2},
    {"descricao": "Cancelado", "cor": "btn-error", "nivel": 2},
)


def _normalize_status_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip().lower()


def _get_status_by_terms(request, exact_matches, contains_terms=()):
    statuses = filtrar_por_clinica(
        StatusAgendamento.objects.filter(status=True).order_by("nivel", "descricao", "id"),
        request,
    )

    normalized_exact = {_normalize_status_text(value) for value in exact_matches}
    normalized_contains = [_normalize_status_text(value) for value in contains_terms]

    for status in statuses:
        descricao = _normalize_status_text(status.descricao)
        if descricao in normalized_exact:
            return status

    for status in statuses:
        descricao = _normalize_status_text(status.descricao)
        if any(term and term in descricao for term in normalized_contains):
            return status

    return None


def ensure_default_status_agendamento(clinica, actor_name="sistema"):
    if not clinica:
        return []

    created_statuses = []
    for item in DEFAULT_STATUS_AGENDAMENTO:
        status_obj, created = StatusAgendamento.objects.get_or_create(
            clinica=clinica,
            descricao=item["descricao"],
            defaults={
                "cor": item["cor"],
                "nivel": item["nivel"],
                "status": True,
                "uscad": actor_name,
                "usalt": actor_name,
            },
        )
        if created:
            created_statuses.append(status_obj)

    return created_statuses


def get_status_agendamento_padrao(request):
    return _get_status_by_terms(
        request,
        exact_matches={"agendado"},
    ) or filtrar_por_clinica(
        StatusAgendamento.objects.filter(status=True, nivel=1).order_by("nivel", "descricao", "id"),
        request,
    ).first()


def get_status_agendamento_em_andamento(request):
    return _get_status_by_terms(
        request,
        exact_matches={"em andamento", "em atendimento", "atendimento"},
        contains_terms={"andamento", "atendimento"},
    )


def get_status_agendamento_finalizado(request):
    return _get_status_by_terms(
        request,
        exact_matches={"finalizado", "concluido", "concluído"},
        contains_terms={"finaliz", "conclu"},
    )


def get_status_agendamento_em_atendimento(request):
    return get_status_agendamento_em_andamento(request)
