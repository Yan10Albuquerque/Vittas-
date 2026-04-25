from django.test import TestCase
from django.urls import reverse

from usuario.models import Clinica


class ClinicaAuthFlowTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Auth",
            email="clinica@auth.com",
            password="Senha@123",
            plano=Clinica.Plano.PROFISSIONAL,
        )
        self.clinica_expirada = Clinica.objects.create_user(
            nome_fantasia="Clinica Expirada",
            email="expirada@clinica.com",
            password="Senha@123",
            plano=Clinica.Plano.PROFISSIONAL,
            reseta_senha=True,
        )
        self.clinica_inativa = Clinica.objects.create_user(
            nome_fantasia="Clinica Inativa",
            email="inativa@clinica.com",
            password="Senha@123",
            plano=Clinica.Plano.PROFISSIONAL,
            status=False,
        )

    def test_login_api_recusa_clinica_inativa(self):
        response = self.client.post(
            reverse("usuario:login_api"),
            {"email": self.clinica_inativa.email, "senha": "Senha@123"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"status": "ERROR", "message": "Dados de acesso inválidos."},
        )

    def test_alterar_senha_api_usa_clinica_pendente_na_sessao(self):
        login_response = self.client.post(
            reverse("usuario:login_api"),
            {"email": self.clinica_expirada.email, "senha": "Senha@123"},
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertJSONEqual(login_response.content, {"status": "SENHA_EXPIRADA"})
        self.assertEqual(
            self.client.session.get("password_reset_user_id"),
            self.clinica_expirada.pk,
        )

        alterar_response = self.client.post(
            reverse("usuario:alterar_senha_api"),
            {
                "senha_atual": "Senha@123",
                "nova_senha": "NovaSenha@123",
            },
        )

        self.assertEqual(alterar_response.status_code, 200)
        self.clinica_expirada.refresh_from_db()
        self.assertFalse(self.clinica_expirada.reseta_senha)
        self.assertTrue(self.clinica_expirada.check_password("NovaSenha@123"))
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.clinica_expirada.pk),
        )
        self.assertIsNone(self.client.session.get("password_reset_user_id"))

    def test_logout_api_encerra_sessao(self):
        self.client.force_login(self.clinica)

        response = self.client.post(reverse("usuario:logout_api"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"status": "OK", "redirect_url": reverse("usuario:login")},
        )
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_paginas_principais_renderizam_para_clinica_logada(self):
        self.client.force_login(self.clinica)

        home_response = self.client.get(reverse("usuario:home"))
        perfil_response = self.client.get(reverse("usuario:clinica_perfil"))

        self.assertEqual(home_response.status_code, 200)
        self.assertEqual(perfil_response.status_code, 200)

    def test_plano_basico_libera_todos_os_modulos(self):
        clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Basica",
            email="basica@clinica.com",
            password="Senha@123",
            plano=Clinica.Plano.BASICO,
        )

        self.assertTrue(clinica.modulo_disponivel("pacientes"))
        self.assertTrue(clinica.modulo_disponivel("agenda"))
        self.assertTrue(clinica.modulo_disponivel("cadastros"))
        self.assertTrue(clinica.modulo_disponivel("configuracoes"))
        self.assertTrue(clinica.modulo_disponivel("financeiro"))
        self.assertTrue(clinica.modulo_disponivel("enfermagem"))

    def test_plano_profissional_nao_libera_enfermagem(self):
        clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Profissional",
            email="profissional@clinica.com",
            password="Senha@123",
            plano=Clinica.Plano.PROFISSIONAL,
        )

        self.assertTrue(clinica.modulo_disponivel("pacientes"))
        self.assertTrue(clinica.modulo_disponivel("agenda"))
        self.assertTrue(clinica.modulo_disponivel("cadastros"))
        self.assertTrue(clinica.modulo_disponivel("configuracoes"))
        self.assertTrue(clinica.modulo_disponivel("financeiro"))
        self.assertFalse(clinica.modulo_disponivel("enfermagem"))

    def test_plano_pro_legado_equivale_a_enterprise(self):
        clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Legada",
            email="legada@clinica.com",
            password="Senha@123",
            plano="PRO",
        )

        self.assertEqual(clinica.plano_normalizado, Clinica.Plano.ENTERPRISE)
        self.assertTrue(clinica.modulo_disponivel("enfermagem"))
        self.assertTrue(clinica.modulo_disponivel("financeiro"))
