from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from agenda.models import Agenda
from base.models import Convenio, Especialidade, FormaPagamento, StatusAgendamento, TipoConsulta
from base.statuses import ensure_default_status_agendamento
from financeiro.models import CategoriaFinanceira, LancamentoFinanceiro
from medico.models import Medico, MedicoAgenda, MedicoEspecialidade
from paciente.models import Paciente, PacienteVacina
from usuario.models import Clinica, Colaborador


DEMO_PASSWORD = "Demo@123"
DEMO_ACTOR = "seed_demo_data"


class Command(BaseCommand):
    help = "Insere dados fictícios para demonstração do sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clinic-email",
            dest="clinic_email",
            help="Email da clínica que receberá os dados fictícios.",
        )
        parser.add_argument(
            "--create-clinic-if-missing",
            action="store_true",
            dest="create_clinic_if_missing",
            help="Cria uma clínica de demonstração caso nenhuma clínica ativa seja encontrada.",
        )

    def handle(self, *args, **options):
        clinics = self._get_target_clinics(
            clinic_email=options.get("clinic_email"),
            create_clinic_if_missing=options.get("create_clinic_if_missing", False),
        )
        if not clinics:
            self.stdout.write(self.style.WARNING("Nenhuma clínica ativa encontrada para popular."))
            return

        with transaction.atomic():
            for clinica in clinics:
                resumo = self._seed_clinic(clinica)
                self.stdout.write(self.style.SUCCESS(self._format_summary(clinica, resumo)))

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed finalizado. Senha padrão dos acessos de demonstração: {DEMO_PASSWORD}"
            )
        )

    def _get_target_clinics(self, clinic_email=None, create_clinic_if_missing=False):
        if clinic_email:
            clinica = Clinica.objects.filter(email__iexact=clinic_email, status=True).first()
            return [clinica] if clinica else []

        clinicas = list(Clinica.objects.filter(status=True).order_by("id"))
        if clinicas:
            return clinicas

        if not create_clinic_if_missing:
            return []

        clinica = Clinica.objects.create_user(
            nome_fantasia="Clinica Demo Vittas",
            email="demo@vittas.com",
            password=DEMO_PASSWORD,
            plano=Clinica.Plano.ENTERPRISE,
            telefone="(11) 4000-1000",
            uscad=DEMO_ACTOR,
            usalt=DEMO_ACTOR,
        )
        return [clinica]

    def _seed_clinic(self, clinica):
        hoje = timezone.localdate()
        amanha = hoje + timedelta(days=1)
        ontem = hoje - timedelta(days=1)

        ensure_default_status_agendamento(clinica, actor_name=DEMO_ACTOR)
        status_agendado = StatusAgendamento.objects.get(clinica=clinica, descricao="Agendado")
        status_em_andamento = StatusAgendamento.objects.get(clinica=clinica, descricao="Em Andamento")
        status_finalizado = StatusAgendamento.objects.get(clinica=clinica, descricao="Finalizado")

        especialidades = {
            descricao: self._get_or_create(
                Especialidade,
                clinica=clinica,
                descricao=descricao,
                defaults={"status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            )
            for descricao in ["Dermatologia", "Cardiologia", "Clínica Geral"]
        }
        convenios = {
            nome: self._get_or_create(
                Convenio,
                clinica=clinica,
                nome=nome,
                defaults={
                    "status": True,
                    "telefone": "(11) 3000-2000",
                    "email": f"{self._slug(nome)}@demo.com",
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )
            for nome in ["Particular", "Unimed", "Bradesco Saúde"]
        }
        formas_pagamento = {
            descricao: self._get_or_create(
                FormaPagamento,
                clinica=clinica,
                descricao=descricao,
                defaults={"status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            )
            for descricao in ["Pix", "Cartão", "Dinheiro"]
        }
        tipos_consulta = {
            descricao: self._get_or_create(
                TipoConsulta,
                clinica=clinica,
                descricao=descricao,
                defaults={"status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            )
            for descricao in ["Consulta Inicial", "Retorno", "Avaliação"]
        }

        categorias = {
            ("RECEITA", "Consulta Particular"): self._get_or_create(
                CategoriaFinanceira,
                clinica=clinica,
                tipo=CategoriaFinanceira.Tipo.RECEITA,
                descricao="Consulta Particular",
                defaults={"cor": "badge-success", "status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            ),
            ("RECEITA", "Vacinação"): self._get_or_create(
                CategoriaFinanceira,
                clinica=clinica,
                tipo=CategoriaFinanceira.Tipo.RECEITA,
                descricao="Vacinação",
                defaults={"cor": "badge-primary", "status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            ),
            ("DESPESA", "Marketing"): self._get_or_create(
                CategoriaFinanceira,
                clinica=clinica,
                tipo=CategoriaFinanceira.Tipo.DESPESA,
                descricao="Marketing",
                defaults={"cor": "badge-error", "status": True, "uscad": DEMO_ACTOR, "usalt": DEMO_ACTOR},
            ),
        }

        medicos = []
        for indice, (nome, crm, especialidade_nome) in enumerate(
            [
                ("Dra. Marina Lopes", "CRM1001", "Dermatologia"),
                ("Dr. Paulo Mendes", "CRM1002", "Cardiologia"),
                ("Dra. Carla Souza", "CRM1003", "Clínica Geral"),
            ],
            start=1,
        ):
            medico = self._get_or_create(
                Medico,
                clinica=clinica,
                crm=crm,
                defaults={
                    "nome": nome,
                    "cpf": f"100200300{indice:02d}",
                    "celular": f"(11) 98888-10{indice:02d}",
                    "telefone": f"(11) 3333-10{indice:02d}",
                    "email": f"medico{indice}.{clinica.pk}@demo.com",
                    "status": True,
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )
            MedicoEspecialidade.objects.get_or_create(
                clinica=clinica,
                medico=medico,
                especialidade=especialidades[especialidade_nome],
                defaults={"descricao": "Especialista demo", "status": True, "uscad": DEMO_ACTOR},
            )
            for hora in ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30"]:
                MedicoAgenda.objects.get_or_create(
                    clinica=clinica,
                    medico=medico,
                    hora=datetime.strptime(hora, "%H:%M").time(),
                    defaults={"status": True, "uscad": DEMO_ACTOR},
                )
            medicos.append(medico)

        pacientes = []
        nomes_pacientes = [
            "Ana Beatriz Lima",
            "Bruno Costa",
            "Camila Fernandes",
            "Daniel Rocha",
            "Eduarda Martins",
            "Felipe Nunes",
            "Gabriela Ribeiro",
            "Henrique Alves",
            "Isabela Freitas",
            "João Pedro Melo",
            "Larissa Gomes",
            "Marcos Oliveira",
        ]
        for indice, nome in enumerate(nomes_pacientes, start=1):
            convenio = list(convenios.values())[indice % len(convenios)]
            paciente = self._get_or_create(
                Paciente,
                clinica=clinica,
                cpf=f"900000000{indice:02d}",
                defaults={
                    "nome": nome,
                    "celular": f"(11) 97777-20{indice:02d}",
                    "telefone": f"(11) 3444-20{indice:02d}",
                    "email": f"{self._slug(nome)}.{clinica.pk}@demo.com",
                    "documento": f"RG-{indice:06d}",
                    "nascimento": hoje - timedelta(days=365 * (22 + indice)),
                    "sexo": "Feminino" if indice % 2 else "Masculino",
                    "profissao": "Cliente demonstração",
                    "logradouro": "Rua das Flores",
                    "numero": str(100 + indice),
                    "bairro": "Centro",
                    "cidade": "São Paulo",
                    "estado": "SP",
                    "convenio": convenio,
                    "prontuario": "Paciente fictício para demonstração do sistema.",
                    "status": True,
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )
            pacientes.append(paciente)

        self._ensure_colaboradores(clinica)

        horarios = [
            ("08:00", Agenda.Status.AGENDADO, status_agendado, pacientes[0]),
            ("08:30", Agenda.Status.AGENDADO, status_finalizado, pacientes[1]),
            ("09:00", Agenda.Status.AGENDADO, status_agendado, pacientes[2]),
            ("09:30", Agenda.Status.AGENDADO, status_em_andamento, pacientes[3]),
            ("10:00", Agenda.Status.AGENDADO, status_agendado, pacientes[4]),
            ("10:30", Agenda.Status.DISPONIVEL, None, None),
            ("11:00", Agenda.Status.AGENDADO, status_agendado, pacientes[5]),
            ("11:30", Agenda.Status.BLOQUEADO, None, None),
        ]
        agenda_criada = 0
        for dia, medico in [(ontem, medicos[0]), (hoje, medicos[1]), (amanha, medicos[2])]:
            for posicao, (hora_str, status_slot, status_agendamento, paciente) in enumerate(horarios):
                hora = datetime.strptime(hora_str, "%H:%M").time()
                agenda, created = Agenda.objects.get_or_create(
                    clinica=clinica,
                    medico=medico,
                    data=dia,
                    hora=hora,
                    defaults={
                        "paciente": paciente,
                        "convenio": paciente.convenio if paciente else None,
                        "tipo_consulta": list(tipos_consulta.values())[posicao % len(tipos_consulta)],
                        "especialidade": medico.especialidades.first().especialidade if medico.especialidades.exists() else None,
                        "status_agendamento": status_agendamento,
                        "status": status_slot,
                        "uscad": DEMO_ACTOR,
                        "usalt": DEMO_ACTOR,
                    },
                )
                if not created:
                    agenda.status = status_slot
                    agenda.paciente = paciente
                    agenda.convenio = paciente.convenio if paciente else None
                    agenda.tipo_consulta = list(tipos_consulta.values())[posicao % len(tipos_consulta)] if paciente else None
                    agenda.especialidade = medico.especialidades.first().especialidade if medico.especialidades.exists() and paciente else None
                    agenda.status_agendamento = status_agendamento
                    agenda.usalt = DEMO_ACTOR
                    agenda.save()
                agenda_criada += int(created)

        vacinas = [
            ("Influenza", pacientes[0], Decimal("120.00")),
            ("Hepatite B", pacientes[6], Decimal("95.00")),
            ("Febre Amarela", pacientes[8], Decimal("150.00")),
        ]
        for descricao, paciente, valor in vacinas:
            PacienteVacina.objects.get_or_create(
                clinica=clinica,
                paciente=paciente,
                descricao_vacina=descricao,
                defaults={
                    "data_aplicacao": hoje - timedelta(days=7),
                    "forma_pagamento": formas_pagamento["Pix"],
                    "valor": valor,
                    "obs": "Aplicação fictícia para demonstração.",
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )

        lancamentos = [
            {
                "descricao": "Consulta Particular - Ana Beatriz Lima",
                "tipo": LancamentoFinanceiro.Tipo.RECEITA,
                "origem": LancamentoFinanceiro.Origem.CONSULTA,
                "categoria": categorias[("RECEITA", "Consulta Particular")],
                "paciente": pacientes[0],
                "convenio": None,
                "forma_pagamento": formas_pagamento["Pix"],
                "valor": Decimal("280.00"),
                "valor_recebido": Decimal("280.00"),
                "data_lancamento": hoje - timedelta(days=1),
                "competencia": hoje,
                "data_vencimento": hoje - timedelta(days=1),
                "data_pagamento": hoje - timedelta(days=1),
            },
            {
                "descricao": "Consulta Particular - Bruno Costa",
                "tipo": LancamentoFinanceiro.Tipo.RECEITA,
                "origem": LancamentoFinanceiro.Origem.CONSULTA,
                "categoria": categorias[("RECEITA", "Consulta Particular")],
                "paciente": pacientes[1],
                "convenio": None,
                "forma_pagamento": formas_pagamento["Cartão"],
                "valor": Decimal("320.00"),
                "valor_recebido": Decimal("160.00"),
                "data_lancamento": hoje,
                "competencia": hoje,
                "data_vencimento": hoje,
                "data_pagamento": None,
            },
            {
                "descricao": "Lote de vacinação demo",
                "tipo": LancamentoFinanceiro.Tipo.RECEITA,
                "origem": LancamentoFinanceiro.Origem.VACINA,
                "categoria": categorias[("RECEITA", "Vacinação")],
                "paciente": pacientes[6],
                "convenio": None,
                "forma_pagamento": formas_pagamento["Pix"],
                "valor": Decimal("150.00"),
                "valor_recebido": Decimal("0.00"),
                "data_lancamento": hoje,
                "competencia": hoje,
                "data_vencimento": amanha,
                "data_pagamento": None,
            },
            {
                "descricao": "Campanha Instagram",
                "tipo": LancamentoFinanceiro.Tipo.DESPESA,
                "origem": LancamentoFinanceiro.Origem.MANUAL,
                "categoria": categorias[("DESPESA", "Marketing")],
                "paciente": None,
                "convenio": None,
                "forma_pagamento": formas_pagamento["Cartão"],
                "valor": Decimal("480.00"),
                "valor_recebido": Decimal("0.00"),
                "data_lancamento": hoje - timedelta(days=10),
                "competencia": hoje,
                "data_vencimento": hoje - timedelta(days=3),
                "data_pagamento": None,
            },
        ]
        for item in lancamentos:
            LancamentoFinanceiro.objects.get_or_create(
                clinica=clinica,
                descricao=item["descricao"],
                data_lancamento=item["data_lancamento"],
                defaults={
                    **item,
                    "nome_cliente": item["paciente"].nome if item["paciente"] else "Fornecedor Demo",
                    "observacoes": "Lançamento fictício para vídeo demonstrativo.",
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )

        return {
            "pacientes": len(pacientes),
            "medicos": len(medicos),
            "agenda_nova": agenda_criada,
            "colaboradores": clinica.colaboradores.count(),
            "lancamentos": LancamentoFinanceiro.objects.filter(clinica=clinica).count(),
            "vacinas": PacienteVacina.objects.filter(clinica=clinica).count(),
        }

    def _ensure_colaboradores(self, clinica):
        limite = clinica.limite_colaboradores or 4
        perfis = [
            ("Administrador Demo", "ADMIN"),
            ("Recepção Demo", "RECEPCAO"),
            ("Financeiro Demo", "FINANCEIRO"),
            ("Enfermagem Demo", "ENFERMAGEM"),
        ][:limite]

        for indice, (nome, papel) in enumerate(perfis, start=1):
            colaborador, created = Colaborador.objects.get_or_create(
                clinica=clinica,
                email=f"demo{indice}.{clinica.pk}@vittas.com",
                defaults={
                    "nome": nome,
                    "papel": papel,
                    "status": True,
                    "uscad": DEMO_ACTOR,
                    "usalt": DEMO_ACTOR,
                },
            )
            if created:
                colaborador.set_password(DEMO_PASSWORD)
                colaborador.save(update_fields=["password"])

    def _get_or_create(self, model, defaults=None, **lookup):
        obj, created = model.objects.get_or_create(defaults=defaults or {}, **lookup)
        if not created and defaults:
            changed = False
            for field, value in defaults.items():
                if getattr(obj, field) in (None, "", False):
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.save()
        return obj

    def _slug(self, value):
        return (
            value.lower()
            .replace(" ", "-")
            .replace(".", "")
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
        )

    def _format_summary(self, clinica, resumo):
        return (
            f"{clinica.nome_fantasia}: "
            f"{resumo['pacientes']} pacientes, "
            f"{resumo['medicos']} médicos, "
            f"{resumo['colaboradores']} colaboradores, "
            f"{resumo['agenda_nova']} horários novos, "
            f"{resumo['lancamentos']} lançamentos, "
            f"{resumo['vacinas']} vacinas."
        )
