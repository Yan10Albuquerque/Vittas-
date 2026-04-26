from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from simple_history.models import HistoricalRecords

from base.history import resolve_history_user


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
    history = HistoricalRecords(get_user=resolve_history_user)

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

    @property
    def nome_exibicao(self):
        return self.nome_fantasia

    @property
    def tipo_usuario(self):
        return "CLINICA"

    @property
    def pode_gerenciar_equipe(self):
        return True

    @property
    def limite_colaboradores(self):
        if self.plano_normalizado == self.Plano.PROFISSIONAL:
            return 5
        return None

    def colaboradores_ativos(self):
        return self.colaboradores.filter(status=True)

    def pode_adicionar_colaborador(self, colaborador_atual=None):
        limite = self.limite_colaboradores
        if limite is None:
            return True
        ativos = self.colaboradores_ativos()
        if colaborador_atual and colaborador_atual.pk:
            ativos = ativos.exclude(pk=colaborador_atual.pk)
        return ativos.count() < limite


class ColaboradorManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, clinica, email, password, **extra_fields):
        if not clinica:
            raise ValueError("A clínica do colaborador é obrigatória.")
        if not email:
            raise ValueError("O email do colaborador é obrigatório.")

        email = self.normalize_email(email)
        extra_fields.setdefault("nome", email.split("@")[0])
        papel = extra_fields.get("papel", Colaborador.Papel.RECEPCAO)
        extra_fields.setdefault(
            "modulos_permitidos",
            list(Colaborador.MODULOS_PADRAO_POR_PAPEL.get(papel, set())),
        )
        colaborador = self.model(clinica=clinica, email=email, **extra_fields)
        colaborador.set_password(password)
        colaborador.save(using=self._db)
        return colaborador

    def create_user(self, clinica, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("status", True)
        return self._create_user(clinica, email, password, **extra_fields)

    def create_superuser(self, clinica, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", True)
        return self._create_user(clinica, email, password, **extra_fields)


class Colaborador(AbstractBaseUser, PermissionsMixin):
    class Papel(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        RECEPCAO = "RECEPCAO", "Recepção"
        FINANCEIRO = "FINANCEIRO", "Financeiro"
        ENFERMAGEM = "ENFERMAGEM", "Enfermagem"
        MEDICO = "MEDICO", "Médico"

    MODULOS_PADRAO_POR_PAPEL = {
        Papel.ADMIN: {"pacientes", "agenda", "cadastros", "configuracoes", "enfermagem", "financeiro"},
        Papel.RECEPCAO: {"pacientes", "agenda", "configuracoes"},
        Papel.FINANCEIRO: {"pacientes", "financeiro"},
        Papel.ENFERMAGEM: {"pacientes", "enfermagem"},
        Papel.MEDICO: {"agenda"},
    }

    clinica = models.ForeignKey(
        "usuario.Clinica",
        on_delete=models.CASCADE,
        related_name="colaboradores",
        verbose_name="Clínica",
    )
    nome = models.CharField(max_length=80, verbose_name="Nome")
    email = models.EmailField(max_length=100, unique=True, verbose_name="Email")
    password = models.CharField(max_length=128, default="", verbose_name="password")
    papel = models.CharField(
        max_length=20,
        choices=Papel.choices,
        default=Papel.RECEPCAO,
        verbose_name="Papel",
    )
    modulos_permitidos = models.JSONField(default=list, blank=True, verbose_name="Módulos permitidos")
    status = models.BooleanField(default=True, verbose_name="Ativo")
    is_staff = models.BooleanField(default=False, verbose_name="Acesso ao Admin")
    reseta_senha = models.BooleanField(default=False, verbose_name="Forçar Redefinição de Senha")
    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="colaborador_set",
        related_query_name="colaborador",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="colaborador_set",
        related_query_name="colaborador",
        verbose_name="user permissions",
    )
    uscad = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Cadastro")
    dtcad = models.DateTimeField(auto_now_add=True, verbose_name="Data Cadastro")
    usalt = models.CharField(max_length=25, null=True, blank=True, verbose_name="Usuário Alteração")
    dtalt = models.DateTimeField(auto_now=True, verbose_name="Data Alteração")
    history = HistoricalRecords(get_user=resolve_history_user)

    objects = ColaboradorManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.clinica.nome_fantasia})"

    @property
    def is_active(self):
        return self.status and self.clinica.status

    @property
    def username(self):
        return self.email

    @property
    def first_name(self):
        return self.nome

    @property
    def nome_fantasia(self):
        return self.nome

    @property
    def nome_exibicao(self):
        return self.nome

    @property
    def tipo_usuario(self):
        return "COLABORADOR"

    @property
    def pode_gerenciar_equipe(self):
        return self.papel == self.Papel.ADMIN

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome

    def modulo_disponivel(self, modulo):
        modulos_padrao = self.MODULOS_PADRAO_POR_PAPEL.get(self.papel, set())
        modulos_salvos = self.modulos_permitidos
        modulos_configurados = set(modulos_padrao if modulos_salvos is None else modulos_salvos)
        return (
            modulo in modulos_configurados
            and self.clinica.modulo_disponivel(modulo)
        )

    def get_modulos_padrao_por_papel(self):
        return self.MODULOS_PADRAO_POR_PAPEL.get(self.papel, set())
