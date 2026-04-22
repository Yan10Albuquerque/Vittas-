from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from base.tenancy import ClinicaModuloRequiredMixin, get_actor_name, set_clinica
from .models import Convenio, Especialidade, FormaPagamento, StatusAgendamento, TipoConsulta, TipoExame
from .forms import (
    ConvenioForm,
    EspecialidadeForm,
    FormaPagamentoForm,
    StatusAgendamentoForm,
    TipoConsultaForm,
    TipoExameForm,
)

class ConvenioListView(ClinicaModuloRequiredMixin, ListView):
    model = Convenio
    template_name = 'convenios/list.html'
    context_object_name = 'convenios'
    paginate_by = 10
    modulo_requerido = 'cadastros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) | 
                Q(cnpj__icontains=busca)
            )
        return queryset.order_by('nome')

class AjaxFormMixin:
    def form_valid(self, form):
        set_clinica(form.instance, self.request)
        if self.request.user.is_authenticated:
            if not self.object: # Create
                form.instance.uscad = get_actor_name(self.request)
            form.instance.usalt = get_actor_name(self.request)
            
        self.object = form.save()
        return JsonResponse({'success': True, 'message': 'Operação realizada com sucesso!'})

    def form_invalid(self, form):
        return JsonResponse({
            'success': False, 
            'html': render_to_string(
                self.template_name, 
                {'form': form}, 
                request=self.request
            )
        })

class ConvenioCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = Convenio
    form_class = ConvenioForm
    template_name = 'convenios/form_partial.html'
    modulo_requerido = 'cadastros'

class ConvenioUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = Convenio
    form_class = ConvenioForm
    template_name = 'convenios/form_partial.html'
    modulo_requerido = 'cadastros'

class ConvenioDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = Convenio
    success_url = reverse_lazy('base:convenio_list')
    modulo_requerido = 'cadastros'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


# Views de Especialidade
class EspecialidadeListView(ClinicaModuloRequiredMixin, ListView):
    model = Especialidade
    template_name = 'especialidades/list.html'
    context_object_name = 'especialidades'
    paginate_by = 10
    modulo_requerido = 'cadastros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(Q(descricao__icontains=busca))
        return queryset.order_by('descricao')


class EspecialidadeCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'especialidades/form_partial.html'
    modulo_requerido = 'cadastros'


class EspecialidadeUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'especialidades/form_partial.html'
    modulo_requerido = 'cadastros'


class EspecialidadeDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = Especialidade
    success_url = reverse_lazy('base:especialidade_list')
    modulo_requerido = 'cadastros'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


# Views de FormaPagamento
class FormaPagamentoListView(ClinicaModuloRequiredMixin, ListView):
    model = FormaPagamento
    template_name = 'formas_pagamento/list.html'
    context_object_name = 'formas_pagamento'
    paginate_by = 10
    modulo_requerido = 'cadastros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(Q(descricao__icontains=busca))
        return queryset.order_by('descricao')


class FormaPagamentoCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = FormaPagamento
    form_class = FormaPagamentoForm
    template_name = 'formas_pagamento/form_partial.html'
    modulo_requerido = 'cadastros'


class FormaPagamentoUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = FormaPagamento
    form_class = FormaPagamentoForm
    template_name = 'formas_pagamento/form_partial.html'
    modulo_requerido = 'cadastros'


class FormaPagamentoDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = FormaPagamento
    success_url = reverse_lazy('base:forma_pagamento_list')
    modulo_requerido = 'cadastros'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


# Views de TipoConsulta
class TipoConsultaListView(ClinicaModuloRequiredMixin, ListView):
    model = TipoConsulta
    template_name = 'tipos_consulta/list.html'
    context_object_name = 'tipos_consulta'
    paginate_by = 10
    modulo_requerido = 'cadastros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(Q(descricao__icontains=busca))
        return queryset.order_by('descricao')


class TipoConsultaCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = TipoConsulta
    form_class = TipoConsultaForm
    template_name = 'tipos_consulta/form_partial.html'
    modulo_requerido = 'cadastros'


class TipoConsultaUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = TipoConsulta
    form_class = TipoConsultaForm
    template_name = 'tipos_consulta/form_partial.html'
    modulo_requerido = 'cadastros'


class TipoConsultaDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = TipoConsulta
    success_url = reverse_lazy('base:tipo_consulta_list')
    modulo_requerido = 'cadastros'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


# Views de TipoExame
class TipoExameListView(ClinicaModuloRequiredMixin, ListView):
    model = TipoExame
    template_name = 'tipos_exame/list.html'
    context_object_name = 'tipos_exame'
    paginate_by = 10
    modulo_requerido = 'cadastros'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(Q(descricao__icontains=busca))
        return queryset.order_by('descricao')


class TipoExameCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'tipos_exame/form_partial.html'
    modulo_requerido = 'cadastros'


class TipoExameUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'tipos_exame/form_partial.html'
    modulo_requerido = 'cadastros'


class TipoExameDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = TipoExame
    success_url = reverse_lazy('base:tipo_exame_list')
    modulo_requerido = 'cadastros'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


class StatusAgendamentoListView(ClinicaModuloRequiredMixin, ListView):
    model = StatusAgendamento
    template_name = 'status_agendamento/list.html'
    context_object_name = 'status_agendamentos'
    paginate_by = 10
    modulo_requerido = 'cadastros'

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(descricao__icontains=busca) |
                Q(cor__icontains=busca)
            )
        return queryset.order_by('nivel', 'descricao')


class StatusAgendamentoCreateView(ClinicaModuloRequiredMixin, AjaxFormMixin, CreateView):
    model = StatusAgendamento
    form_class = StatusAgendamentoForm
    template_name = 'status_agendamento/form_partial.html'
    modulo_requerido = 'cadastros'


class StatusAgendamentoUpdateView(ClinicaModuloRequiredMixin, AjaxFormMixin, UpdateView):
    model = StatusAgendamento
    form_class = StatusAgendamentoForm
    template_name = 'status_agendamento/form_partial.html'
    modulo_requerido = 'cadastros'


class StatusAgendamentoDeleteView(ClinicaModuloRequiredMixin, DeleteView):
    model = StatusAgendamento
    success_url = reverse_lazy('base:status_agendamento_list')
    modulo_requerido = 'cadastros'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'message': 'Registro excluído com sucesso!'})


class MigracaoTecnologicaView(TemplateView):
    """View pública para exibir o plano de migração tecnológica"""
    template_name = 'migracao_tecnologia.html'
