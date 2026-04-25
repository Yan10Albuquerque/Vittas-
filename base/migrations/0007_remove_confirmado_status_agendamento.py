from django.db import migrations


def remove_confirmado_status_agendamento(apps, schema_editor):
    StatusAgendamento = apps.get_model("base", "StatusAgendamento")
    Agenda = apps.get_model("agenda", "Agenda")

    for status_confirmado in StatusAgendamento.objects.filter(descricao="Confirmado"):
        status_agendado, _ = StatusAgendamento.objects.get_or_create(
            clinica=status_confirmado.clinica,
            descricao="Agendado",
            defaults={
                "cor": "btn-primary",
                "nivel": 1,
                "status": True,
                "uscad": "migracao",
                "usalt": "migracao",
            },
        )
        Agenda.objects.filter(status_agendamento_id=status_confirmado.pk).update(
            status_agendamento_id=status_agendado.pk
        )
        status_confirmado.delete()


def rename_em_atendimento_to_em_andamento(apps, schema_editor):
    StatusAgendamento = apps.get_model("base", "StatusAgendamento")

    for status_obj in StatusAgendamento.objects.filter(descricao="Em Atendimento"):
        existente = StatusAgendamento.objects.filter(
            clinica=status_obj.clinica,
            descricao="Em Andamento",
        ).exclude(pk=status_obj.pk).first()
        if existente:
            continue
        status_obj.descricao = "Em Andamento"
        status_obj.cor = "btn-warning"
        status_obj.nivel = 2
        status_obj.status = True
        status_obj.usalt = "migracao"
        status_obj.save(update_fields=["descricao", "cor", "nivel", "status", "usalt", "dtalt"])


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0005_agenda_clinica_historicalagenda_clinica"),
        ("base", "0006_seed_default_status_agendamento"),
    ]

    operations = [
        migrations.RunPython(rename_em_atendimento_to_em_andamento, migrations.RunPython.noop),
        migrations.RunPython(remove_confirmado_status_agendamento, migrations.RunPython.noop),
    ]
