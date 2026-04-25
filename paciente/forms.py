from django import forms
from base.tenancy import get_clinica_atual
from .models import Paciente, PacienteVacina

ESTADOS_BRASIL = [
    ('', '-----'),
    ('AC', 'AC'),
    ('AL', 'AL'),
    ('AP', 'AP'),
    ('AM', 'AM'),
    ('BA', 'BA'),
    ('CE', 'CE'),
    ('DF', 'DF'),
    ('ES', 'ES'),
    ('GO', 'GO'),
    ('MA', 'MA'),
    ('MT', 'MT'),
    ('MS', 'MS'),
    ('MG', 'MG'),
    ('PA', 'PA'),
    ('PB', 'PB'),
    ('PR', 'PR'),
    ('PE', 'PE'),
    ('PI', 'PI'),
    ('RJ', 'RJ'),
    ('RN', 'RN'),
    ('RS', 'RS'),
    ('RO', 'RO'),
    ('RR', 'RR'),
    ('SC', 'SC'),
    ('SP', 'SP'),
    ('SE', 'SE'),
    ('TO', 'TO'),
]

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'
        exclude = ['clinica', 'dtcad', 'dtalt', 'uscad', 'usalt'] # Campos automáticos
        widgets = {
            'nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'nome': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'cpf': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '000.000.000-00'}),
            'celular': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '(00) 00000-0000'}),
            'telefone': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '(00) 0000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'obs': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full', 'rows': 3}),
            'prontuario': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full min-h-48', 'rows': 10}),
            'sexo': forms.Select(choices=[('M', 'MASCULINO'), ('F', 'FEMININO'), ('O', 'OUTRO')], attrs={'class': 'select select-bordered select-sm w-full'}),
            'estado': forms.Select(choices=ESTADOS_BRASIL, attrs={'class': 'select select-bordered select-sm w-full'}),
            'convenio': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'sus': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-secondary checkbox-sm'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        clinica = get_clinica_atual(self.request) if self.request else None
        if clinica:
            self.fields['convenio'].queryset = self.fields['convenio'].queryset.filter(clinica=clinica).order_by('nome')
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'input input-bordered input-sm w-full'


class PacienteVacinaForm(forms.ModelForm):
    class Meta:
        model = PacienteVacina
        fields = ['data_aplicacao', 'descricao_vacina', 'aplicador', 'forma_pagamento', 'valor', 'obs']
        widgets = {
            'data_aplicacao': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'descricao_vacina': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'aplicador': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'forma_pagamento': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'valor': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'step': '0.01'}),
            'obs': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        clinica = get_clinica_atual(self.request) if self.request else None
        if clinica:
            self.fields['aplicador'].queryset = self.fields['aplicador'].queryset.filter(pk=clinica.pk).order_by('nome_fantasia')
            self.fields['forma_pagamento'].queryset = self.fields['forma_pagamento'].queryset.filter(clinica=clinica).order_by('descricao')

