from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class ClinicaManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("O email da clínica é obrigatório.")

        email = self.normalize_email(email)
        extra_fields.setdefault("nome_fantasia", email.split("@")[0])
        clinica = self.model(email=email, **extra_fields)
        clinica.set_password(password)
        clinica.save(using=self._db)
        return clinica

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("status", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class Clinica(AbstractBaseUser, PermissionsMixin):
    class Plano(models.TextChoices):
        BASICO = "BASICO", "Básico"
        PROFISSIONAL = "PROFISSIONAL", "Profissional"
        ENTERPRISE = "ENTERPRISE", "Enterprise"

    MODULOS_POR_PLANO = {
        Plano.BASICO: {
            "pacientes",
            "agenda",
            "cadastros",
            "configuracoes",
            "enfermagem",
            "financeiro",
        },
        Plano.PROFISSIONAL: {
            "pacientes",
            "agenda",
            "cadastros",
            "configuracoes",
            "financeiro",
        },
        Plano.ENTERPRISE: {
            "pacientes",
            "agenda",
            "cadastros",
            "configuracoes",
            "enfermagem",
            "financeiro",
        },
    }

    nome_fantasia = models.CharField(max_length=80, verbose_name="Nome Fantasia")
    password = models.CharField(max_length=128, default="", verbose_name="password")
    razao_social = models.CharField(max_length=120, null=True, blank=True, verbose_name="Razão Social")
    cnpj = models.CharField(max_length=18, null=True, blank=True, unique=True, verbose_name="CNPJ")
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True, verbose_name="Email")
    telefone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    plano = models.CharField(
        max_length=20,
        choices=Plano.choices,
        default=Plano.BASICO,
        verbose_name="Plano",
    )
    status = models.BooleanField(default=True, verbose_name="Ativa")
    is_staff = models.BooleanField(default=False, verbose_name="Acesso ao Admin")
    reseta_senha = models.BooleanField(default=False, verbose_name="Forçar Redefinição de Senha")
    uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
    dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
    usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
    dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
    history = HistoricalRecords()

    objects = ClinicaManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome_fantasia"]

    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"
        ordering = ["nome_fantasia"]

    def __str__(self):
        return self.nome_fantasia

    @property
    def is_active(self):
        return self.status

    @property
    def username(self):
        return self.email

    @property
    def first_name(self):
        return self.nome_fantasia

    @property
    def clinica(self):
        return self

    @property
    def clinica_id(self):
        return self.pk

    def get_full_name(self):
        return self.nome_fantasia

    def get_short_name(self):
        return self.nome_fantasia

    @property
    def plano_normalizado(self):
        if self.plano == "PRO":
            return self.Plano.ENTERPRISE
        return self.plano

    def modulo_disponivel(self, modulo):
        return modulo in self.MODULOS_POR_PLANO.get(self.plano_normalizado, set())
