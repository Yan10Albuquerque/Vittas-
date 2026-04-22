from django import forms

from .models import Clinica


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
