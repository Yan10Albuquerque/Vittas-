from django import forms
from django.core.exceptions import ValidationError

from base.tenancy import MODULO_LABELS
from .models import Clinica, Colaborador


class ClinicaForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "autocomplete": "new-password",
            }
        ),
        required=False,
        help_text="Preencha apenas se desejar definir ou alterar a senha de acesso.",
    )

    class Meta:
        model = Clinica
        fields = [
            "nome_fantasia",
            "razao_social",
            "cnpj",
            "email",
            "telefone",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_superuser:
            self.fields["plano"] = forms.ChoiceField(
                choices=Clinica.Plano.choices,
                initial=self.instance.plano or Clinica.Plano.BASICO,
                required=True,
            )
            self.fields["status"] = forms.BooleanField(
                required=False,
                initial=self.instance.status,
            )
            self.fields["reseta_senha"] = forms.BooleanField(
                required=False,
                initial=self.instance.reseta_senha,
            )

        if not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Senha obrigatória para o primeiro acesso da clínica."

        for name, field in self.fields.items():
            if name in {"status", "reseta_senha"}:
                field.widget.attrs.update({"class": "toggle toggle-success"})
            elif name == "plano":
                field.widget.attrs.setdefault("class", "select select-bordered w-full")
            else:
                field.widget.attrs.setdefault("class", "input input-bordered w-full")

    def save(self, commit=True):
        clinica = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            clinica.set_password(password)
        if "plano" in self.cleaned_data:
            clinica.plano = self.cleaned_data["plano"]
        if "status" in self.cleaned_data:
            clinica.status = self.cleaned_data["status"]
        if "reseta_senha" in self.cleaned_data:
            clinica.reseta_senha = self.cleaned_data["reseta_senha"]

        if commit:
            clinica.save()
        return clinica


class ColaboradorForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "autocomplete": "new-password",
            }
        ),
        required=False,
        help_text="Preencha apenas se desejar definir ou alterar a senha de acesso.",
    )
    modulos_permitidos = forms.MultipleChoiceField(
        label="Permissões de módulos",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Colaborador
        fields = [
            "nome",
            "email",
            "papel",
            "status",
            "reseta_senha",
        ]

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        self.clinica = kwargs.pop("clinica", None)
        super().__init__(*args, **kwargs)

        self.fields["papel"].widget.attrs.setdefault("class", "select select-bordered w-full")
        self.fields["nome"].widget.attrs.setdefault("class", "input input-bordered w-full")
        self.fields["email"].widget.attrs.setdefault("class", "input input-bordered w-full")
        self.fields["status"].widget.attrs.update({"class": "toggle toggle-success"})
        self.fields["reseta_senha"].widget.attrs.update({"class": "toggle toggle-warning"})
        papel_selecionado = self._get_papel_selecionado()
        modulos_base = self._get_modulos_base(papel_selecionado)
        self.fields["modulos_permitidos"].choices = [
            (modulo, MODULO_LABELS.get(modulo, modulo.title()))
            for modulo in MODULO_LABELS
        ]
        modulos_iniciais = self.instance.modulos_permitidos
        if modulos_iniciais is None:
            modulos_iniciais = list(modulos_base)
        self.initial["modulos_permitidos"] = list(modulos_iniciais)

        if not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Senha obrigatória para o primeiro acesso do colaborador."

    def clean(self):
        cleaned_data = super().clean()
        clinica = self.clinica or getattr(self.instance, "clinica", None)
        status = cleaned_data.get("status", True)
        papel = cleaned_data.get("papel") or self.instance.papel or Colaborador.Papel.RECEPCAO
        modulos_permitidos = set(cleaned_data.get("modulos_permitidos") or [])
        modulos_base = self._get_modulos_base(papel)
        modulos_validos = set(MODULO_LABELS.keys())
        if not clinica or not status:
            cleaned_data["modulos_permitidos"] = list(modulos_permitidos if modulos_permitidos else modulos_base)
            return cleaned_data

        modulos_invalidos = modulos_permitidos - modulos_validos
        if modulos_invalidos:
            raise ValidationError(
                "As permissões selecionadas contêm módulos inválidos."
            )

        if not clinica.pode_adicionar_colaborador(colaborador_atual=self.instance):
            raise ValidationError(
                "O plano Profissional permite até 5 colaboradores ativos. Inative um colaborador atual ou altere o plano da clínica."
            )

        cleaned_data["modulos_permitidos"] = list(modulos_permitidos)

        return cleaned_data

    def save(self, commit=True):
        colaborador = super().save(commit=False)
        if self.clinica and not colaborador.clinica_id:
            colaborador.clinica = self.clinica

        password = self.cleaned_data.get("password")
        if password:
            colaborador.set_password(password)
        colaborador.modulos_permitidos = self.cleaned_data.get("modulos_permitidos")

        if commit:
            colaborador.save()
        return colaborador

    def _get_modulos_base(self, papel):
        return set(Colaborador.MODULOS_PADRAO_POR_PAPEL.get(papel, set()))

    def _get_papel_selecionado(self):
        if self.is_bound:
            return self.data.get(self.add_prefix("papel")) or Colaborador.Papel.RECEPCAO
        return self.instance.papel or self.initial.get("papel") or Colaborador.Papel.RECEPCAO
