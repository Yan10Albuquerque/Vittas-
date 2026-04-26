from .models import Clinica, Colaborador


class ClinicaAuthBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        clinica = Clinica.objects.filter(email__iexact=email, status=True).first()
        if clinica and clinica.check_password(password):
            return clinica
        return None

    def get_user(self, user_id):
        return Clinica.objects.filter(pk=user_id, status=True).first()


class ColaboradorAuthBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        colaborador = (
            Colaborador.objects.select_related("clinica")
            .filter(email__iexact=email, status=True, clinica__status=True)
            .first()
        )
        if colaborador and colaborador.check_password(password):
            return colaborador
        return None

    def get_user(self, user_id):
        return (
            Colaborador.objects.select_related("clinica")
            .filter(pk=user_id, status=True, clinica__status=True)
            .first()
        )
