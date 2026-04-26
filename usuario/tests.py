from django.test import TestCase
from django.urls import reverse

from usuario.models import Clinica, Colaborador


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
        self.admin_colaborador = Colaborador.objects.create_user(
            clinica=self.clinica,
            nome="Ana Admin",
            email="ana@clinica.com",
            password="Senha@123",
            papel=Colaborador.Papel.ADMIN,
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

    def test_login_api_autentica_colaborador(self):
        response = self.client.post(
            reverse("usuario:login_api"),
            {"email": self.admin_colaborador.email, "senha": "Senha@123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"status": "OK", "redirect_url": reverse("usuario:home")},
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.admin_colaborador.pk))
        self.assertEqual(
            self.client.session.get("_auth_user_backend"),
            "usuario.auth_backends.ColaboradorAuthBackend",
        )

    def test_login_api_tenta_colaborador_quando_clinica_com_mesmo_email_nao_bate_senha(self):
        clinica_secundaria = Clinica.objects.create_user(
            nome_fantasia="Clinica Secundaria",
            email="compartilhado@demo.com",
            password="SenhaClinica@123",
            plano=Clinica.Plano.BASICO,
        )
        colaborador = Colaborador.objects.create_user(
            clinica=clinica_secundaria,
            nome="Colaborador Compartilhado",
            email="compartilhado@demo.com",
            password="SenhaColab@123",
            papel=Colaborador.Papel.RECEPCAO,
        )

        response = self.client.post(
            reverse("usuario:login_api"),
            {"email": colaborador.email, "senha": "SenhaColab@123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(colaborador.pk))
        self.assertEqual(
            self.client.session.get("_auth_user_backend"),
            "usuario.auth_backends.ColaboradorAuthBackend",
        )

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

    def test_colaborador_admin_pode_gerenciar_equipe(self):
        self.client.force_login(
            self.admin_colaborador,
            backend="usuario.auth_backends.ColaboradorAuthBackend",
        )

        response = self.client.get(reverse("usuario:colaborador_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipe da Clínica")

    def test_colaborador_nao_admin_nao_pode_gerenciar_equipe(self):
        recepcao = Colaborador.objects.create_user(
            clinica=self.clinica,
            nome="Rita Recepcao",
            email="rita@clinica.com",
            password="Senha@123",
            papel=Colaborador.Papel.RECEPCAO,
        )
        self.client.force_login(
            recepcao,
            backend="usuario.auth_backends.ColaboradorAuthBackend",
        )

        response = self.client.get(reverse("usuario:colaborador_list"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("usuario:home"))

    def test_mensagem_de_bloqueio_diferencia_plano_de_perfil(self):
        recepcao = Colaborador.objects.create_user(
            clinica=self.clinica,
            nome="Perfil Restrito",
            email="restrito@clinica.com",
            password="Senha@123",
            papel=Colaborador.Papel.RECEPCAO,
        )
        self.client.force_login(
            recepcao,
            backend="usuario.auth_backends.ColaboradorAuthBackend",
        )

        response = self.client.get(reverse("financeiro:dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seu perfil não possui permissão para acessar o módulo Financeiro.")

    def test_plano_profissional_limita_a_cinco_colaboradores_ativos(self):
        for indice in range(2, 6):
            Colaborador.objects.create_user(
                clinica=self.clinica,
                nome=f"Colaborador {indice}",
                email=f"colaborador{indice}@clinica.com",
                password="Senha@123",
                papel=Colaborador.Papel.RECEPCAO,
            )
        self.client.force_login(self.clinica)

        response = self.client.post(
            reverse("usuario:colaborador_create"),
            {
                "nome": "Carla",
                "email": "carla@clinica.com",
                "papel": Colaborador.Papel.FINANCEIRO,
                "status": "on",
                "reseta_senha": "",
                "password": "Senha@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 colaboradores ativos")
        self.assertFalse(Colaborador.objects.filter(email="carla@clinica.com").exists())

    def test_plano_basico_nao_tem_limite_de_colaboradores(self):
        clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Basica Colaboradores",
            email="basica2@clinica.com",
            password="Senha@123",
            plano=Clinica.Plano.BASICO,
        )
        for indice in range(3):
            Colaborador.objects.create_user(
                clinica=clinica,
                nome=f"Colaborador {indice}",
                email=f"col{indice}@basica.com",
                password="Senha@123",
                papel=Colaborador.Papel.RECEPCAO,
            )

        self.assertEqual(clinica.colaboradores_ativos().count(), 3)

    def test_perfil_medico_tem_acesso_apenas_a_consultas(self):
        medico = Colaborador.objects.create_user(
            clinica=self.clinica,
            nome="Medico Demo",
            email="medico@clinica.com",
            password="Senha@123",
            papel=Colaborador.Papel.MEDICO,
        )

        self.assertTrue(medico.modulo_disponivel("agenda"))
        self.assertFalse(medico.modulo_disponivel("pacientes"))
        self.assertFalse(medico.modulo_disponivel("configuracoes"))
        self.assertFalse(medico.modulo_disponivel("financeiro"))

    def test_perfil_recepcao_tem_acessos_padrao(self):
        recepcao = Colaborador.objects.create_user(
            clinica=self.clinica,
            nome="Recepcao Demo",
            email="recepcao@clinica.com",
            password="Senha@123",
            papel=Colaborador.Papel.RECEPCAO,
        )

        self.assertTrue(recepcao.modulo_disponivel("pacientes"))
        self.assertTrue(recepcao.modulo_disponivel("agenda"))
        self.assertTrue(recepcao.modulo_disponivel("configuracoes"))
        self.assertFalse(recepcao.modulo_disponivel("financeiro"))

    def test_cadastro_colaborador_permite_restringir_modulos_do_papel(self):
        self.client.force_login(self.clinica)

        response = self.client.post(
            reverse("usuario:colaborador_create"),
            {
                "nome": "Julia Recepcao",
                "email": "julia@clinica.com",
                "papel": Colaborador.Papel.RECEPCAO,
                "status": "on",
                "password": "Senha@123",
                "modulos_permitidos": ["agenda"],
            },
        )

        self.assertEqual(response.status_code, 302)
        colaborador = Colaborador.objects.get(email="julia@clinica.com")
        self.assertEqual(colaborador.modulos_permitidos, ["agenda"])
        self.assertTrue(colaborador.modulo_disponivel("agenda"))
        self.assertFalse(colaborador.modulo_disponivel("pacientes"))
        self.assertFalse(colaborador.modulo_disponivel("configuracoes"))

    def test_cadastro_colaborador_permite_liberar_modulo_fora_do_padrao_do_papel(self):
        self.client.force_login(self.clinica)

        response = self.client.post(
            reverse("usuario:colaborador_create"),
            {
                "nome": "Dr Modulos",
                "email": "drmodulos@clinica.com",
                "papel": Colaborador.Papel.MEDICO,
                "status": "on",
                "password": "Senha@123",
                "modulos_permitidos": ["agenda", "pacientes", "configuracoes"],
            },
        )

        self.assertEqual(response.status_code, 302)
        colaborador = Colaborador.objects.get(email="drmodulos@clinica.com")
        self.assertTrue(colaborador.modulo_disponivel("agenda"))
        self.assertTrue(colaborador.modulo_disponivel("pacientes"))
        self.assertTrue(colaborador.modulo_disponivel("configuracoes"))

    def test_cadastro_colaborador_permite_salvar_sem_modulos_liberados(self):
        self.client.force_login(self.clinica)

        response = self.client.post(
            reverse("usuario:colaborador_create"),
            {
                "nome": "Sem Modulos",
                "email": "semmodulos@clinica.com",
                "papel": Colaborador.Papel.RECEPCAO,
                "status": "on",
                "password": "Senha@123",
            },
        )

        self.assertEqual(response.status_code, 302)
        colaborador = Colaborador.objects.get(email="semmodulos@clinica.com")
        self.assertEqual(colaborador.modulos_permitidos, [])
        self.assertFalse(colaborador.modulo_disponivel("agenda"))
        self.assertFalse(colaborador.modulo_disponivel("pacientes"))
