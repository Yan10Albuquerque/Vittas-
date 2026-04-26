from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from enfermagem.models import AgendaEnfermagem, Autorizacao, Procedimento
from paciente.models import Paciente
from usuario.models import Clinica


class AgendaEnfermagemRulesTest(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Teste",
            email="teste@clinica.com",
            password="123456",
            plano=Clinica.Plano.ENTERPRISE,
        )
        self.client.force_login(self.clinica)
        self.paciente = Paciente.objects.create(
            clinica=self.clinica,
            cpf="12345678901",
            nome="Paciente Teste",
            celular="11999999999",
            nascimento="1990-01-01",
        )
        self.procedimento = Procedimento.objects.create(
            clinica=self.clinica,
            nome="Curativo",
            descricao="Curativo simples",
        )
        self.autorizacao = Autorizacao.objects.create(
            clinica=self.clinica,
            paciente=self.paciente,
            procedimento=self.procedimento,
            status="APROVADA",
        )

    def _proximo_dia_util(self):
        data = timezone.localdate() + timedelta(days=1)
        while data.weekday() >= 5:
            data += timedelta(days=1)
        return data

    def _data_storage(self, data_agendamento):
        return timezone.make_aware(
            datetime.combine(data_agendamento, datetime.min.time()),
            timezone.get_current_timezone(),
        )

    def test_impede_duplo_agendamento_ativo_para_mesma_autorizacao(self):
        data_agendamento = self._proximo_dia_util()
        data_storage = self._data_storage(data_agendamento)

        AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=data_storage,
            hora_agendamento="09:00",
        )

        with self.assertRaises(ValidationError):
            AgendaEnfermagem.objects.create(
                clinica=self.clinica,
                autorizacao=self.autorizacao,
                data_agendamento=data_storage,
                hora_agendamento="10:00",
            )

    def test_endpoint_retorna_apenas_horarios_livres(self):
        data_agendamento = self._proximo_dia_util()
        data_storage = self._data_storage(data_agendamento)

        AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=data_storage,
            hora_agendamento="09:00",
        )

        outra_autorizacao = Autorizacao.objects.create(
            clinica=self.clinica,
            paciente=self.paciente,
            procedimento=self.procedimento,
            status="APROVADA",
        )

        response = self.client.get(
            reverse("enfermagem:horarios_disponiveis", args=[outra_autorizacao.pk]),
            {"data": data_agendamento.strftime("%Y-%m-%d")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("09:00", response.json())
        self.assertIn("10:00", response.json())

    def test_cancelar_agendamento_altera_status_para_cancelado(self):
        data_agendamento = self._proximo_dia_util()
        agendamento = AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=self._data_storage(data_agendamento),
            hora_agendamento="09:00",
        )

        response = self.client.post(
            reverse("enfermagem:agendamento_cancelar", args=[agendamento.pk]),
            {"observacao_status": "Paciente solicitou remarcacao."},
        )

        self.assertRedirects(
            response,
            reverse("enfermagem:agendamento_create", args=[self.autorizacao.pk]) + "?cancelado=1",
        )

        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, "CANCELADO")
        self.assertIn("Cancelamento", agendamento.observacoes)

    def test_cancelar_agendamento_sem_observacao_nao_altera_status(self):
        data_agendamento = self._proximo_dia_util()
        agendamento = AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=self._data_storage(data_agendamento),
            hora_agendamento="09:00",
        )

        response = self.client.post(
            reverse("enfermagem:agendamento_cancelar", args=[agendamento.pk]),
            {"observacao_status": ""},
        )

        self.assertRedirects(
            response,
            reverse("enfermagem:agendamento_create", args=[self.autorizacao.pk]) + "?cancelamento_sem_observacao=1",
        )

        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, "AGENDADO")

    def test_realizar_agendamento_altera_status_para_realizado(self):
        data_agendamento = self._proximo_dia_util()
        agendamento = AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=self._data_storage(data_agendamento),
            hora_agendamento="09:00",
        )

        response = self.client.post(
            reverse("enfermagem:agendamento_realizar", args=[agendamento.pk]),
            {"observacao_status": "Procedimento realizado sem intercorrencias."},
        )

        self.assertRedirects(
            response,
            reverse("enfermagem:agendamento_create", args=[self.autorizacao.pk]) + "?realizado=1",
        )

        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, "REALIZADO")
        self.assertIn("Realização", agendamento.observacoes)

    def test_impede_excluir_autorizacao_com_agendamento_ativo(self):
        data_agendamento = self._proximo_dia_util()
        AgendaEnfermagem.objects.create(
            clinica=self.clinica,
            autorizacao=self.autorizacao,
            data_agendamento=self._data_storage(data_agendamento),
            hora_agendamento="09:00",
        )

        response = self.client.get(
            reverse("enfermagem:autorizacao_delete", args=[self.autorizacao.pk]),
        )

        self.assertRedirects(
            response,
            reverse("enfermagem:autorizacao_list") + "?exclusao_bloqueada=1",
        )
        self.assertTrue(Autorizacao.objects.filter(pk=self.autorizacao.pk).exists())
