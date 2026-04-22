from django import forms
from .models import Medico


class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['cpf', 'crm', 'nome', 'celular', 'telefone', 'email', 'obs', 'status']
        widgets = {
            'cpf': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '000.000.000-00'}),
            'crm': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': '52-000000'}),
            'nome': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'celular': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '(00) 00000-0000'}),
            'telefone': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'data-mask': '(00) 0000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'obs': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full', 'rows': 3}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define valor inicial "52-" para novo registro
        if not self.instance.pk:
            self.fields['crm'].initial = '52-'

    def clean_uscad(self):
        return self.instance.uscad

    def clean_usalt(self):
        return self.instance.usalt
