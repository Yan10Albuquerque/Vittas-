import uuid
from datetime import date
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.db import OperationalError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from base.tenancy import ClinicaModuloRequiredMixin, filtrar_por_clinica, get_actor_name, get_clinica_atual, modulo_requerido, set_clinica
from base.services import CepLookupError, consultar_cep
from agenda.services import sync_agenda_status
from .forms import PacienteForm
from .models import Paciente

from enfermagem.models import AgendaEnfermagem, Autorizacao


TIMELINE_STYLES = {
    'Consulta': {
        'badge_class': 'badge-info badge-outline',
        'status_class': 'badge-info',
        'icon': 'fa-solid fa-stethoscope',
    },
    'Autorizacao': {
        'badge_class': 'badge-warning badge-outline',
        'status_class': 'badge-warning',
        'icon': 'fa-solid fa-file-circle-check',
    },
    'Procedimento': {
        'badge_class': 'badge-secondary badge-outline',
        'status_class': 'badge-secondary',
        'icon': 'fa-solid fa-hand-holding-medical',
    },
    'Vacina': {
        'badge_class': 'badge-success badge-outline',
        'status_class': 'badge-success',
        'icon': 'fa-solid fa-syringe',
    },
    'Financeiro': {
        'badge_class': 'badge-accent badge-outline',
        'status_class': 'badge-accent',
        'icon': 'fa-solid fa-wallet',
    },
    'Prontuario': {
        'badge_class': 'badge-primary badge-outline',
        'status_class': 'badge-primary',
        'icon': 'fa-solid fa-notes-medical',
    },
    'Cadastro': {
        'badge_class': 'badge-neutral badge-outline',
        'status_class': 'badge-neutral',
        'icon': 'fa-solid fa-id-card-clip',
    },
}


def _as_local_datetime(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value)


def _build_timeline_event(tipo, titulo, instante, descricao=None, *, detalhes=None, status=None, valor=None):
    style = TIMELINE_STYLES.get(tipo, TIMELINE_STYLES['Cadastro'])
    return {
        'tipo': tipo,
        'titulo': titulo,
        'instante': instante,
        'descricao': descricao or '',
        'detalhes': [detalhe for detalhe in (detalhes or []) if detalhe],
        'status': status or '',
        'valor': valor,
        'badge_class': style['badge_class'],
        'status_class': style['status_class'],
        'icon': style['icon'],
    }


def _build_prontuario_history_events(paciente):
    eventos = []
    historicos = list(paciente.history.order_by('history_date', 'history_id'))
    historico_anterior = None

    for historico in historicos:
        instante = _as_local_datetime(historico.history_date)
        responsavel = historico.history_user or historico.history_change_reason or 'Sistema'
        prontuario_atual = (historico.prontuario or '').strip()
        prontuario_anterior = (getattr(historico_anterior, 'prontuario', '') or '').strip() if historico_anterior else ''

        if historico.history_type == '+':
            eventos.append(
                _build_timeline_event(
                    'Cadastro',
                    'Cadastro do paciente',
                    instante,
                    detalhes=[f'Responsável: {responsavel}'],
                )
            )
        elif historico.history_type == '-':
            eventos.append(
                _build_timeline_event(
                    'Cadastro',
                    'Registro do paciente removido',
                    instante,
                    detalhes=[f'Responsável: {responsavel}'],
                    status='Removido',
                )
            )
        else:
            if prontuario_atual != prontuario_anterior:
                descricao = prontuario_atual or 'Prontuário clínico limpo.'
                eventos.append(
                    _build_timeline_event(
                        'Prontuario',
                        'Evolução do prontuário atualizada',
                        instante,
                        descricao=descricao,
                        detalhes=[f'Responsável: {responsavel}'],
                    )
                )
            else:
                eventos.append(
                    _build_timeline_event(
                        'Cadastro',
                        'Dados cadastrais atualizados',
                        instante,
                        detalhes=[f'Responsável: {responsavel}'],
                    )
                )

        historico_anterior = historico

    return eventos


def _build_prontuario_summary(paciente, eventos, autorizacoes, agendamentos_enfermagem):
    contador = Counter(evento['tipo'] for evento in eventos)
    financeiro_em_aberto = sum(
        lancamento.valor_em_aberto
        for lancamento in paciente.lancamentos_financeiros.exclude(
            status__in=['PAGO', 'CANCELADO']
        )
    )
    autorizacoes_pendentes = sum(1 for autorizacao in autorizacoes if autorizacao.status == 'PENDENTE')
    procedimentos_ativos = sum(1 for agendamento in agendamentos_enfermagem if agendamento.status == 'AGENDADO')
    ultima_consulta = next((evento for evento in eventos if evento['tipo'] == 'Consulta'), None)
    ultimo_evento = eventos[0] if eventos else None

    return {
        'cards': [
            {'label': 'Eventos clínicos', 'valor': len(eventos), 'classe': 'text-primary'},
            {'label': 'Consultas registradas', 'valor': contador.get('Consulta', 0), 'classe': 'text-info'},
            {'label': 'Procedimentos ativos', 'valor': procedimentos_ativos, 'classe': 'text-secondary'},
            {'label': 'Autorizações pendentes', 'valor': autorizacoes_pendentes, 'classe': 'text-warning'},
        ],
        'financeiro_em_aberto': financeiro_em_aberto,
        'ultima_consulta': ultima_consulta,
        'ultimo_evento': ultimo_evento,
        'tem_prontuario': bool((paciente.prontuario or '').strip()),
        'autorizacoes_pendentes': autorizacoes_pendentes,
    }


def _build_prontuario_timeline(paciente):
    eventos = []

    for agendamento in paciente.agendamentos.select_related(
        'medico',
        'tipo_consulta',
        'especialidade',
        'status_agendamento',
        'convenio',
    ):
        instante = _as_local_datetime(timezone.datetime.combine(agendamento.data, agendamento.hora))
        eventos.append(
            _build_timeline_event(
                'Consulta',
                agendamento.tipo_consulta.descricao if agendamento.tipo_consulta_id else 'Atendimento agendado',
                instante,
                descricao='Consulta registrada na agenda clínica.',
                detalhes=[
                    f"Médico: {agendamento.medico.nome}" if agendamento.medico_id else None,
                    f"Especialidade: {agendamento.especialidade.descricao}" if agendamento.especialidade_id else None,
                    f"Convênio: {agendamento.convenio.nome}" if agendamento.convenio_id else None,
                ],
                status=agendamento.status_agendamento.descricao if agendamento.status_agendamento_id else agendamento.get_status_display(),
            )
        )

    autorizacoes = list(
        Autorizacao.objects.filter(paciente=paciente).select_related('procedimento').order_by('-data_solicitacao', '-pk')
    )
    for autorizacao in autorizacoes:
        instante = _as_local_datetime(autorizacao.data_resposta or autorizacao.data_solicitacao)
        eventos.append(
            _build_timeline_event(
                'Autorizacao',
                autorizacao.procedimento.nome if autorizacao.procedimento_id else 'Autorização clínica',
                instante,
                descricao=autorizacao.observacoes or 'Solicitação/autorização registrada para o paciente.',
                detalhes=[
                    f"Procedimento: {autorizacao.procedimento.descricao}" if autorizacao.procedimento_id else None,
                ],
                status=autorizacao.get_status_display(),
            )
        )

    agendamentos_enfermagem = list(
        AgendaEnfermagem.objects.filter(autorizacao__paciente=paciente)
        .select_related('autorizacao__procedimento')
        .order_by('-data_agendamento', '-hora_agendamento', '-pk')
    )
    for agendamento in agendamentos_enfermagem:
        eventos.append(
            _build_timeline_event(
                'Procedimento',
                agendamento.autorizacao.procedimento.nome if agendamento.autorizacao_id and agendamento.autorizacao.procedimento_id else 'Procedimento agendado',
                _as_local_datetime(agendamento.data_hora_agendada or agendamento.data_agendamento),
                descricao=agendamento.observacoes or 'Agendamento da enfermagem vinculado ao paciente.',
                detalhes=[
                    f"Procedimento: {agendamento.autorizacao.procedimento.descricao}" if agendamento.autorizacao_id and agendamento.autorizacao.procedimento_id else None,
                ],
                status=agendamento.get_status_display(),
            )
        )

    for vacina in paciente.vacinas.select_related('aplicador', 'forma_pagamento'):
        instante_base = timezone.datetime.combine(vacina.data_aplicacao, timezone.datetime.min.time()) if vacina.data_aplicacao else vacina.dtcad
        eventos.append(
            _build_timeline_event(
                'Vacina',
                vacina.descricao_vacina or 'Vacina registrada',
                _as_local_datetime(instante_base),
                descricao=vacina.obs or 'Aplicação registrada no histórico do paciente.',
                detalhes=[
                    f"Aplicador: {vacina.aplicador}" if vacina.aplicador_id else None,
                    f"Pagamento: {vacina.forma_pagamento}" if vacina.forma_pagamento_id else None,
                ],
            )
        )

    for lancamento in paciente.lancamentos_financeiros.select_related('categoria', 'forma_pagamento'):
        instante_base = timezone.datetime.combine(lancamento.data_lancamento, timezone.datetime.min.time())
        eventos.append(
            _build_timeline_event(
                'Financeiro',
                lancamento.descricao,
                _as_local_datetime(instante_base),
                descricao=lancamento.observacoes or 'Lançamento financeiro associado ao paciente.',
                detalhes=[
                    f"Categoria: {lancamento.categoria.descricao}" if lancamento.categoria_id else None,
                    f"Origem: {lancamento.get_origem_display()}",
                    f"Forma de pagamento: {lancamento.forma_pagamento}" if lancamento.forma_pagamento_id else None,
                ],
                status=lancamento.get_status_display(),
                valor=lancamento.valor,
            )
        )

    eventos.extend(_build_prontuario_history_events(paciente))

    eventos.sort(key=lambda evento: evento['instante'] or timezone.now(), reverse=True)
    return eventos, _build_prontuario_summary(paciente, eventos, autorizacoes, agendamentos_enfermagem)


class PacienteListView(ClinicaModuloRequiredMixin, ListView):
    model = Paciente
    template_name = 'pacientes/list.html'
    context_object_name = 'pacientes'
    paginate_by = 10
    modulo_requerido = 'pacientes'

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca)
                | Q(cpf__icontains=busca)
                | Q(carteira_conv__icontains=busca)
            )
        return queryset.order_by('nome')


class PacienteCreateView(ClinicaModuloRequiredMixin, CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'pacientes/form.html'
    success_url = reverse_lazy('paciente:paciente_list')
    modulo_requerido = 'pacientes'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        set_clinica(form.instance, self.request)
        form.instance.uscad = get_actor_name(self.request)
        return super().form_valid(form)


class PacienteUpdateView(ClinicaModuloRequiredMixin, UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'pacientes/form.html'
    success_url = reverse_lazy('paciente:paciente_list')
    modulo_requerido = 'pacientes'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = kwargs.get('active_tab', self.request.GET.get('tab', 'cadastro'))
        timeline_eventos, prontuario_resumo = _build_prontuario_timeline(self.object)
        context['timeline_eventos'] = timeline_eventos
        context['prontuario_resumo'] = prontuario_resumo
        context['next_url'] = self.request.POST.get('next') or self.request.GET.get('next') or ''
        context['agenda_id'] = self.request.POST.get('agenda_id') or self.request.GET.get('agenda_id') or ''
        return context

    def get_success_url(self):
        return self.request.POST.get('next') or self.request.GET.get('next') or self.success_url

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'salvar_prontuario' in request.POST:
            agenda_id = request.POST.get('agenda_id') or request.GET.get('agenda_id')
            self.object.prontuario = (request.POST.get('prontuario') or '').strip()
            self.object.usalt = get_actor_name(request)
            self.object.save(update_fields=['prontuario', 'usalt', 'dtalt'])
            if agenda_id:
                from agenda.models import Agenda

                agenda = filtrar_por_clinica(Agenda.objects.filter(pk=agenda_id), request).first()
                if agenda:
                    sync_agenda_status(agenda, request, actor_name=get_actor_name(request))
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(f"{request.path}?tab=prontuario")

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        agenda_id = self.request.POST.get('agenda_id') or self.request.GET.get('agenda_id')
        form.instance.usalt = get_actor_name(self.request)
        response = super().form_valid(form)
        if agenda_id:
            from agenda.models import Agenda

            agenda = filtrar_por_clinica(Agenda.objects.filter(pk=agenda_id), self.request).first()
            if agenda:
                sync_agenda_status(agenda, self.request, actor_name=get_actor_name(self.request))
        return response


class PacienteDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = Paciente
    success_url = reverse_lazy('paciente:paciente_list')
    modulo_requerido = 'pacientes'

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Paciente excluído com sucesso!'})


@require_POST
@login_required
@modulo_requerido('pacientes')
def paciente_api(request):
    funcao = request.POST.get('funcao', '').strip()
    try:
        if funcao == 'buscar_dados':
            return _paciente_buscar_dados(request)
        elif funcao == 'cadbasico':
            return _paciente_cadbasico(request)
        elif funcao == 'atualiza_paciente':
            return _paciente_atualiza(request)
        else:
            return JsonResponse({'success': False, 'message': 'Função inválida.'}, status=400)
    except OperationalError as exc:
        if 'database is locked' in str(exc).lower():
            return JsonResponse(
                {'success': False, 'message': 'Sistema temporariamente ocupado. Tente novamente em instantes.'},
                status=503,
            )
        raise


def _paciente_buscar_dados(request):
    cod_paciente = request.POST.get('cod_paciente', '').strip()
    if not cod_paciente:
        return JsonResponse({'success': False, 'message': 'Código do paciente não informado.'}, status=400)

    paciente = filtrar_por_clinica(Paciente.objects.filter(pk=cod_paciente).select_related('convenio'), request).first()
    if not paciente:
        return JsonResponse({'success': False, 'message': 'Paciente não encontrado.'}, status=404)

    return JsonResponse(
        {
            'success': True,
            'paciente': {
                'id': paciente.id,
                'cpf': paciente.cpf,
                'nome': paciente.nome,
                'celular': paciente.celular,
                'telefone': paciente.telefone or '',
                'email': paciente.email or '',
                'documento': paciente.documento or '',
                'nascimento': paciente.nascimento.isoformat() if paciente.nascimento else '',
                'peso': str(paciente.peso or ''),
                'altura': str(paciente.altura or ''),
                'sexo': paciente.sexo or '',
                'profissao': paciente.profissao or '',
                'cep': paciente.cep or '',
                'endereco': paciente.logradouro or '',
                'numero': paciente.numero or '',
                'complemento': paciente.complemento or '',
                'bairro': paciente.bairro or '',
                'cidade': paciente.cidade or '',
                'estado': paciente.estado or '',
                'mae': paciente.mae or '',
                'pai': paciente.pai or '',
                'convenio': paciente.convenio_id or '',
                'num_carteira': paciente.carteira_conv or '',
                'carteira_sus': paciente.carteira_sus or '',
                'obs': paciente.obs or '',
                'prontuario': paciente.prontuario or '',
            },
        }
    )


def _paciente_cadbasico(request):
    nome = (request.POST.get('nome') or '').strip()
    celular = (request.POST.get('celular') or '').strip()
    cpf = (request.POST.get('cpf') or '').strip()

    if not nome:
        return JsonResponse({'success': False, 'message': 'Nome é obrigatório.'}, status=400)
    if not celular:
        return JsonResponse({'success': False, 'message': 'Celular é obrigatório.'}, status=400)

    convenio_id = request.POST.get('convenio') or None
    nascimento_str = request.POST.get('nascimento') or '1900-01-01'
    try:
        nascimento = date.fromisoformat(nascimento_str)
    except ValueError:
        nascimento = date(1900, 1, 1)

    defaults = {
        'nome': nome,
        'celular': celular,
        'nascimento': nascimento,
        'convenio_id': convenio_id,
        'clinica': get_clinica_atual(request),
        'uscad': get_actor_name(request),
    }

    with transaction.atomic():
        if cpf:
            paciente, created = Paciente.objects.get_or_create(
                clinica=get_clinica_atual(request),
                cpf=cpf,
                defaults=defaults,
            )
            if not created:
                paciente.nome = nome
                paciente.celular = celular
                paciente.convenio_id = convenio_id
                paciente.usalt = get_actor_name(request)
                paciente.save()
        else:
            defaults['cpf'] = f"SEM-{uuid.uuid4().hex[:10].upper()}"
            paciente = Paciente.objects.create(**defaults)

    return JsonResponse({'success': True, 'paciente_id': paciente.id, 'message': 'Paciente cadastrado.'})


def _paciente_atualiza(request):
    from agenda.models import Agenda

    cod_paciente = (request.POST.get('cod_paciente') or '').strip()
    if not cod_paciente:
        return JsonResponse({'success': False, 'message': 'Código do paciente não informado.'}, status=400)

    paciente = filtrar_por_clinica(Paciente.objects.filter(pk=cod_paciente), request).first()
    if not paciente:
        return JsonResponse({'success': False, 'message': 'Paciente não encontrado.'}, status=404)

    cpf = (request.POST.get('cpf') or '').strip()
    if not cpf:
        return JsonResponse({'success': False, 'message': 'CPF é obrigatório.'}, status=400)

    if filtrar_por_clinica(Paciente.objects.filter(cpf=cpf), request).exclude(pk=paciente.pk).exists():
        return JsonResponse({'success': False, 'message': 'Já existe outro paciente com este CPF.'}, status=400)

    paciente.cpf = cpf
    paciente.nome = (request.POST.get('nome') or '').strip()
    paciente.celular = (request.POST.get('celular') or '').strip()
    paciente.telefone = (request.POST.get('telefone') or '').strip() or None
    paciente.email = (request.POST.get('email') or '').strip() or None
    paciente.documento = (request.POST.get('documento') or '').strip() or None
    paciente.nascimento = request.POST.get('nascimento') or paciente.nascimento
    paciente.peso = request.POST.get('peso') or None
    paciente.altura = request.POST.get('altura') or None
    paciente.sexo = (request.POST.get('sexo') or '').strip() or None
    paciente.profissao = (request.POST.get('profissao') or '').strip() or None
    paciente.cep = (request.POST.get('cep') or '').strip() or None
    paciente.logradouro = (request.POST.get('endereco') or '').strip() or None
    paciente.numero = (request.POST.get('numero') or '').strip() or None
    paciente.complemento = (request.POST.get('complemento') or '').strip() or None
    paciente.bairro = (request.POST.get('bairro') or '').strip() or None
    paciente.cidade = (request.POST.get('cidade') or '').strip() or None
    paciente.estado = (request.POST.get('estado') or '').strip() or None
    paciente.mae = (request.POST.get('mae') or '').strip() or None
    paciente.pai = (request.POST.get('pai') or '').strip() or None
    paciente.convenio_id = request.POST.get('convenio') or None
    paciente.carteira_conv = (request.POST.get('num_carteira') or '').strip() or None
    paciente.carteira_sus = (request.POST.get('carteira_sus') or '').strip() or None
    paciente.obs = (request.POST.get('obs') or '').strip() or None
    if 'prontuario' in request.POST:
        paciente.prontuario = (request.POST.get('prontuario') or '').strip()
    paciente.usalt = get_actor_name(request)
    paciente.save()

    cod_agenda = request.POST.get('cod_agenda')
    if cod_agenda:
        agenda = filtrar_por_clinica(Agenda.objects.filter(pk=cod_agenda), request).first()
        if agenda:
            sync_agenda_status(agenda, request, actor_name=get_actor_name(request))

    return JsonResponse({'success': True, 'message': 'Paciente atualizado com sucesso.'})


@login_required
@modulo_requerido('pacientes')
def consultar_cep_api(request, cep):
    try:
        dados = consultar_cep(cep)
        return JsonResponse({'success': True, 'dados': dados, 'data': dados})
    except ValueError:
        return JsonResponse({'success': False, 'message': 'CEP inválido.'}, status=400)
    except CepLookupError as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Erro ao consultar CEP.'}, status=500)
