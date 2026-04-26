from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from base.models import Convenio, Especialidade, StatusAgendamento, TipoConsulta
from base.statuses import (
    get_status_agendamento_em_andamento,
    get_status_agendamento_finalizado,
    get_status_agendamento_padrao,
)
from base.tenancy import ClinicaModuloRequiredMixin, filtrar_por_clinica, get_actor_name, modulo_requerido
from medico.models import Medico, MedicoAgenda, MedicoEspecialidade
from paciente.models import Paciente

from .models import Agenda
from .services import sync_agenda_status


def _get_data_agenda(request):
    data_param = request.GET.get('data_agenda') or request.POST.get('data_agenda')
    if not data_param:
        return date.today()

    try:
        return datetime.strptime(data_param, '%Y-%m-%d').date()
    except ValueError:
        return date.today()


def _status_button_classes(consulta):
    if consulta.status == Agenda.Status.BLOQUEADO:
        return 'btn-neutral liberar'
    if consulta.status == Agenda.Status.AGENDADO:
        return 'btn-primary cancelar_consulta'
    return 'btn-primary agendar'


def _status_label_classes(status_obj):
    if not status_obj:
        return 'btn-ghost'

    cor = (status_obj.cor or '').strip()
    return cor or 'btn-ghost'


def _normalize_status_text(value):
    return (value or '').strip().lower()


def _is_status_in(consulta, termos):
    descricao = _normalize_status_text(consulta.status_agendamento.descricao if consulta.status_agendamento_id else '')
    return any(termo in descricao for termo in termos)


def _build_workflow_links(request, consulta):
    if not consulta.paciente_id:
        return {'prontuario_url': '', 'financeiro_url': ''}

    next_url = request.get_full_path()
    prontuario_query = urlencode(
        {
            'tab': 'prontuario',
            'agenda_id': consulta.pk,
            'next': next_url,
        }
    )
    financeiro_query = urlencode(
        {
            'paciente': consulta.paciente_id,
            'convenio': consulta.convenio_id or '',
            'origem': 'CONSULTA',
            'tipo': 'RECEITA',
            'descricao': f"Consulta - {consulta.paciente.nome}",
            'data_lancamento': consulta.data.isoformat(),
            'competencia': consulta.data.isoformat(),
            'data_vencimento': consulta.data.isoformat(),
            'next': next_url,
        }
    )
    return {
        'prontuario_url': f"{reverse('paciente:paciente_update', args=[consulta.paciente_id])}?{prontuario_query}",
        'financeiro_url': f"{reverse('financeiro:lancamento_create')}?{financeiro_query}",
    }


def _build_workflow_state(request, consulta):
    status_em_andamento = get_status_agendamento_em_andamento(request)
    status_finalizado = get_status_agendamento_finalizado(request)
    descricao_status = _normalize_status_text(consulta.status_agendamento.descricao if consulta.status_agendamento_id else '')
    em_andamento = bool(status_em_andamento and consulta.status_agendamento_id == status_em_andamento.pk) or 'andamento' in descricao_status or 'atendimento' in descricao_status
    finalizado = bool(status_finalizado and consulta.status_agendamento_id == status_finalizado.pk) or 'finaliz' in descricao_status or 'conclu' in descricao_status
    encerrado = finalizado or 'cancel' in descricao_status or 'falt' in descricao_status
    return {
        'pode_iniciar': consulta.status == Agenda.Status.AGENDADO and consulta.paciente_id and not em_andamento and not encerrado,
        'pode_finalizar': consulta.status == Agenda.Status.AGENDADO and consulta.paciente_id and not finalizado and ('andamento' in descricao_status or 'atendimento' in descricao_status or em_andamento),
        'atendimento_ativo': em_andamento and not finalizado,
        'atendimento_finalizado': finalizado,
    }


def _redirect_back(request, fallback_name='agenda:agenda_consultas'):
    destino = request.POST.get('next') or request.GET.get('next')
    return redirect(destino or reverse(fallback_name))


def _atualizar_fluxo_atendimento(request, pk, status_destino, mensagem_sucesso):
    agenda = get_object_or_404(
        filtrar_por_clinica(Agenda.objects.select_related('paciente', 'status_agendamento'), request),
        pk=pk,
    )

    if agenda.status != Agenda.Status.AGENDADO or not agenda.paciente_id:
        messages.error(request, 'Somente consultas agendadas com paciente podem seguir no fluxo de atendimento.')
        return _redirect_back(request)

    if not status_destino:
        messages.error(request, 'Não foi possível localizar o status necessário para o fluxo de atendimento.')
        return _redirect_back(request)

    agenda.status_agendamento = status_destino
    agenda.usalt = get_actor_name(request)
    agenda.save(update_fields=['status_agendamento', 'usalt', 'dtalt'])
    messages.success(request, mensagem_sucesso)
    return _redirect_back(request)


class AgendaConsultasView(ClinicaModuloRequiredMixin, TemplateView):
    template_name = 'agenda/consultas.html'
    modulo_requerido = 'agenda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data_agenda = _get_data_agenda(self.request)
        ontem = data_agenda - timedelta(days=1)
        amanha = data_agenda + timedelta(days=1)

        medico_id = self.request.GET.get('cod_medico', '0')

        medicos = filtrar_por_clinica(Medico.objects.filter(status=True), self.request)
        medicos = medicos.order_by('nome')

        medico_selecionado = None
        if medico_id and medico_id.isdigit() and int(medico_id) > 0:
            medico_selecionado = medicos.filter(pk=int(medico_id)).first()

        agenda_qs = Agenda.objects.none()
        possui_config_agenda = False
        mostrar_btn_abrir_agenda = False
        mensagem_tabela = 'SELECIONE UM MÉDICO PARA VISUALIZAR A AGENDA'

        if medico_selecionado:
            possui_config_agenda = filtrar_por_clinica(MedicoAgenda.objects.filter(
                medico=medico_selecionado,
                status=True,
            ), self.request).exists()
            agenda_qs = (
                filtrar_por_clinica(Agenda.objects.filter(
                    medico=medico_selecionado,
                    data=data_agenda,
                ), self.request)
                .select_related(
                    'paciente',
                    'convenio',
                    'tipo_consulta',
                    'especialidade',
                    'status_agendamento',
                )
                .order_by('hora')
            )

            if agenda_qs.exists():
                mensagem_tabela = ''
            elif not possui_config_agenda:
                mensagem_tabela = 'O(A) MÉDICO(A) NÃO POSSUI HORÁRIOS CONFIGURADOS'
            else:
                mensagem_tabela = 'NÃO FOI ABERTA AGENDA PARA ESTA DATA'
                mostrar_btn_abrir_agenda = True

        agenda_qs = list(agenda_qs)
        actor_name = get_actor_name(self.request) if self.request.user.is_authenticated else None
        agenda_consultas = []
        status_em_andamento = get_status_agendamento_em_andamento(self.request)
        status_finalizado = get_status_agendamento_finalizado(self.request)
        for index, consulta in enumerate(agenda_qs):
            next_hora = agenda_qs[index + 1].hora if index + 1 < len(agenda_qs) else None
            sync_agenda_status(consulta, self.request, next_hora=next_hora, actor_name=actor_name)
            workflow_links = _build_workflow_links(self.request, consulta)
            workflow_state = _build_workflow_state(self.request, consulta)
            agenda_consultas.append(
                {
                    'id': consulta.id,
                    'hora': consulta.hora,
                    'status': consulta.status,
                    'cod_paciente': consulta.paciente_id,
                    'paciente_nome': consulta.paciente.nome if consulta.paciente else '',
                    'convenio_nome': consulta.convenio.nome if consulta.convenio else '',
                    'tipo_consulta': consulta.tipo_consulta.descricao if consulta.tipo_consulta else '',
                    'especialidade': consulta.especialidade.descricao if consulta.especialidade else '',
                    'cod_status_agendamento': consulta.status_agendamento_id or '',
                    'status_agendamento': consulta.status_agendamento.descricao if consulta.status_agendamento else '',
                    'hora_button_classes': _status_button_classes(consulta),
                    'status_button_classes': _status_label_classes(consulta.status_agendamento),
                    'prontuario_url': workflow_links['prontuario_url'],
                    'financeiro_url': workflow_links['financeiro_url'],
                    'pode_iniciar': workflow_state['pode_iniciar'],
                    'pode_finalizar': workflow_state['pode_finalizar'],
                    'atendimento_ativo': workflow_state['atendimento_ativo'],
                    'atendimento_finalizado': workflow_state['atendimento_finalizado'],
                }
            )

        context.update(
            {
                'data_agenda': data_agenda.strftime('%Y-%m-%d'),
                'data_agenda_br': data_agenda.strftime('%d/%m/%Y'),
                'ontem': ontem.strftime('%Y-%m-%d'),
                'amanha': amanha.strftime('%Y-%m-%d'),
                'cod_medico': str(medico_selecionado.pk) if medico_selecionado else '0',
                'medico_selecionado': medico_selecionado,
                'medicos': medicos,
                'agenda_consultas': agenda_consultas,
                'mensagem_tabela': mensagem_tabela,
                'mostrar_btn_abrir_agenda': mostrar_btn_abrir_agenda,
                'tipos_consulta': filtrar_por_clinica(
                    TipoConsulta.objects.filter(status=True).order_by('descricao'),
                    self.request,
                ),
                'convenios': filtrar_por_clinica(
                    Convenio.objects.filter(status=True).order_by('nome'),
                    self.request,
                ),
                'status_agendamento_nivel_1': filtrar_por_clinica(StatusAgendamento.objects.filter(
                    status=True,
                    nivel=1,
                ).order_by('descricao'), self.request),
                'status_agendamento_modal': filtrar_por_clinica(StatusAgendamento.objects.filter(
                    status=True,
                    nivel__lte=2,
                ).order_by('nivel', 'descricao'), self.request),
                'status_em_atendimento_id': status_em_andamento.pk if status_em_andamento else '',
                'status_finalizado_id': status_finalizado.pk if status_finalizado else '',
                'pacientes': filtrar_por_clinica(Paciente.objects.filter(status=True), self.request)
                .select_related('convenio')
                .order_by('nome')[:200],
            }
        )
        return context


@login_required
@require_GET
@modulo_requerido('agenda')
def medico_especialidades_api(request, medico_id):
    especialidades = filtrar_por_clinica(MedicoEspecialidade.objects.filter(
        medico_id=medico_id,
        status=True,
    ), request).select_related('especialidade').order_by('especialidade__descricao')

    return JsonResponse(
        {
            'success': True,
            'especialidades': [
                {
                    'id': item.especialidade_id,
                    'descricao': item.especialidade.descricao,
                }
                for item in especialidades
            ],
        }
    )


@login_required
@require_POST
@transaction.atomic
@modulo_requerido('agenda')
def agenda_api(request):
    action = request.POST.get('funcao')

    try:
        if action == 'criar_agenda':
            return _criar_agenda(request)
        if action == 'addhora':
            return _adicionar_horario(request)
        if action == 'salvar_consulta':
            return _salvar_consulta(request)
        if action == 'cancelar_consulta':
            return _cancelar_consulta(request)
        if action == 'bloquear_horario':
            return _bloquear_horario(request)
        if action == 'liberar_horario':
            return _liberar_horario(request)
        if action == 'novo_status':
            return _novo_status(request)

        return JsonResponse({'success': False, 'message': 'Ação inválida.'}, status=400)
    except OperationalError as exc:
        if 'database is locked' in str(exc).lower():
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Banco ocupado no momento. Tente novamente em alguns segundos.',
                },
                status=503,
            )
        raise


def _get_agenda_or_error(request):
    cod_agenda = request.POST.get('cod_agenda')
    if not cod_agenda:
        return None, JsonResponse({'success': False, 'message': 'Código da agenda não informado.'}, status=400)

    agenda = filtrar_por_clinica(Agenda.objects.filter(pk=cod_agenda), request).first()
    if not agenda:
        return None, JsonResponse({'success': False, 'message': 'Horário da agenda não encontrado.'}, status=404)

    return agenda, None


def _criar_agenda(request):
    data_agenda = _get_data_agenda(request)
    medico_id = request.POST.get('cod_medico')
    medico = get_object_or_404(filtrar_por_clinica(Medico.objects.filter(status=True), request), pk=medico_id)

    horarios_base = filtrar_por_clinica(MedicoAgenda.objects.filter(
        medico=medico,
        status=True,
    ), request).order_by('hora')

    if not horarios_base.exists():
        return JsonResponse({'success': False, 'message': 'O médico não possui horários configurados.'}, status=400)

    horarios_existentes = set(
        filtrar_por_clinica(Agenda.objects.filter(
            medico=medico,
            data=data_agenda,
        ), request).values_list('hora', flat=True)
    )

    novos_registros = []
    for horario in horarios_base:
        if horario.hora in horarios_existentes:
            continue
        novos_registros.append(
            Agenda(
                clinica=medico.clinica,
                data=data_agenda,
                hora=horario.hora,
                medico=medico,
                status=Agenda.Status.DISPONIVEL,
                uscad=get_actor_name(request),
            )
        )

    if not novos_registros:
        return JsonResponse({'success': False, 'message': 'A agenda desta data já está aberta.'}, status=400)

    Agenda.objects.bulk_create(novos_registros)
    return JsonResponse({'success': True, 'message': f'{len(novos_registros)} horários criados com sucesso.'})


def _adicionar_horario(request):
    data_agenda = _get_data_agenda(request)
    medico_id = request.POST.get('cod_medico')
    hora_agenda = request.POST.get('hora_agenda')

    if not medico_id or not hora_agenda:
        return JsonResponse({'success': False, 'message': 'Médico e horário são obrigatórios.'}, status=400)

    medico = get_object_or_404(filtrar_por_clinica(Medico.objects.filter(status=True), request), pk=medico_id)
    try:
        hora = datetime.strptime(hora_agenda, '%H:%M').time()
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Horário inválido.'}, status=400)

    agenda, created = Agenda.objects.get_or_create(
        clinica=medico.clinica,
        data=data_agenda,
        hora=hora,
        medico=medico,
        defaults={
            'status': Agenda.Status.DISPONIVEL,
            'uscad': get_actor_name(request),
        },
    )

    if not created:
        return JsonResponse({'success': False, 'message': 'Este horário já existe na agenda.'}, status=400)

    return JsonResponse({'success': True, 'message': 'Horário adicionado com sucesso.', 'agenda_id': agenda.id})


def _salvar_consulta(request):
    agenda, error = _get_agenda_or_error(request)
    if error:
        return error

    paciente = get_object_or_404(
        filtrar_por_clinica(Paciente.objects.filter(status=True), request),
        pk=request.POST.get('cod_paciente'),
    )
    status_agendamento_id = request.POST.get('cod_status_agendamento') or None
    status_agendamento = None
    if status_agendamento_id:
        status_agendamento = filtrar_por_clinica(
            StatusAgendamento.objects.filter(pk=status_agendamento_id, status=True),
            request,
        ).first()
    if not status_agendamento:
        status_agendamento = _get_status_agendamento_padrao(request)

    agenda.paciente = paciente
    agenda.convenio_id = request.POST.get('convenio_consulta') or paciente.convenio_id
    agenda.tipo_consulta_id = request.POST.get('cod_tipo_consulta') or None
    agenda.especialidade_id = request.POST.get('cod_especialidade') or None
    agenda.status_agendamento = status_agendamento
    agenda.status = Agenda.Status.AGENDADO
    agenda.usalt = get_actor_name(request)
    agenda.save()
    sync_agenda_status(agenda, request, actor_name=get_actor_name(request))

    return JsonResponse({'success': True, 'message': 'Consulta salva com sucesso.'})


def _cancelar_consulta(request):
    agenda, error = _get_agenda_or_error(request)
    if error:
        return error

    agenda.paciente = None
    agenda.convenio = None
    agenda.tipo_consulta = None
    agenda.especialidade = None
    agenda.status_agendamento = None
    agenda.status = Agenda.Status.DISPONIVEL
    agenda.usalt = get_actor_name(request)
    agenda.save()

    return JsonResponse({'success': True, 'message': 'Consulta cancelada com sucesso.'})


def _bloquear_horario(request):
    agenda, error = _get_agenda_or_error(request)
    if error:
        return error

    agenda.paciente = None
    agenda.convenio = None
    agenda.tipo_consulta = None
    agenda.especialidade = None
    agenda.status_agendamento = None
    agenda.status = Agenda.Status.BLOQUEADO
    agenda.usalt = get_actor_name(request)
    agenda.save()

    return JsonResponse({'success': True, 'message': 'Horário bloqueado com sucesso.'})


def _liberar_horario(request):
    agenda, error = _get_agenda_or_error(request)
    if error:
        return error

    agenda.paciente = None
    agenda.convenio = None
    agenda.tipo_consulta = None
    agenda.especialidade = None
    agenda.status_agendamento = None
    agenda.status = Agenda.Status.DISPONIVEL
    agenda.usalt = get_actor_name(request)
    agenda.save()

    return JsonResponse({'success': True, 'message': 'Horário liberado com sucesso.'})


def _novo_status(request):
    agenda, error = _get_agenda_or_error(request)
    if error:
        return error

    cod_novo_status = request.POST.get('cod_novo_status')
    status_agendamento = get_object_or_404(
        filtrar_por_clinica(StatusAgendamento.objects.filter(status=True), request),
        pk=cod_novo_status,
    )
    agenda.status_agendamento = status_agendamento
    agenda.usalt = get_actor_name(request)
    agenda.save(update_fields=['status_agendamento', 'usalt', 'dtalt'])

    return JsonResponse({'success': True, 'message': 'Status atualizado com sucesso.'})


@login_required
@require_POST
@modulo_requerido('agenda')
def iniciar_atendimento(request, pk):
    return _atualizar_fluxo_atendimento(
        request,
        pk,
        get_status_agendamento_em_andamento(request),
        'Atendimento iniciado com sucesso.',
    )


@login_required
@require_POST
@modulo_requerido('agenda')
def finalizar_atendimento(request, pk):
    return _atualizar_fluxo_atendimento(
        request,
        pk,
        get_status_agendamento_finalizado(request),
        'Atendimento finalizado com sucesso.',
    )
