from datetime import date, time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agenda
from base.models import Convenio, StatusAgendamento
from financeiro.models import CategoriaFinanceira, LancamentoFinanceiro
from medico.models import Medico
from paciente.models import Paciente
from usuario.models import Clinica


class PacienteModuleTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Paciente",
            email="paciente@clinica.com",
            password="123456",
            plano=Clinica.Plano.PROFISSIONAL,
        )
        self.client.force_login(self.clinica)

        self.convenio = Convenio.objects.create(clinica=self.clinica, nome="Particular")
        self.status_agendado = StatusAgendamento.objects.get(
            clinica=self.clinica,
            descricao="Agendado",
        )
        self.medico = Medico.objects.create(
            clinica=self.clinica,
            crm="12345",
            nome="Dra. Prontuario",
        )
        self.categoria = CategoriaFinanceira.objects.create(
            clinica=self.clinica,
            descricao="Consulta",
            tipo=CategoriaFinanceira.Tipo.RECEITA,
            cor="badge-primary",
        )
        self.paciente = Paciente.objects.create(
            clinica=self.clinica,
            cpf="12345678900",
            nome="Paciente Teste",
            celular="11999999999",
            nascimento=date(1990, 1, 1),
            convenio=self.convenio,
        )

    def test_tela_edicao_exibe_apenas_aba_prontuario(self):
        response = self.client.get(reverse("paciente:paciente_update", args=[self.paciente.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prontuário")
        self.assertNotContains(response, "activeTab === 'vacinas'")
        self.assertNotContains(response, "activeTab === 'medicacao'")
        self.assertNotContains(response, "activeTab === 'consultas'")

    def test_prontuario_exibe_linha_do_tempo_e_persiste_anotacao(self):
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(9, 0),
            status=Agenda.Status.AGENDADO,
        )
        LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            paciente=self.paciente,
            categoria=self.categoria,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            origem=LancamentoFinanceiro.Origem.CONSULTA,
            descricao="Consulta cardiologica",
            nome_cliente=self.paciente.nome,
            data_lancamento=timezone.localdate(),
            competencia=timezone.localdate(),
            data_vencimento=timezone.localdate(),
            valor=Decimal("150.00"),
        )

        salvar_response = self.client.post(
            reverse("paciente:paciente_update", args=[self.paciente.pk]),
            {
                "salvar_prontuario": "1",
                "prontuario": "Paciente evoluindo bem, sem intercorrencias.",
            },
        )

        self.assertEqual(salvar_response.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.prontuario, "Paciente evoluindo bem, sem intercorrencias.")

        response = self.client.get(reverse("paciente:paciente_update", args=[self.paciente.pk]))
        self.assertContains(response, "Linha do tempo do paciente")
        self.assertContains(response, "Atendimento agendado")
        self.assertContains(response, "Consulta cardiologica")
        self.assertContains(response, "Paciente evoluindo bem, sem intercorrencias.")
