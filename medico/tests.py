import json
from datetime import time

from django.test import TestCase
from django.urls import reverse

from base.models import Especialidade
from medico.models import Medico, MedicoAgenda, MedicoEspecialidade
from usuario.models import Clinica


class MedicoAsyncFlowsTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Medico",
            email="medico@clinica.com",
            password="123456",
            plano=Clinica.Plano.PROFISSIONAL,
        )
        self.client.force_login(self.clinica)
        self.medico = Medico.objects.create(
            clinica=self.clinica,
            crm="52-123456",
            nome="Dr. Fluxo",
        )
        self.especialidade = Especialidade.objects.create(
            clinica=self.clinica,
            descricao="Ortopedia",
        )

    def test_vincula_especialidade_via_ajax(self):
        response = self.client.post(
            reverse("medico:medico_update", args=[self.medico.pk]),
            {
                "action": "add_especialidade",
                "especialidade_id": self.especialidade.pk,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(
            MedicoEspecialidade.objects.filter(
                clinica=self.clinica,
                medico=self.medico,
                especialidade=self.especialidade,
            ).exists()
        )

    def test_vincula_especialidade_via_post_normal_redireciona_para_aba(self):
        response = self.client.post(
            reverse("medico:medico_update", args=[self.medico.pk]),
            {
                "action": "add_especialidade",
                "especialidade_id": self.especialidade.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("?tab=especialidades"))
        self.assertTrue(
            MedicoEspecialidade.objects.filter(
                clinica=self.clinica,
                medico=self.medico,
                especialidade=self.especialidade,
            ).exists()
        )

    def test_grava_horarios_via_ajax(self):
        response = self.client.post(
            reverse("medico:medico_update", args=[self.medico.pk]),
            {
                "action": "save_horarios",
                "horarios_json": json.dumps(
                    [
                        {"horario": "08:00", "liberado": True},
                        {"horario": "08:30", "liberado": False},
                    ]
                ),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(
            list(
                MedicoAgenda.objects.filter(medico=self.medico)
                .order_by("hora")
                .values_list("hora", flat=True)
            ),
            [time(8, 0), time(8, 30)],
        )

    def test_rejeita_horarios_invalidos_via_ajax(self):
        response = self.client.post(
            reverse("medico:medico_update", args=[self.medico.pk]),
            {
                "action": "save_horarios",
                "horarios_json": json.dumps([{"horario": "", "liberado": True}]),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
