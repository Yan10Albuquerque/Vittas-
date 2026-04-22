from datetime import datetime
import json
import logging
from json import JSONDecodeError

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from base.models import Especialidade
from base.tenancy import ClinicaModuloRequiredMixin, filtrar_por_clinica, get_actor_name, get_clinica_atual, set_clinica
from .models import Medico, MedicoEspecialidade, MedicoAgenda
from .forms import MedicoForm

logger = logging.getLogger(__name__)


class MedicoListView(ClinicaModuloRequiredMixin, ListView):
    model = Medico
    template_name = 'medicos/list.html'
    context_object_name = 'medicos'
    paginate_by = 10
    modulo_requerido = 'cadastros'

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')

        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca)
                | Q(crm__icontains=busca)
                | Q(cpf__icontains=busca)
            )

        return queryset.order_by('nome')


class MedicoCreateView(ClinicaModuloRequiredMixin, CreateView):
    model = Medico
    form_class = MedicoForm
    template_name = 'medicos/form.html'
    success_url = reverse_lazy('medico:medico_list')
    modulo_requerido = 'cadastros'

    def get_form_kwargs(self):
        return super().get_form_kwargs()

    def form_valid(self, form):
        set_clinica(form.instance, self.request)
        form.instance.uscad = get_actor_name(self.request)
        return super().form_valid(form)


class MedicoUpdateView(ClinicaModuloRequiredMixin, UpdateView):
    model = Medico
    form_class = MedicoForm
    template_name = 'medicos/form.html'
    success_url = reverse_lazy('medico:medico_list')
    modulo_requerido = 'cadastros'

    def get_form_kwargs(self):
        return super().get_form_kwargs()

    def _redirect_to_tab(self, tab_name):
        return redirect(f"{self.request.path}?tab={tab_name}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        especialidades_vinculadas = filtrar_por_clinica(
            self.object.especialidades.select_related('especialidade'),
            self.request,
        ).order_by(
            'especialidade__descricao'
        )
        especialidades_vinculadas_ids = especialidades_vinculadas.values_list('especialidade_id', flat=True)
        context['especialidades_disponiveis'] = filtrar_por_clinica(
            Especialidade.objects.filter(status=True).exclude(pk__in=especialidades_vinculadas_ids).order_by('descricao'),
            self.request,
        )
        context['especialidades_vinculadas'] = especialidades_vinculadas
        horarios = filtrar_por_clinica(
            MedicoAgenda.objects.filter(medico=self.object).order_by('hora'),
            self.request,
        )
        context['horarios_medico_json'] = json.dumps(
            [
                {
                    'horario': agenda.hora.strftime('%H:%M'),
                    'liberado': agenda.status,
                }
                for agenda in horarios
            ]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        clinica_atual = get_clinica_atual(request)
        actor_name = get_actor_name(request)

        if action == 'add_especialidade':
            especialidade_id = request.POST.get('especialidade_id')
            descricao = request.POST.get('especialidade_descricao', '').strip()
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

            if not especialidade_id:
                message = 'Selecione uma especialidade.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': message}, status=400)
                messages.error(request, message)
                return self._redirect_to_tab('especialidades')

            especialidade = filtrar_por_clinica(
                Especialidade.objects.filter(pk=especialidade_id, status=True),
                request,
            ).first()
            if not especialidade:
                message = 'Especialidade não encontrada.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': message}, status=404)
                messages.error(request, message)
                return self._redirect_to_tab('especialidades')

            defaults = {
                'descricao': descricao,
                'status': True,
                'clinica': clinica_atual,
                'uscad': actor_name,
            }
            with transaction.atomic():
                vinculo, created = MedicoEspecialidade.objects.get_or_create(
                    clinica=clinica_atual,
                    medico=self.object,
                    especialidade=especialidade,
                    defaults=defaults,
                )
            if not created:
                updated_fields = []
                if descricao and vinculo.descricao != descricao:
                    vinculo.descricao = descricao
                    updated_fields.append('descricao')
                if not vinculo.status:
                    vinculo.status = True
                    updated_fields.append('status')
                if updated_fields:
                    vinculo.uscad = vinculo.uscad or actor_name
                    vinculo.save(update_fields=updated_fields)

            message = 'Especialidade vinculada com sucesso!' if created else 'Especialidade já estava vinculada.'
            if not is_ajax:
                messages.success(request, message)
                return self._redirect_to_tab('especialidades')
            return JsonResponse(
                {
                    'success': True,
                    'message': message,
                    'especialidade': {
                        'id': vinculo.pk,
                        'descricao': vinculo.especialidade.descricao,
                    },
                }
            )

        if action == 'remove_especialidade':
            medico_especialidade_id = request.POST.get('medico_especialidade_id')
            vinculo = filtrar_por_clinica(MedicoEspecialidade.objects.filter(
                pk=medico_especialidade_id,
                medico=self.object,
            ), request).first()
            if vinculo:
                vinculo.delete()
            return redirect(f"{request.path}?tab=especialidades")

        if action == 'save_horarios':
            horarios_json = request.POST.get('horarios_json', '[]')
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

            if not clinica_atual:
                return JsonResponse({'success': False, 'message': 'Clínica atual não identificada.'}, status=400)

            try:
                horarios = json.loads(horarios_json)
            except JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Dados de horários inválidos.'}, status=400)

            if not isinstance(horarios, list) or not horarios:
                return JsonResponse({'success': False, 'message': 'Nenhum horário para gravar.'}, status=400)

            try:
                horarios_normalizados = []
                horarios_duplicados = set()

                for item in horarios:
                    if not isinstance(item, dict):
                        raise ValueError
                    hora_valor = (item.get('horario') or '').strip()
                    if not hora_valor:
                        raise ValueError
                    hora = datetime.strptime(hora_valor, '%H:%M').time()
                    if any(registro['hora'] == hora for registro in horarios_normalizados):
                        horarios_duplicados.add(hora.strftime('%H:%M'))
                        continue
                    horarios_normalizados.append(
                        {
                            'hora': hora,
                            'status': bool(item.get('liberado', True)),
                        }
                    )

                if not horarios_normalizados:
                    return JsonResponse({'success': False, 'message': 'Nenhum horário válido para gravar.'}, status=400)

                ultimo_cadastro = filtrar_por_clinica(
                    MedicoAgenda.objects.filter(medico=self.object),
                    request,
                ).aggregate(ultimo=Max('dtcad'))['ultimo']

                with transaction.atomic():
                    filtrar_por_clinica(
                        MedicoAgenda.objects.filter(medico=self.object),
                        request,
                    ).delete()

                    agendas = []
                    for item in horarios_normalizados:
                        agendas.append(
                            MedicoAgenda(
                                clinica=clinica_atual,
                                medico=self.object,
                                hora=item['hora'],
                                status=item['status'],
                                uscad=actor_name,
                            )
                        )

                    MedicoAgenda.objects.bulk_create(agendas)

                mensagem = f'{len(agendas)} horários gravados com sucesso!'
                if horarios_duplicados:
                    duplicados = ', '.join(sorted(horarios_duplicados))
                    mensagem = f'{mensagem} Horários duplicados ignorados: {duplicados}.'

                return JsonResponse({
                    'success': True,
                    'message': mensagem,
                    'horarios': [
                        {
                            'horario': agenda.hora.strftime('%H:%M'),
                            'liberado': agenda.status,
                        }
                        for agenda in agendas
                    ],
                    'substituiu_horarios': bool(ultimo_cadastro),
                })
            except (TypeError, ValueError):
                return JsonResponse({'success': False, 'message': 'Formato de horário inválido.'}, status=400)
            except Exception:
                logger.exception('Erro ao gravar horários do médico %s', self.object.pk)
                if is_ajax:
                    return JsonResponse(
                        {'success': False, 'message': 'Erro interno ao gravar os horários.'},
                        status=500,
                    )
                raise

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        return super().form_valid(form)


class MedicoDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = Medico
    success_url = reverse_lazy('medico:medico_list')
    modulo_requerido = 'cadastros'

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Médico excluído com sucesso!'})


class MedicoEspecialidadeDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = MedicoEspecialidade
    modulo_requerido = 'cadastros'

    def post(self, request, *args, **kwargs):
        medico = get_object_or_404(filtrar_por_clinica(Medico.objects.all(), request), pk=kwargs['pk'])
        vinculo = get_object_or_404(
            filtrar_por_clinica(MedicoEspecialidade.objects.filter(medico=medico), request),
            pk=kwargs['vinculo_id'],
        )
        vinculo.delete()
        return JsonResponse({'success': True, 'message': 'Especialidade desvinculada com sucesso!'})
