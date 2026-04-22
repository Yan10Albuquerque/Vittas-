from django import forms

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
            "data_lancamento": forms.DateInput(attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "competencia": forms.DateInput(attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "data_vencimento": forms.DateInput(attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "data_pagamento": forms.DateInput(attrs={"type": "date", "class": "input input-bordered input-sm w-full"}),
            "valor": forms.NumberInput(attrs={"class": "input input-bordered input-sm w-full", "step": "0.01", "min": "0"}),
            "valor_recebido": forms.NumberInput(attrs={"class": "input input-bordered input-sm w-full", "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": "select select-bordered select-sm w-full"}),
            "observacoes": forms.Textarea(attrs={"class": "textarea textarea-bordered textarea-sm w-full", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        clinica = get_clinica_atual(self.request) if self.request else None

        if clinica:
            self.fields["categoria"].queryset = CategoriaFinanceira.objects.filter(clinica=clinica, status=True).order_by("tipo", "descricao")
            self.fields["paciente"].queryset = Paciente.objects.filter(clinica=clinica, status=True).order_by("nome")
            self.fields["convenio"].queryset = Convenio.objects.filter(clinica=clinica, status=True).order_by("nome")
            self.fields["forma_pagamento"].queryset = FormaPagamento.objects.filter(clinica=clinica, status=True).order_by("descricao")

        self.fields["paciente"].required = False
        self.fields["convenio"].required = False
        self.fields["nome_cliente"].required = False
        self.fields["forma_pagamento"].required = False
        self.fields["data_pagamento"].required = False
        self.fields["valor_recebido"].required = False

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
