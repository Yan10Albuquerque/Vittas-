from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import FormaPagamento
from financeiro.models import CategoriaFinanceira, LancamentoFinanceiro
from financeiro.services import sincronizar_lancamento_vacina
from paciente.models import Paciente, PacienteVacina
from usuario.models import Clinica


class FinanceiroModuleTest(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Financeira",
            email="financeiro@clinica.com",
            password="123456",
            plano=Clinica.Plano.PROFISSIONAL,
        )
        self.client.force_login(self.clinica)
        self.categoria = CategoriaFinanceira.objects.create(
            clinica=self.clinica,
            descricao="Consultas",
            tipo=CategoriaFinanceira.Tipo.RECEITA,
            cor="badge-primary",
        )

    def test_dashboard_financeiro_responde(self):
        response = self.client.get(reverse("financeiro:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_lancamento_atualiza_status_para_atrasado(self):
        lancamento = LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            categoria=self.categoria,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            descricao="Consulta Particular",
            nome_cliente="Cliente Teste",
            competencia=timezone.localdate().replace(day=1),
            data_vencimento=timezone.localdate() - timezone.timedelta(days=5),
            valor=Decimal("150.00"),
        )
        self.assertEqual(lancamento.status, LancamentoFinanceiro.Status.ATRASADO)

    def test_sincroniza_lancamento_de_vacina(self):
        forma_pagamento = FormaPagamento.objects.create(
            clinica=self.clinica,
            descricao="PIX",
        )
        paciente = Paciente.objects.create(
            clinica=self.clinica,
            cpf="11122233344",
            nome="Paciente Financeiro",
            celular="11999999999",
            nascimento="1995-05-05",
        )
        vacina = PacienteVacina.objects.create(
            clinica=self.clinica,
            paciente=paciente,
            data_aplicacao=timezone.localdate(),
            descricao_vacina="Influenza",
            forma_pagamento=forma_pagamento,
            valor=Decimal("89.90"),
        )

        lancamento = sincronizar_lancamento_vacina(vacina)

        self.assertIsNotNone(lancamento)
        self.assertEqual(lancamento.vacina, vacina)
        self.assertEqual(lancamento.status, LancamentoFinanceiro.Status.PAGO)
        self.assertEqual(lancamento.valor, Decimal("89.90"))
