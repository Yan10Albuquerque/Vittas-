from base.tenancy import MODULO_LABELS, get_clinica_atual


def unidades_context(request):
    clinica = get_clinica_atual(request)
    modulos_plano = {modulo: False for modulo in MODULO_LABELS}

    if clinica and getattr(clinica, "is_authenticated", False):
        for modulo in modulos_plano:
            modulos_plano[modulo] = clinica.modulo_disponivel(modulo)

    return {
        "clinica_atual": clinica,
        "modulos_plano": modulos_plano,
        "mostrar_menu_configuracoes": modulos_plano["configuracoes"],
    }
