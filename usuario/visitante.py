"""Modo visitante: acesso sem cadastro a uma clínica de demonstração, somente leitura.

O visitante entra autenticado como uma clínica fictícia populada pelo comando
``seed_demo_data``. Essa clínica e seus colaboradores não possuem senha utilizável,
então o único caminho de acesso a ela é o botão "Entrar como visitante" — e toda
sessão aberta por esse caminho é marcada como somente leitura.
"""

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Clinica

VISITANTE_SESSION_KEY = "modo_visitante"
VISITANTE_EMAIL = "visitante@vittas.demo"
VISITANTE_NOME = "Clínica Demonstração"
VISITANTE_ACTOR = "modo_visitante"

MENSAGEM_SOMENTE_LEITURA = (
    "Modo visitante: esta é uma demonstração somente leitura, as alterações estão desabilitadas."
)


def modo_visitante_habilitado():
    return getattr(settings, "MODO_VISITANTE_HABILITADO", False)


def is_visitante(request):
    session = getattr(request, "session", None)
    return bool(session is not None and session.get(VISITANTE_SESSION_KEY))


def _criar_clinica_visitante():
    clinica = Clinica(
        nome_fantasia=VISITANTE_NOME,
        razao_social=VISITANTE_NOME,
        email=VISITANTE_EMAIL,
        telefone="(11) 4000-1000",
        status=True,
        uscad=VISITANTE_ACTOR,
        usalt=VISITANTE_ACTOR,
    )
    clinica.set_unusable_password()
    clinica.save()
    return clinica


def _dados_desatualizados(clinica):
    from agenda.models import Agenda

    return not Agenda.objects.filter(clinica=clinica, data=timezone.localdate()).exists()


def obter_clinica_visitante():
    """Retorna a clínica de demonstração, criando-a e populando-a quando necessário.

    Os dados fictícios são gerados relativos à data atual, então o seed é executado
    novamente quando a agenda do dia ainda não existe (ex.: primeiro acesso do dia).
    """
    clinica = Clinica.objects.filter(email=VISITANTE_EMAIL).first()
    if clinica is None:
        try:
            with transaction.atomic():
                clinica = _criar_clinica_visitante()
        except IntegrityError:
            # Outro acesso simultâneo criou a clínica primeiro.
            clinica = Clinica.objects.get(email=VISITANTE_EMAIL)

    if not clinica.status:
        clinica.status = True
        clinica.save(update_fields=["status"])

    if _dados_desatualizados(clinica):
        call_command("seed_demo_data", clinic_email=VISITANTE_EMAIL, stdout=StringIO())

    # O seed cria colaboradores com a senha pública de demonstração; na clínica do
    # visitante ninguém pode autenticar por senha (o que contornaria o modo leitura).
    for colaborador in clinica.colaboradores.all():
        if colaborador.has_usable_password():
            colaborador.set_unusable_password()
            colaborador.save(update_fields=["password"])

    return clinica
