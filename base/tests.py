from django.test import TestCase
from django.urls import reverse

from base.models import StatusAgendamento
from usuario.models import Clinica


class StatusAgendamentoCrudTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Base",
            email="base@clinica.com",
            password="123456",
            plano=Clinica.Plano.BASICO,
        )
        self.client.force_login(self.clinica)

    def test_lista_status_agendamento_renderiza(self):
        response = self.client.get(reverse("base:status_agendamento_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Status de Agendamento")

    def test_cria_status_agendamento_vinculado_a_clinica(self):
        response = self.client.post(
            reverse("base:status_agendamento_create"),
            {
                "descricao": "Confirmado",
                "cor": "btn-success",
                "nivel": 1,
                "status": "on",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(StatusAgendamento.objects.filter(clinica=self.clinica, descricao="Confirmado").exists())
