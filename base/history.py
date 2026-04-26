def resolve_history_user(request, **kwargs):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None

    if getattr(user, "tipo_usuario", "") == "COLABORADOR":
        return user.clinica
    return user
