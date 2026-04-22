from datetime import datetime, time, timedelta
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from base.tenancy import filtrar_por_clinica, get_clinica_atual, modulo_requerido
from .models import AgendaEnfermagem, Autorizacao, Paciente, Procedimento


def _aplicar_status_exibicao_autorizacoes(autorizacoes):
    for autorizacao in autorizacoes:
        agendamento_ativo = getattr(autorizacao, "agendamentos_vinculados", [])
        agendamento_ativo = agendamento_ativo[0] if agendamento_ativo else None

        autorizacao.agendamento_ativo = agendamento_ativo
        autorizacao.pode_agendar = agendamento_ativo is None

        if agendamento_ativo and agendamento_ativo.status == "AGENDADO":
            autorizacao.status_exibicao = "Agendado"
            autorizacao.status_exibicao_class = "badge bg-info text-dark"
        elif agendamento_ativo and agendamento_ativo.status == "REALIZADO":
            autorizacao.status_exibicao = "Realizado"
            autorizacao.status_exibicao_class = "badge bg-primary text-primary-content"
        else:
            autorizacao.status_exibicao = autorizacao.get_status_display()
            autorizacao.status_exibicao_class = autorizacao.get_status_class()

    return autorizacoes


@login_required
@modulo_requerido("enfermagem")
def AutorizacaoListView(request):
    busca = (request.GET.get("busca") or "").strip()
    agendamentos_prefetch = Prefetch(
        "agendaenfermagem_set",
        queryset=filtrar_por_clinica(
            AgendaEnfermagem.objects.exclude(status="CANCELADO").order_by("data_agendamento", "hora_agendamento"),
            request,
        ),
        to_attr="agendamentos_vinculados",
    )
    lista_autorizacoes = (
        filtrar_por_clinica(Autorizacao.objects.select_related("paciente", "procedimento"), request)
        .prefetch_related(agendamentos_prefetch)
        .order_by("-data_resposta", "-data_solicitacao")
    )

    if busca:
        lista_autorizacoes = lista_autorizacoes.filter(
            Q(paciente__nome__icontains=busca)
            | Q(paciente__email__icontains=busca)
            | Q(procedimento__nome__icontains=busca)
            | Q(procedimento__descricao__icontains=busca)
            | Q(numero_autorizacao__icontains=busca)
            | Q(status__icontains=busca)
        )

    lista_autorizacoes = _aplicar_status_exibicao_autorizacoes(list(lista_autorizacoes))
    pacientes = filtrar_por_clinica(Paciente.objects.all(), request)
    procedimentos = filtrar_por_clinica(Procedimento.objects.all(), request)

    context = {
        "autorizacoes": lista_autorizacoes,
        "pacientes": pacientes,
        "procedimentos": procedimentos,
        "exclusao_bloqueada": request.GET.get("exclusao_bloqueada") == "1",
    }
    return render(request, "autorizacao_list.html", context)


@login_required
@modulo_requerido("enfermagem")
def NovaAutorizacaoView(request):
    if request.method == "POST":
        paciente_id = request.POST.get("paciente")
        procedimento_id = request.POST.get("procedimento")
        status = request.POST.get("status")
        observacoes = request.POST.get("observacoes")

        paciente = get_object_or_404(filtrar_por_clinica(Paciente.objects.all(), request), pk=paciente_id)
        procedimento = None
        if procedimento_id:
            procedimento = get_object_or_404(filtrar_por_clinica(Procedimento.objects.all(), request), pk=procedimento_id)

        nova_autorizacao = Autorizacao(
            clinica=get_clinica_atual(request),
            paciente=paciente,
            procedimento=procedimento,
            status=status,
            observacoes=observacoes,
            data_resposta=datetime.now(),
        )
        nova_autorizacao.save()

        return redirect("enfermagem:autorizacao_list")

    return redirect("enfermagem:autorizacao_list")


@login_required
@modulo_requerido("enfermagem")
def AutorizacaoDeleteView(request, pk):
    autorizacao = None
    if pk:
        autorizacao = get_object_or_404(filtrar_por_clinica(Autorizacao.objects.all(), request), pk=pk)

    if _get_agendamento_ativo(request, autorizacao):
        return redirect(f"{reverse('enfermagem:autorizacao_list')}?exclusao_bloqueada=1")

    autorizacao.delete()
    return redirect("enfermagem:autorizacao_list")


@login_required
@modulo_requerido("enfermagem")
def AutorizacaoUpdateView(request, pk):
    autorizacao = get_object_or_404(filtrar_por_clinica(Autorizacao.objects.all(), request), pk=pk)

    if request.method == "POST":
        status = request.POST.get("statusAtual")
        observacoes = request.POST.get("observacoesEdit")

        autorizacao.status = status
        autorizacao.observacoes = observacoes
        autorizacao.data_resposta = datetime.now()
        autorizacao.save()

        return redirect("enfermagem:autorizacao_list")

    return redirect("enfermagem:autorizacao_list")


@login_required
@modulo_requerido("enfermagem")
def AprovadosListView(request):
    busca = (request.GET.get("busca") or "").strip()
    agendamentos_prefetch = Prefetch(
        "agendaenfermagem_set",
        queryset=filtrar_por_clinica(
            AgendaEnfermagem.objects.exclude(status="CANCELADO").order_by("data_agendamento", "hora_agendamento"),
            request,
        ),
        to_attr="agendamentos_vinculados",
    )

    autorizacoes_aprovadas = (
        filtrar_por_clinica(Autorizacao.objects.filter(status="APROVADA"), request)
        .select_related("paciente", "procedimento")
        .prefetch_related(agendamentos_prefetch)
        .order_by("-data_resposta", "-data_solicitacao")
    )

    if busca:
        autorizacoes_aprovadas = autorizacoes_aprovadas.filter(
            Q(paciente__nome__icontains=busca)
            | Q(procedimento__nome__icontains=busca)
            | Q(procedimento__descricao__icontains=busca)
            | Q(numero_autorizacao__icontains=busca)
        )

    autorizacoes_aprovadas = _aplicar_status_exibicao_autorizacoes(list(autorizacoes_aprovadas))

    context = {
        "autorizacoes_aprovadas": autorizacoes_aprovadas,
        "agendamento_sucesso": request.GET.get("agendado") == "1",
    }
    return render(request, "aprovados.html", context)


@login_required
@modulo_requerido("enfermagem")
def ProcedimentoListView(request):
    busca = (request.GET.get("busca") or "").strip()
    procedimentos = filtrar_por_clinica(Procedimento.objects.all(), request).order_by("nome", "descricao")

    if busca:
        procedimentos = procedimentos.filter(
            Q(nome__icontains=busca)
            | Q(descricao__icontains=busca)
            | Q(id__icontains=busca)
        )

    context = {
        "procedimentos": procedimentos,
    }
    return render(request, "procedimentos.html", context)


@login_required
@modulo_requerido("enfermagem")
def ProcedimentoCreateView(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")

        novo_procedimento = Procedimento(
            clinica=get_clinica_atual(request),
            nome=nome,
            descricao=descricao,
        )
        novo_procedimento.save()

        return redirect("enfermagem:procedimento_list")

    return redirect("enfermagem:procedimento_list")


@login_required
@modulo_requerido("enfermagem")
def ProcedimentoUpdateView(request, pk):
    procedimento = get_object_or_404(filtrar_por_clinica(Procedimento.objects.all(), request), pk=pk)

    if request.method == "POST":
        nome = request.POST.get("nome")
        descricao = request.POST.get("descricao")
        procedimento.nome = nome
        procedimento.descricao = descricao
        procedimento.save()

        return redirect("enfermagem:procedimento_list")

    return redirect("enfermagem:procedimento_list")


@login_required
@modulo_requerido("enfermagem")
def ProcedimentoDeleteView(request, pk):
    procedimento = None
    if pk:
        procedimento = get_object_or_404(filtrar_por_clinica(Procedimento.objects.all(), request), pk=pk)
    procedimento.delete()
    return redirect("enfermagem:procedimento_list")


def gerar_horarios(data_agendamento):
    inicio = datetime.combine(data_agendamento, time(9, 0))
    fim = datetime.combine(data_agendamento, time(18, 0))
    horarios = []

    while inicio < fim:
        horarios.append(inicio.time())
        inicio += timedelta(hours=1)

    return horarios


def _parse_data_agendamento(data_texto):
    if not data_texto:
        return None

    try:
        return datetime.strptime(data_texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_hora_agendamento(hora_texto):
    if not hora_texto:
        return None

    try:
        return datetime.strptime(hora_texto, "%H:%M").time()
    except ValueError:
        return None


def _listar_horarios_disponiveis(request, data_agendamento):
    horarios_base = gerar_horarios(data_agendamento)
    horarios_ocupados = set(
        filtrar_por_clinica(AgendaEnfermagem.objects.filter(
            data_agendamento__date=data_agendamento,
            status="AGENDADO",
        ), request).values_list("hora_agendamento", flat=True)
    )
    return [horario for horario in horarios_base if horario not in horarios_ocupados]


def _montar_data_agendamento(data_agendamento):
    data_hora = datetime.combine(data_agendamento, time.min)
    if timezone.is_naive(data_hora):
        return timezone.make_aware(data_hora, timezone.get_current_timezone())
    return timezone.localtime(data_hora)


def _get_agendamento_ativo(request, autorizacao):
    return (
        filtrar_por_clinica(AgendaEnfermagem.objects.filter(
            autorizacao=autorizacao,
            status__in=["AGENDADO", "REALIZADO"],
        ), request)
        .order_by("data_agendamento", "hora_agendamento")
        .first()
    )


def _registrar_observacao_status(agendamento, acao, observacao):
    timestamp = timezone.localtime().strftime("%d/%m/%Y %H:%M")
    prefixo = f"[{timestamp}] {acao}: {observacao.strip()}"

    if agendamento.observacoes:
        return f"{agendamento.observacoes}\n{prefixo}"
    return prefixo


def _redirect_agendamento_status(agendamento, querystring):
    return redirect(f"{reverse('enfermagem:agendamento_create', args=[agendamento.autorizacao_id])}?{querystring}")


def _atualizar_status_agendamento(request, pk, novo_status, acao_label, sucesso_param, erro_param, observacao_param):
    agendamento = get_object_or_404(
        filtrar_por_clinica(AgendaEnfermagem.objects.select_related("autorizacao"), request),
        pk=pk,
    )

    if request.method != "POST":
        return redirect("enfermagem:agendamento_create", pk=agendamento.autorizacao_id)

    if agendamento.status != "AGENDADO":
        return _redirect_agendamento_status(agendamento, f"{erro_param}=1")

    observacao = (request.POST.get("observacao_status") or "").strip()
    if not observacao:
        return _redirect_agendamento_status(agendamento, f"{observacao_param}=1")

    agendamento.status = novo_status
    agendamento.observacoes = _registrar_observacao_status(agendamento, acao_label, observacao)
    agendamento.save(update_fields=["status", "observacoes"])

    return _redirect_agendamento_status(agendamento, f"{sucesso_param}=1")


@login_required
@modulo_requerido("enfermagem")
def horarios_disponiveis_view(request, pk):
    autorizacao = get_object_or_404(filtrar_por_clinica(Autorizacao.objects.all(), request), pk=pk)
    data_agendamento = _parse_data_agendamento(request.GET.get("data"))

    if autorizacao.status != "APROVADA" or not data_agendamento:
        return JsonResponse([], safe=False)

    horarios = _listar_horarios_disponiveis(request, data_agendamento)
    horarios_formatados = [horario.strftime("%H:%M") for horario in horarios]
    return JsonResponse(horarios_formatados, safe=False)


@login_required
@modulo_requerido("enfermagem")
def agendar(request, pk):
    autorizacao = get_object_or_404(
        filtrar_por_clinica(Autorizacao.objects.select_related("paciente", "procedimento"), request),
        pk=pk,
    )

    if autorizacao.status != "APROVADA":
        return redirect("enfermagem:aprovados_list")

    agendamento_existente = _get_agendamento_ativo(request, autorizacao)

    hoje = timezone.localdate()
    data_referencia = _parse_data_agendamento(request.GET.get("data")) or hoje
    if data_referencia < hoje:
        data_referencia = hoje

    erros = []
    horario_selecionado = ""

    if request.method == "POST":
        data_texto = request.POST.get("data_agendamento")
        horario_selecionado = request.POST.get("hora_agendamento") or ""
        observacoes = (request.POST.get("observacoes") or "").strip()

        data_referencia = _parse_data_agendamento(data_texto)
        hora_agendamento = _parse_hora_agendamento(horario_selecionado)

        if not data_referencia:
            erros.append("Informe uma data válida para o agendamento.")
        if not hora_agendamento:
            erros.append("Selecione um horário válido para o agendamento.")

        if not erros:
            try:
                AgendaEnfermagem.objects.create(
                    clinica=get_clinica_atual(request),
                    autorizacao=autorizacao,
                    data_agendamento=_montar_data_agendamento(data_referencia),
                    hora_agendamento=hora_agendamento,
                    observacoes=observacoes,
                )
                return redirect(f"{reverse('enfermagem:aprovados_list')}?agendado=1")
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for mensagens in exc.message_dict.values():
                        erros.extend(mensagens)
                else:
                    erros.extend(exc.messages)

        if not data_referencia:
            data_referencia = hoje

    horarios = _listar_horarios_disponiveis(request, data_referencia)

    context = {
        "autorizacao": autorizacao,
        "agendamento_existente": agendamento_existente,
        "data_minima": hoje.strftime("%Y-%m-%d"),
        "data_agendamento": data_referencia.strftime("%Y-%m-%d"),
        "horarios": [horario.strftime("%H:%M") for horario in horarios],
        "hora_agendamento": horario_selecionado,
        "erros_agendamento": erros,
        "cancelamento_sucesso": request.GET.get("cancelado") == "1",
        "cancelamento_erro": request.GET.get("cancelamento_erro") == "1",
        "cancelamento_sem_observacao": request.GET.get("cancelamento_sem_observacao") == "1",
        "realizacao_sucesso": request.GET.get("realizado") == "1",
        "realizacao_erro": request.GET.get("realizacao_erro") == "1",
        "realizacao_sem_observacao": request.GET.get("realizacao_sem_observacao") == "1",
        "horarios_disponiveis_url": reverse("enfermagem:horarios_disponiveis", args=[autorizacao.pk]),
    }
    return render(request, "agendar.html", context)


@login_required
@modulo_requerido("enfermagem")
def cancelar_agendamento(request, pk):
    return _atualizar_status_agendamento(
        request=request,
        pk=pk,
        novo_status="CANCELADO",
        acao_label="Cancelamento",
        sucesso_param="cancelado",
        erro_param="cancelamento_erro",
        observacao_param="cancelamento_sem_observacao",
    )


@login_required
@modulo_requerido("enfermagem")
def realizar_agendamento(request, pk):
    return _atualizar_status_agendamento(
        request=request,
        pk=pk,
        novo_status="REALIZADO",
        acao_label="Realização",
        sucesso_param="realizado",
        erro_param="realizacao_erro",
        observacao_param="realizacao_sem_observacao",
    )
