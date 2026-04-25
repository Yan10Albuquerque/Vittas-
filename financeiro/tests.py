from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import Convenio, FormaPagamento
from financeiro.forms import LancamentoFinanceiroForm
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
        self.factory = RequestFactory()
        self.categoria = CategoriaFinanceira.objects.create(
            clinica=self.clinica,
            descricao="Consultas",
            tipo=CategoriaFinanceira.Tipo.RECEITA,
            cor="badge-primary",
        )
        self.forma_pagamento = FormaPagamento.objects.create(
            clinica=self.clinica,
            descricao="PIX",
        )
        self.paciente = Paciente.objects.create(
            clinica=self.clinica,
            cpf="11122233344",
            nome="Paciente Financeiro",
            celular="11999999999",
            nascimento="1995-05-05",
        )
        self.convenio = Convenio.objects.create(
            clinica=self.clinica,
            nome="Convenio Teste",
            status=True,
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
        self.assertEqual(lancamento.status_badge_class, "badge-error text-error-content")

    def test_sincroniza_lancamento_de_vacina(self):
        vacina = PacienteVacina.objects.create(
            clinica=self.clinica,
            paciente=self.paciente,
            data_aplicacao=timezone.localdate(),
            descricao_vacina="Influenza",
            forma_pagamento=self.forma_pagamento,
            valor=Decimal("89.90"),
        )

        lancamento = sincronizar_lancamento_vacina(vacina)

        self.assertIsNotNone(lancamento)
        self.assertEqual(lancamento.vacina, vacina)
        self.assertEqual(lancamento.status, LancamentoFinanceiro.Status.PAGO)
        self.assertEqual(lancamento.valor, Decimal("89.90"))

    def test_baixar_lancamento_atrasado_registra_pagamento_parcial(self):
        lancamento = LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            categoria=self.categoria,
            paciente=self.paciente,
            forma_pagamento=self.forma_pagamento,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            descricao="Consulta atrasada",
            data_lancamento=timezone.localdate() - timezone.timedelta(days=10),
            competencia=timezone.localdate().replace(day=1),
            data_vencimento=timezone.localdate() - timezone.timedelta(days=5),
            valor=Decimal("150.00"),
        )

        response = self.client.post(
            reverse("financeiro:lancamento_baixar", args=[lancamento.pk]),
            {
                "valor_pago": "50.00",
                "data_pagamento": timezone.localdate().isoformat(),
                "next": reverse("financeiro:lancamento_list"),
            },
        )

        self.assertEqual(response.status_code, 302)
        lancamento.refresh_from_db()
        self.assertEqual(lancamento.valor_recebido, Decimal("50.00"))
        self.assertEqual(lancamento.status, LancamentoFinanceiro.Status.PARCIAL)

    def test_formulario_edicao_mantem_relacionamentos_inativos(self):
        self.categoria.status = False
        self.categoria.save(update_fields=["status"])
        self.forma_pagamento.status = False
        self.forma_pagamento.save(update_fields=["status"])
        self.paciente.status = False
        self.paciente.save(update_fields=["status"])
        self.convenio.status = False
        self.convenio.save(update_fields=["status"])

        lancamento = LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            categoria=self.categoria,
            paciente=self.paciente,
            convenio=self.convenio,
            forma_pagamento=self.forma_pagamento,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            descricao="Receita com vinculos inativos",
            data_lancamento=timezone.localdate(),
            competencia=timezone.localdate(),
            data_vencimento=timezone.localdate(),
            valor=Decimal("90.00"),
        )

        request = self.factory.get(reverse("financeiro:lancamento_update", args=[lancamento.pk]))
        request.user = self.clinica
        form = LancamentoFinanceiroForm(instance=lancamento, request=request)

        self.assertIn(self.categoria, form.fields["categoria"].queryset)
        self.assertIn(self.paciente, form.fields["paciente"].queryset)
        self.assertIn(self.convenio, form.fields["convenio"].queryset)
        self.assertIn(self.forma_pagamento, form.fields["forma_pagamento"].queryset)

    def test_formulario_edicao_renderiza_datas_em_formato_html_date(self):
        lancamento = LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            categoria=self.categoria,
            paciente=self.paciente,
            forma_pagamento=self.forma_pagamento,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            descricao="Receita com datas",
            data_lancamento=timezone.localdate(),
            competencia=timezone.localdate(),
            data_vencimento=timezone.localdate() + timezone.timedelta(days=7),
            data_pagamento=timezone.localdate(),
            valor=Decimal("120.00"),
            valor_recebido=Decimal("120.00"),
        )

        response = self.client.get(reverse("financeiro:lancamento_update", args=[lancamento.pk]))

        self.assertContains(response, f'name="data_lancamento" value="{lancamento.data_lancamento.isoformat()}"')
        self.assertContains(response, f'name="competencia" value="{lancamento.competencia.isoformat()}"')
        self.assertContains(response, f'name="data_vencimento" value="{lancamento.data_vencimento.isoformat()}"')
        self.assertContains(response, f'name="data_pagamento" value="{lancamento.data_pagamento.isoformat()}"')

    def test_lista_expoe_valor_aberto_sem_quebrar_modal_de_baixa(self):
        lancamento = LancamentoFinanceiro.objects.create(
            clinica=self.clinica,
            categoria=self.categoria,
            paciente=self.paciente,
            tipo=LancamentoFinanceiro.Tipo.RECEITA,
            descricao="Lançamento atrasado para modal",
            data_lancamento=timezone.localdate() - timezone.timedelta(days=10),
            competencia=timezone.localdate().replace(day=1),
            data_vencimento=timezone.localdate() - timezone.timedelta(days=2),
            valor=Decimal("150.00"),
        )

        response = self.client.get(reverse("financeiro:lancamento_list"))

        self.assertContains(response, 'data-valor-aberto="150,00"')
        self.assertContains(response, "normalizarValorFinanceiro")
