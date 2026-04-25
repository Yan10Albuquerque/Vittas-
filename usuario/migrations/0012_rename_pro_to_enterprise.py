from django.db import migrations, models


def rename_pro_to_enterprise(apps, schema_editor):
    Clinica = apps.get_model("usuario", "Clinica")
    HistoricalClinica = apps.get_model("usuario", "HistoricalClinica")

    Clinica.objects.filter(plano="PRO").update(plano="ENTERPRISE")
    HistoricalClinica.objects.filter(plano="PRO").update(plano="ENTERPRISE")


class Migration(migrations.Migration):

    dependencies = [
        ("usuario", "0011_remove_historicalusuario_clinica_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_pro_to_enterprise, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="clinica",
            name="plano",
            field=models.CharField(
                choices=[
                    ("BASICO", "Básico"),
                    ("PROFISSIONAL", "Profissional"),
                    ("ENTERPRISE", "Enterprise"),
                ],
                default="BASICO",
                max_length=20,
                verbose_name="Plano",
            ),
        ),
        migrations.AlterField(
            model_name="historicalclinica",
            name="plano",
            field=models.CharField(
                choices=[
                    ("BASICO", "Básico"),
                    ("PROFISSIONAL", "Profissional"),
                    ("ENTERPRISE", "Enterprise"),
                ],
                default="BASICO",
                max_length=20,
                verbose_name="Plano",
            ),
        ),
    ]
