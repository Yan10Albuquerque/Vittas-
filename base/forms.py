from django import forms
from .models import (
    Convenio,
    Especialidade,
    FormaPagamento,
    StatusAgendamento,
    TipoConsulta,
    TipoExame,
)

class ConvenioForm(forms.ModelForm):
    class Meta:
        model = Convenio
        fields = ['cnpj', 'nome', 'telefone', 'email', 'status', 'obs']
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': '00.000.000/0000-00'}),
            'nome': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'telefone': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'obs': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full', 'rows': 3}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt


class EspecialidadeForm(forms.ModelForm):
    class Meta:
        model = Especialidade
        fields = ['descricao', 'status']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt


class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ['descricao', 'status']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt


class TipoConsultaForm(forms.ModelForm):
    class Meta:
        model = TipoConsulta
        fields = ['descricao', 'status']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt


class TipoExameForm(forms.ModelForm):
    class Meta:
        model = TipoExame
        fields = ['descricao', 'recorrencia', 'status']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'recorrencia': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'min': '0'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt


class StatusAgendamentoForm(forms.ModelForm):
    class Meta:
        model = StatusAgendamento
        fields = ['descricao', 'cor', 'nivel', 'status']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'cor': forms.TextInput(
                attrs={
                    'class': 'input input-bordered input-sm w-full',
                    'placeholder': 'Ex.: btn-primary',
                }
            ),
            'nivel': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'min': '1'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt
