from django import forms
from django.db.models import Q

from base.tenancy import get_clinica_atual
from base.models import Convenio, FormaPagamento
from paciente.models import Paciente

from .models import CategoriaFinanceira, LancamentoFinanceiro


class CategoriaFinanceiraForm(forms.ModelForm):
    class Meta:
        model = CategoriaFinanceira
        fields = ["descricao", "tipo", "cor", "status"]
        widgets = {
            "descricao": forms.TextInput(attrs={"class": "input input-bordered input-sm w-full"}),
            "tipo": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "cor": forms.TextInput(attrs={"class": "input input-bordered input-sm w-full", "placeholder": "badge-primary"}),
            "status": forms.CheckboxInput(attrs={"class": "toggle toggle-success toggle-sm"}),
        }


class LancamentoFinanceiroForm(forms.ModelForm):
    class Meta:
        model = LancamentoFinanceiro
        fields = [
            "tipo",
            "origem",
            "categoria",
            "descricao",
            "paciente",
            "convenio",
            "nome_cliente",
            "forma_pagamento",
            "data_lancamento",
            "competencia",
            "data_vencimento",
            "data_pagamento",
            "valor",
            "valor_recebido",
            "status",
            "observacoes",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "origem": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "categoria": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "descricao": forms.TextInput(attrs={"class": "input input-bordered input-sm w-full"}),
            "paciente": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "convenio": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "nome_cliente": forms.TextInput(attrs={"class": "input input-bordered input-sm w-full"}),
            "forma_pagamento": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "data_lancamento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "competencia": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "data_vencimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "data_pagamento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "valor": forms.NumberInput(attrs={"class": "input input-bordered input-sm w-full", "step": "0.01", "min": "0"}),
            "valor_recebido": forms.NumberInput(attrs={"class": "input input-bordered input-sm w-full", "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "observacoes": forms.Textarea(attrs={"class": "textarea textarea-bordered textarea-sm w-full", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        clinica = get_clinica_atual(self.request) if self.request else None
        instance = getattr(self, "instance", None)

        if clinica:
            categoria_qs = CategoriaFinanceira.objects.filter(clinica=clinica)
            paciente_qs = Paciente.objects.filter(clinica=clinica)
            convenio_qs = Convenio.objects.filter(clinica=clinica)
            forma_pagamento_qs = FormaPagamento.objects.filter(clinica=clinica)

            if instance and instance.pk:
                categoria_qs = categoria_qs.filter(Q(status=True) | Q(pk=instance.categoria_id))
                paciente_qs = paciente_qs.filter(Q(status=True) | Q(pk=instance.paciente_id))
                convenio_qs = convenio_qs.filter(Q(status=True) | Q(pk=instance.convenio_id))
                forma_pagamento_qs = forma_pagamento_qs.filter(Q(status=True) | Q(pk=instance.forma_pagamento_id))
            else:
                categoria_qs = categoria_qs.filter(status=True)
                paciente_qs = paciente_qs.filter(status=True)
                convenio_qs = convenio_qs.filter(status=True)
                forma_pagamento_qs = forma_pagamento_qs.filter(status=True)

            self.fields["categoria"].queryset = categoria_qs.order_by("tipo", "descricao").distinct()
            self.fields["paciente"].queryset = paciente_qs.order_by("nome").distinct()
            self.fields["convenio"].queryset = convenio_qs.order_by("nome").distinct()
            self.fields["forma_pagamento"].queryset = forma_pagamento_qs.order_by("descricao").distinct()

        self.fields["paciente"].required = False
        self.fields["convenio"].required = False
        self.fields["nome_cliente"].required = False
        self.fields["forma_pagamento"].required = False
        self.fields["data_pagamento"].required = False
        self.fields["valor_recebido"].required = False
        self.fields["data_lancamento"].input_formats = ["%Y-%m-%d"]
        self.fields["competencia"].input_formats = ["%Y-%m-%d"]
        self.fields["data_vencimento"].input_formats = ["%Y-%m-%d"]
        self.fields["data_pagamento"].input_formats = ["%Y-%m-%d"]

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get("paciente")
        convenio = cleaned_data.get("convenio")
        nome_cliente = (cleaned_data.get("nome_cliente") or "").strip()
        valor = cleaned_data.get("valor")
        valor_recebido = cleaned_data.get("valor_recebido")
        status = cleaned_data.get("status")

        if not paciente and not convenio and not nome_cliente:
            self.add_error("nome_cliente", "Informe um paciente, convênio ou nome do cliente.")

        if valor_recebido and valor and valor_recebido > valor:
            self.add_error("valor_recebido", "O valor recebido não pode ser maior que o valor do lançamento.")

        if status == LancamentoFinanceiro.Status.PAGO and not cleaned_data.get("data_pagamento"):
            cleaned_data["data_pagamento"] = cleaned_data.get("data_vencimento")

        return cleaned_data
