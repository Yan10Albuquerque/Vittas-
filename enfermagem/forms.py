from django import forms
from .models import *

class ProcedimentoForm(forms.ModelForm):
    class Meta:
        model = Procedimento
        fields = ['codigo', 'descricao', 'status']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'descricao': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'status': forms.CheckboxInput(attrs={'class': 'toggle toggle-success toggle-sm'}),
        }
        
        

        
