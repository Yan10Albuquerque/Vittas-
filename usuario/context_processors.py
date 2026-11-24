from base.tenancy import MODULO_LABELS, get_clinica_atual

from .visitante import MENSAGEM_SOMENTE_LEITURA, is_visitante


def unidades_context(request):
    clinica = get_clinica_atual(request)
    modulos_liberados = {modulo: False for modulo in MODULO_LABELS}
    user = getattr(request, "user", None)

    if user and getattr(user, "is_authenticated", False):
        for modulo in modulos_liberados:
            modulos_liberados[modulo] = user.modulo_disponivel(modulo)

    return {
        "clinica_atual": clinica,
        "modulos_liberados": modulos_liberados,
        "mostrar_menu_configuracoes": modulos_liberados["configuracoes"],
        "modo_visitante": is_visitante(request),
        "mensagem_modo_visitante": MENSAGEM_SOMENTE_LEITURA,
    }
