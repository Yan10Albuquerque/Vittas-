from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from base.tenancy import (
    ClinicaModuloRequiredMixin,
    filtrar_por_clinica,
    get_actor_name,
    modulo_requerido,
    set_clinica,
)

from .forms import CategoriaFinanceiraForm, LancamentoFinanceiroForm
from .models import CategoriaFinanceira, LancamentoFinanceiro


def _parse_periodo(valor):
    if not valor:
        return None
    try:
        return timezone.datetime.strptime(valor, "%Y-%m").date()
    except ValueError:
        return None


def _somar(queryset, campo):
    return queryset.aggregate(
        total=Coalesce(
            Sum(campo),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )["total"]


def _redirect_back(request, fallback):
    destino = request.POST.get("next") or request.GET.get("next")
    return redirect(destino or fallback)


class FinanceiroDashboardView(ClinicaModuloRequiredMixin, TemplateView):
    template_name = "financeiro/dashboard.html"
    modulo_requerido = "financeiro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        periodo = _parse_periodo(self.request.GET.get("periodo")) or timezone.localdate().replace(day=1)
        lancamentos = filtrar_por_clinica(
            LancamentoFinanceiro.objects.select_related("categoria", "paciente", "convenio"),
            self.request,
        ).filter(competencia__year=periodo.year, competencia__month=periodo.month)

        receitas = lancamentos.filter(tipo=LancamentoFinanceiro.Tipo.RECEITA)
        despesas = lancamentos.filter(tipo=LancamentoFinanceiro.Tipo.DESPESA)

        context.update(
            {
                "periodo": periodo.strftime("%Y-%m"),
                "receitas_previstas": _somar(receitas.exclude(status=LancamentoFinanceiro.Status.CANCELADO), "valor"),
                "receitas_recebidas": _somar(receitas.filter(status=LancamentoFinanceiro.Status.PAGO), "valor_recebido"),
                "receitas_pendentes": _somar(
                    receitas.filter(status__in=[LancamentoFinanceiro.Status.PENDENTE, LancamentoFinanceiro.Status.ATRASADO, LancamentoFinanceiro.Status.PARCIAL]),
                    "valor",
                ),
                "despesas_previstas": _somar(despesas.exclude(status=LancamentoFinanceiro.Status.CANCELADO), "valor"),
                "despesas_pagas": _somar(despesas.filter(status=LancamentoFinanceiro.Status.PAGO), "valor_recebido"),
                "lancamentos_atrasados": receitas.filter(status=LancamentoFinanceiro.Status.ATRASADO).order_by("data_vencimento")[:8],
                "ultimos_lancamentos": lancamentos.order_by("-dtcad")[:10],
            }
        )
        context["saldo_periodo"] = context["receitas_recebidas"] - context["despesas_pagas"]
        return context


class LancamentoFinanceiroListView(ClinicaModuloRequiredMixin, ListView):
    model = LancamentoFinanceiro
    template_name = "financeiro/lancamentos/list.html"
    context_object_name = "lancamentos"
    paginate_by = 15
    modulo_requerido = "financeiro"

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "categoria",
            "paciente",
            "convenio",
            "forma_pagamento",
        )
        busca = (self.request.GET.get("busca") or "").strip()
        tipo = (self.request.GET.get("tipo") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        categoria_id = (self.request.GET.get("categoria") or "").strip()

        if busca:
            queryset = queryset.filter(
                Q(descricao__icontains=busca)
                | Q(nome_cliente__icontains=busca)
                | Q(paciente__nome__icontains=busca)
                | Q(convenio__nome__icontains=busca)
            )
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if status:
            queryset = queryset.filter(status=status)
        if categoria_id.isdigit():
            queryset = queryset.filter(categoria_id=int(categoria_id))

        return queryset.order_by("data_vencimento", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context.update(
            {
                "categorias": filtrar_por_clinica(CategoriaFinanceira.objects.filter(status=True), self.request).order_by("tipo", "descricao"),
                "tipos": LancamentoFinanceiro.Tipo.choices,
                "status_choices": LancamentoFinanceiro.Status.choices,
                "total_periodo": _somar(queryset.exclude(status=LancamentoFinanceiro.Status.CANCELADO), "valor"),
                "total_recebido": _somar(queryset.filter(status=LancamentoFinanceiro.Status.PAGO), "valor_recebido"),
                "total_em_aberto": _somar(
                    queryset.filter(status__in=[LancamentoFinanceiro.Status.PENDENTE, LancamentoFinanceiro.Status.ATRASADO, LancamentoFinanceiro.Status.PARCIAL]),
                    "valor",
                ),
            }
        )
        return context


class LancamentoFinanceiroCreateView(ClinicaModuloRequiredMixin, CreateView):
    model = LancamentoFinanceiro
    form_class = LancamentoFinanceiroForm
    template_name = "financeiro/lancamentos/form.html"
    success_url = reverse_lazy("financeiro:lancamento_list")
    modulo_requerido = "financeiro"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        query = self.request.GET

        for campo in ["tipo", "origem", "descricao", "nome_cliente"]:
            if query.get(campo):
                initial[campo] = query.get(campo)

        for campo in ["paciente", "convenio", "categoria"]:
            valor = (query.get(campo) or "").strip()
            if valor.isdigit():
                initial[campo] = int(valor)

        for campo in ["data_lancamento", "competencia", "data_vencimento", "data_pagamento"]:
            if query.get(campo):
                initial[campo] = query.get(campo)

        return initial

    def get_success_url(self):
        return self.request.POST.get("next") or self.request.GET.get("next") or self.success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.POST.get("next") or self.request.GET.get("next") or ""
        return context

    def form_valid(self, form):
        set_clinica(form.instance, self.request)
        form.instance.uscad = get_actor_name(self.request)
        if not form.instance.nome_cliente and form.instance.paciente_id:
            form.instance.nome_cliente = form.instance.paciente.nome
        return super().form_valid(form)


class LancamentoFinanceiroUpdateView(ClinicaModuloRequiredMixin, UpdateView):
    model = LancamentoFinanceiro
    form_class = LancamentoFinanceiroForm
    template_name = "financeiro/lancamentos/form.html"
    success_url = reverse_lazy("financeiro:lancamento_list")
    modulo_requerido = "financeiro"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        return self.request.POST.get("next") or self.request.GET.get("next") or self.success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.POST.get("next") or self.request.GET.get("next") or ""
        return context

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        if not form.instance.nome_cliente and form.instance.paciente_id:
            form.instance.nome_cliente = form.instance.paciente.nome
        return super().form_valid(form)


class CategoriaFinanceiraListView(ClinicaModuloRequiredMixin, ListView):
    model = CategoriaFinanceira
    template_name = "financeiro/categorias/list.html"
    context_object_name = "categorias"
    paginate_by = 15
    modulo_requerido = "financeiro"

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = (self.request.GET.get("busca") or "").strip()
        if busca:
            queryset = queryset.filter(Q(descricao__icontains=busca) | Q(tipo__icontains=busca))
        return queryset.order_by("tipo", "descricao")


class CategoriaFinanceiraCreateView(ClinicaModuloRequiredMixin, CreateView):
    model = CategoriaFinanceira
    form_class = CategoriaFinanceiraForm
    template_name = "financeiro/categorias/form.html"
    success_url = reverse_lazy("financeiro:categoria_list")
    modulo_requerido = "financeiro"

    def form_valid(self, form):
        set_clinica(form.instance, self.request)
        form.instance.uscad = get_actor_name(self.request)
        return super().form_valid(form)


class CategoriaFinanceiraUpdateView(ClinicaModuloRequiredMixin, UpdateView):
    model = CategoriaFinanceira
    form_class = CategoriaFinanceiraForm
    template_name = "financeiro/categorias/form.html"
    success_url = reverse_lazy("financeiro:categoria_list")
    modulo_requerido = "financeiro"

    def form_valid(self, form):
        form.instance.usalt = get_actor_name(self.request)
        return super().form_valid(form)


@login_required
@require_POST
@modulo_requerido("financeiro")
def baixar_lancamento(request, pk):
    lancamento = get_object_or_404(
        filtrar_por_clinica(LancamentoFinanceiro.objects.all(), request),
        pk=pk,
    )
    valor_informado = request.POST.get("valor_pago") or str(lancamento.valor_em_aberto or lancamento.valor)
    data_pagamento = request.POST.get("data_pagamento") or timezone.localdate().isoformat()

    try:
        valor_pago = Decimal(str(valor_informado).replace(",", "."))
    except Exception:
        messages.error(request, "Informe um valor de pagamento válido.")
        return _redirect_back(request, "financeiro:lancamento_list")

    if valor_pago <= 0:
        messages.error(request, "O valor do pagamento deve ser maior que zero.")
        return _redirect_back(request, "financeiro:lancamento_list")

    total_recebido = (lancamento.valor_recebido or Decimal("0.00")) + valor_pago
    if total_recebido > lancamento.valor:
        messages.error(request, "O pagamento informado excede o valor total do lançamento.")
        return _redirect_back(request, "financeiro:lancamento_list")

    lancamento.valor_recebido = total_recebido
    lancamento.data_pagamento = data_pagamento
    lancamento.usalt = get_actor_name(request)
    lancamento.save()

    if lancamento.status == LancamentoFinanceiro.Status.PAGO:
        messages.success(request, "Lançamento baixado com sucesso.")
    else:
        messages.success(request, "Pagamento parcial registrado com sucesso.")
    return _redirect_back(request, "financeiro:lancamento_list")


@login_required
@require_POST
@modulo_requerido("financeiro")
def cancelar_lancamento(request, pk):
    lancamento = get_object_or_404(
        filtrar_por_clinica(LancamentoFinanceiro.objects.all(), request),
        pk=pk,
    )
    if lancamento.status == LancamentoFinanceiro.Status.PAGO:
        messages.error(request, "Lançamentos pagos não podem ser cancelados.")
        return _redirect_back(request, "financeiro:lancamento_list")

    lancamento.status = LancamentoFinanceiro.Status.CANCELADO
    lancamento.usalt = get_actor_name(request)
    lancamento.save(update_fields=["status", "usalt", "dtalt"])
    messages.success(request, "Lançamento cancelado com sucesso.")
    return _redirect_back(request, "financeiro:lancamento_list")


def vendas (request):
    return render(request, "financeiro/vendas.html")
