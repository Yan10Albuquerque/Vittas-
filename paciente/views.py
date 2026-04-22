import uuid
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import OperationalError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from base.models import StatusAgendamento
from base.statuses import get_status_agendamento_em_atendimento
from base.tenancy import ClinicaModuloRequiredMixin, filtrar_por_clinica, get_actor_name, get_clinica_atual, modulo_requerido, set_clinica
from base.services import CepLookupError, consultar_cep
from financeiro.services import sincronizar_lancamento_vacina
from .forms import PacienteForm, PacienteVacinaForm
from .models import Paciente, PacienteVacina


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
        context['vacina_form'] = kwargs.get('vacina_form', PacienteVacinaForm(request=self.request))
        context['vacinas'] = self.object.vacinas.select_related('aplicador', 'forma_pagamento').order_by('-data_aplicacao', '-dtcad')
        context['active_tab'] = kwargs.get('active_tab', self.request.GET.get('tab', 'cadastro'))
        context['vacina_id_edicao'] = kwargs.get('vacina_id_edicao', '')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'salvar_vacina' in request.POST:
            vacina_id = request.POST.get('vacina_id')
            vacina_instance = None

            if vacina_id:
                vacina_instance = get_object_or_404(
                    filtrar_por_clinica(PacienteVacina.objects.filter(paciente=self.object), request),
                    pk=vacina_id,
                )

            vacina_form = PacienteVacinaForm(request.POST, instance=vacina_instance, request=request)
            if vacina_form.is_valid():
                vacina = vacina_form.save(commit=False)
                set_clinica(vacina, request)
                if vacina_instance:
                    vacina.usalt = get_actor_name(request)
                else:
                    vacina.paciente = self.object
                    vacina.uscad = get_actor_name(request)
                vacina.save()
                sincronizar_lancamento_vacina(vacina)
                return redirect(f"{request.path}?tab=vacinas")

            context = self.get_context_data(
                form=self.get_form(),
                vacina_form=vacina_form,
                active_tab='vacinas',
                vacina_id_edicao=vacina_id or '',
            )
            return self.render_to_response(context)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        return super().form_valid(form)


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
    paciente.usalt = get_actor_name(request)
    paciente.save()

    cod_agenda = request.POST.get('cod_agenda')
    if cod_agenda:
        agenda = filtrar_por_clinica(Agenda.objects.filter(pk=cod_agenda), request).first()
        status_atendimento = get_status_agendamento_em_atendimento(request)
        if agenda and status_atendimento:
            agenda.status_agendamento = status_atendimento
            agenda.usalt = get_actor_name(request)
            agenda.save(update_fields=['status_agendamento', 'usalt', 'dtalt'])

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
