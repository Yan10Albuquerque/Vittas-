from decimal import Decimal

from django.utils import timezone

from base.models import FormaPagamento

from .models import CategoriaFinanceira, LancamentoFinanceiro


def get_or_create_categoria_vacina(clinica):
    categoria, _ = CategoriaFinanceira.objects.get_or_create(
        clinica=clinica,
        tipo=CategoriaFinanceira.Tipo.RECEITA,
        descricao="Vacinas",
        defaults={
            "cor": "badge-success",
            "status": True,
            "uscad": "sistema",
            "usalt": "sistema",
        },
    )
    return categoria


def sincronizar_lancamento_vacina(vacina):
    clinica = vacina.clinica or getattr(vacina.paciente, "clinica", None)
    if not clinica:
        return None

    valor = vacina.valor or Decimal("0.00")
    if valor <= 0:
        if hasattr(vacina, "lancamento_financeiro") and vacina.lancamento_financeiro_id:
            lancamento = vacina.lancamento_financeiro
            lancamento.status = LancamentoFinanceiro.Status.CANCELADO
            lancamento.usalt = vacina.usalt or vacina.uscad or "sistema"
            lancamento.save(update_fields=["status", "usalt", "dtalt"])
        return None

    categoria = get_or_create_categoria_vacina(clinica)
    forma_pagamento = vacina.forma_pagamento
    if not forma_pagamento and vacina.forma_pagamento_id:
        forma_pagamento = FormaPagamento.objects.filter(pk=vacina.forma_pagamento_id).first()

    data_base = vacina.data_aplicacao or timezone.localdate()
    defaults = {
        "clinica": clinica,
        "paciente": vacina.paciente,
        "categoria": categoria,
        "forma_pagamento": forma_pagamento,
        "tipo": LancamentoFinanceiro.Tipo.RECEITA,
        "origem": LancamentoFinanceiro.Origem.VACINA,
        "descricao": f"Vacina - {vacina.descricao_vacina or 'Aplicação'}",
        "nome_cliente": vacina.paciente.nome if vacina.paciente_id else "",
        "data_lancamento": data_base,
        "competencia": data_base,
        "data_vencimento": data_base,
        "data_pagamento": data_base,
        "valor": valor,
        "valor_recebido": valor,
        "status": LancamentoFinanceiro.Status.PAGO,
        "observacoes": vacina.obs or "",
        "uscad": vacina.uscad or "sistema",
        "usalt": vacina.usalt or vacina.uscad or "sistema",
    }

    lancamento, criado = LancamentoFinanceiro.objects.get_or_create(
        vacina=vacina,
        defaults=defaults,
    )
    if not criado:
        for campo, valor_campo in defaults.items():
            setattr(lancamento, campo, valor_campo)
        lancamento.save()
    return lancamento
