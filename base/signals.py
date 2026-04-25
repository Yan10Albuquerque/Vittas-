from django.db.models.signals import post_save
from django.dispatch import receiver

from base.statuses import ensure_default_status_agendamento
from usuario.models import Clinica


@receiver(post_save, sender=Clinica)
def create_default_status_agendamento(sender, instance, created, **kwargs):
    if created:
        ensure_default_status_agendamento(instance)
