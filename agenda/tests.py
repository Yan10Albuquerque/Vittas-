from datetime import date, datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agenda
from base.models import Convenio, Especialidade, StatusAgendamento, TipoConsulta
from medico.models import Medico, MedicoAgenda, MedicoEspecialidade
from paciente.models import Paciente
from usuario.models import Clinica


class AgendaModuleTests(TestCase):
    def setUp(self):
        self.clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Agenda",
            email="agenda@clinica.com",
            password="123456",
            plano=Clinica.Plano.PROFISSIONAL,
        )
        self.client.force_login(self.clinica)

        self.convenio = Convenio.objects.create(clinica=self.clinica, nome="Particular")
        self.especialidade = Especialidade.objects.create(clinica=self.clinica, descricao="Cardiologia")
        self.tipo_consulta = TipoConsulta.objects.create(clinica=self.clinica, descricao="Consulta")
        self.status_agendado = StatusAgendamento.objects.get(
            clinica=self.clinica,
            descricao="Agendado",
        )
        self.status_em_andamento = StatusAgendamento.objects.get(
            clinica=self.clinica,
            descricao="Em Andamento",
        )
        self.status_finalizado = StatusAgendamento.objects.get(
            clinica=self.clinica,
            descricao="Finalizado",
        )
        self.medico = Medico.objects.create(
            clinica=self.clinica,
            crm="12345",
            nome="Dr. Agenda",
        )
        MedicoEspecialidade.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            especialidade=self.especialidade,
        )
        MedicoAgenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            hora=time(8, 0),
        )
        self.paciente = Paciente.objects.create(
            clinica=self.clinica,
            cpf="12345678900",
            nome="Paciente Agenda",
            celular="11999999999",
            nascimento=date(1990, 1, 1),
            convenio=self.convenio,
        )

    def _data_futura(self):
        return timezone.localdate() + timezone.timedelta(days=1)

    def test_agenda_consultas_view_renderiza(self):
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=self._data_futura(),
            hora=time(8, 0),
            status=Agenda.Status.AGENDADO,
        )

        response = self.client.get(
            reverse("agenda:agenda_consultas"),
            {"cod_medico": self.medico.pk, "data_agenda": self._data_futura().isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agenda de Consultas e Exames")
        self.assertContains(response, "Prontuário")
        self.assertContains(response, "Cobrança")
        self.assertContains(response, "Iniciar")

    def test_agenda_api_cria_horarios_a_partir_da_agenda_do_medico(self):
        response = self.client.post(
            reverse("agenda:agenda_api"),
            {
                "funcao": "criar_agenda",
                "cod_medico": self.medico.pk,
                "data_agenda": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Agenda.objects.filter(
                clinica=self.clinica,
                medico=self.medico,
                data=timezone.localdate(),
                hora=time(8, 0),
            ).exists()
        )

    def test_agenda_api_salva_consulta(self):
        agenda = Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            data=self._data_futura(),
            hora=time(9, 0),
            status=Agenda.Status.DISPONIVEL,
        )

        response = self.client.post(
            reverse("agenda:agenda_api"),
            {
                "funcao": "salvar_consulta",
                "cod_agenda": agenda.pk,
                "cod_paciente": self.paciente.pk,
                "convenio_consulta": self.convenio.pk,
                "cod_tipo_consulta": self.tipo_consulta.pk,
                "cod_especialidade": self.especialidade.pk,
                "cod_status_agendamento": self.status_agendado.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        agenda.refresh_from_db()
        self.assertEqual(agenda.paciente, self.paciente)
        self.assertEqual(agenda.status, Agenda.Status.AGENDADO)
        self.assertEqual(agenda.status_agendamento, self.status_agendado)

    def test_atualiza_paciente_move_agenda_para_em_atendimento_sem_id_fixo(self):
        agenda = Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=self._data_futura(),
            hora=time(10, 0),
            status=Agenda.Status.AGENDADO,
        )

        response = self.client.post(
            reverse("paciente:paciente_api"),
            {
                "funcao": "atualiza_paciente",
                "cod_paciente": self.paciente.pk,
                "cpf": self.paciente.cpf,
                "nome": self.paciente.nome,
                "celular": self.paciente.celular,
                "email": "paciente@teste.com",
                "documento": "RG123",
                "nascimento": self.paciente.nascimento.isoformat(),
                "sexo": "FEMININO",
                "profissao": "Analista",
                "cep": "01001000",
                "endereco": "Rua Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "convenio": self.convenio.pk,
                "num_carteira": "ABC123",
                "cod_agenda": agenda.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        agenda.refresh_from_db()
        self.assertEqual(agenda.status_agendamento, self.status_agendado)

    def test_agenda_muda_para_em_andamento_durante_o_periodo_do_atendimento(self):
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(10, 0),
            status=Agenda.Status.AGENDADO,
        )
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            data=timezone.localdate(),
            hora=time(10, 30),
            status=Agenda.Status.DISPONIVEL,
        )

        now = timezone.make_aware(datetime.combine(timezone.localdate(), time(10, 15)))
        with patch("agenda.services.timezone.localtime", return_value=now):
            response = self.client.get(
                reverse("agenda:agenda_consultas"),
                {"cod_medico": self.medico.pk, "data_agenda": timezone.localdate().isoformat()},
            )

        self.assertEqual(response.status_code, 200)
        consulta = Agenda.objects.get(clinica=self.clinica, medico=self.medico, hora=time(10, 0))
        self.assertEqual(consulta.status_agendamento, self.status_em_andamento)

    def test_agenda_muda_para_finalizado_apos_o_periodo_do_atendimento(self):
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(10, 0),
            status=Agenda.Status.AGENDADO,
        )
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            data=timezone.localdate(),
            hora=time(10, 30),
            status=Agenda.Status.DISPONIVEL,
        )

        now = timezone.make_aware(datetime.combine(timezone.localdate(), time(10, 35)))
        with patch("agenda.services.timezone.localtime", return_value=now):
            response = self.client.get(
                reverse("agenda:agenda_consultas"),
                {"cod_medico": self.medico.pk, "data_agenda": timezone.localdate().isoformat()},
            )

        self.assertEqual(response.status_code, 200)
        consulta = Agenda.objects.get(clinica=self.clinica, medico=self.medico, hora=time(10, 0))
        self.assertEqual(consulta.status_agendamento, self.status_finalizado)

    def test_fluxo_agenda_inicia_e_finaliza_atendimento(self):
        agenda = Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(11, 0),
            status=Agenda.Status.AGENDADO,
        )

        iniciar_response = self.client.post(
            reverse("agenda:agenda_iniciar_atendimento", args=[agenda.pk]),
            {"next": reverse("agenda:agenda_consultas")},
        )

        self.assertEqual(iniciar_response.status_code, 302)
        agenda.refresh_from_db()
        self.assertEqual(agenda.status_agendamento, self.status_em_andamento)

        finalizar_response = self.client.post(
            reverse("agenda:agenda_finalizar_atendimento", args=[agenda.pk]),
            {"next": reverse("agenda:agenda_consultas")},
        )

        self.assertEqual(finalizar_response.status_code, 302)
        agenda.refresh_from_db()
        self.assertEqual(agenda.status_agendamento, self.status_finalizado)

    def test_inicio_manual_nao_regride_para_agendado_ao_recarregar_agenda(self):
        agenda = Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(11, 0),
            status=Agenda.Status.AGENDADO,
        )
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            data=timezone.localdate(),
            hora=time(11, 30),
            status=Agenda.Status.DISPONIVEL,
        )

        self.client.post(reverse("agenda:agenda_iniciar_atendimento", args=[agenda.pk]))

        now = timezone.make_aware(datetime.combine(timezone.localdate(), time(10, 45)))
        with patch("agenda.services.timezone.localtime", return_value=now):
            response = self.client.get(
                reverse("agenda:agenda_consultas"),
                {"cod_medico": self.medico.pk, "data_agenda": timezone.localdate().isoformat()},
            )

        self.assertEqual(response.status_code, 200)
        agenda.refresh_from_db()
        self.assertEqual(agenda.status_agendamento, self.status_em_andamento)

    def test_finalizacao_manual_nao_regride_ao_recarregar_agenda(self):
        agenda = Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            paciente=self.paciente,
            convenio=self.convenio,
            tipo_consulta=self.tipo_consulta,
            especialidade=self.especialidade,
            status_agendamento=self.status_agendado,
            data=timezone.localdate(),
            hora=time(11, 0),
            status=Agenda.Status.AGENDADO,
        )
        Agenda.objects.create(
            clinica=self.clinica,
            medico=self.medico,
            data=timezone.localdate(),
            hora=time(11, 30),
            status=Agenda.Status.DISPONIVEL,
        )

        self.client.post(reverse("agenda:agenda_iniciar_atendimento", args=[agenda.pk]))
        self.client.post(reverse("agenda:agenda_finalizar_atendimento", args=[agenda.pk]))

        now = timezone.make_aware(datetime.combine(timezone.localdate(), time(11, 5)))
        with patch("agenda.services.timezone.localtime", return_value=now):
            response = self.client.get(
                reverse("agenda:agenda_consultas"),
                {"cod_medico": self.medico.pk, "data_agenda": timezone.localdate().isoformat()},
            )

        self.assertEqual(response.status_code, 200)
        agenda.refresh_from_db()
        self.assertEqual(agenda.status_agendamento, self.status_finalizado)
