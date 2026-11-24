from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from base.models import Convenio
from paciente.models import Paciente
from usuario.models import Clinica, Colaborador
from usuario.visitante import VISITANTE_EMAIL, VISITANTE_SESSION_KEY


class ClinicaAuthFlowTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Auth",
            email="clinica@auth.com",
            password="Senha@123",
        )
        self.clinica_expirada = Clinica.objects.create_user(
            nome_fantasia="Clinica Expirada",
            email="expirada@clinica.com",
            password="Senha@123",
            reseta_senha=True,
        )
        self.clinica_inativa = Clinica.objects.create_user(
            nome_fantasia="Clinica Inativa",
            email="inativa@clinica.com",
            password="Senha@123",
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

    def test_clinica_tem_acesso_a_todos_os_modulos(self):
        for modulo in ("pacientes", "agenda", "cadastros", "configuracoes", "financeiro", "enfermagem"):
            self.assertTrue(self.clinica.modulo_disponivel(modulo))

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

    def test_mensagem_de_bloqueio_por_perfil(self):
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

    def test_clinica_nao_tem_limite_de_colaboradores(self):
        for indice in range(2, 8):
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

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Colaborador.objects.filter(email="carla@clinica.com").exists())

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


class SeedDemoDataCommandTests(TestCase):
    def _run_seed(self, **options):
        call_command("seed_demo_data", stdout=StringIO(), **options)

    def test_cria_clinica_informada_quando_nao_existe(self):
        Clinica.objects.create_user(
            nome_fantasia="Clinica Existente",
            email="existente@clinica.com",
            password="Senha@123",
        )

        self._run_seed(clinic_email="demo@vittas.com", create_clinic_if_missing=True)

        clinica = Clinica.objects.get(email="demo@vittas.com")
        self.assertTrue(clinica.check_password("Demo@123"))
        self.assertTrue(clinica.pacientes.exists())
        self.assertFalse(Clinica.objects.get(email="existente@clinica.com").pacientes.exists())

    def test_nao_cria_clinica_informada_sem_flag(self):
        self._run_seed(clinic_email="naoexiste@vittas.com")

        self.assertFalse(Clinica.objects.filter(email="naoexiste@vittas.com").exists())


class ModoVisitanteTests(TestCase):
    def _entrar_como_visitante(self):
        return self.client.post(reverse("usuario:visitante"))

    def test_login_exibe_botao_de_visitante(self):
        response = self.client.get(reverse("usuario:login"))

        self.assertContains(response, "Entrar como visitante")

    def test_entrar_como_visitante_cria_clinica_demo_populada(self):
        response = self._entrar_como_visitante()

        self.assertRedirects(response, reverse("usuario:home"))
        self.assertTrue(self.client.session.get(VISITANTE_SESSION_KEY))
        clinica = Clinica.objects.get(email=VISITANTE_EMAIL)
        self.assertEqual(int(self.client.session["_auth_user_id"]), clinica.pk)
        self.assertTrue(clinica.pacientes.exists())

        home = self.client.get(reverse("usuario:home"))
        self.assertContains(home, "Modo visitante.")

    def test_clinica_visitante_nao_aceita_login_por_senha(self):
        self._entrar_como_visitante()
        self.client.logout()
        clinica = Clinica.objects.get(email=VISITANTE_EMAIL)

        self.assertFalse(clinica.has_usable_password())
        self.assertFalse(
            any(colaborador.has_usable_password() for colaborador in clinica.colaboradores.all())
        )
        response = self.client.post(
            reverse("usuario:login_api"),
            {"email": "demo1.%d@vittas.com" % clinica.pk, "senha": "Demo@123"},
        )
        self.assertEqual(response.status_code, 400)

    def test_visitante_navega_pelos_modulos(self):
        self._entrar_como_visitante()

        for nome_url in (
            "usuario:home",
            "agenda:agenda_consultas",
            "paciente:paciente_list",
            "financeiro:dashboard",
            "enfermagem:autorizacao_list",
            "usuario:colaborador_list",
        ):
            with self.subTest(nome_url=nome_url):
                self.assertEqual(self.client.get(reverse(nome_url)).status_code, 200)

    def test_visitante_nao_altera_dados_via_formulario(self):
        self._entrar_como_visitante()
        total_antes = Paciente.objects.count()

        response = self.client.post(
            reverse("paciente:paciente_create"),
            {"nome": "Paciente Visitante"},
            HTTP_ACCEPT="text/html",
            follow=True,
        )

        self.assertEqual(Paciente.objects.count(), total_antes)
        self.assertContains(response, "Modo visitante: esta é uma demonstração somente leitura")

    def test_visitante_nao_altera_dados_via_ajax(self):
        self._entrar_como_visitante()
        convenio = Convenio.objects.filter(clinica__email=VISITANTE_EMAIL).first()

        response = self.client.post(
            reverse("base:convenio_delete", args=[convenio.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.json()["modo_visitante"])
        self.assertTrue(Convenio.objects.filter(pk=convenio.pk).exists())

    def test_visitante_pode_consultar_dados_por_post_de_leitura(self):
        self._entrar_como_visitante()
        paciente = Paciente.objects.filter(clinica__email=VISITANTE_EMAIL).first()

        response = self.client.post(
            reverse("paciente:paciente_api"),
            {"funcao": "buscar_dados", "cod_paciente": paciente.pk},
        )

        self.assertNotEqual(response.status_code, 403)

    def test_visitante_pode_sair(self):
        self._entrar_como_visitante()

        response = self.client.post(reverse("usuario:logout_api"), HTTP_ACCEPT="text/html")

        self.assertRedirects(response, reverse("usuario:login"))
        self.assertNotIn(VISITANTE_SESSION_KEY, self.client.session)

    @override_settings(MODO_VISITANTE_HABILITADO=False)
    def test_modo_visitante_desabilitado(self):
        self.assertNotContains(self.client.get(reverse("usuario:login")), "Entrar como visitante")
        self.assertEqual(self._entrar_como_visitante().status_code, 404)
