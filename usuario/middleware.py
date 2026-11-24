from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .visitante import MENSAGEM_SOMENTE_LEITURA, is_visitante

METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# Rotas que aceitam POST sem alterar dados e continuam liberadas para o visitante.
ROTAS_LIBERADAS = {
    "usuario:logout_api",
    "usuario:visitante",
}

# Endpoints que usam POST + "funcao" também para consultas somente leitura.
FUNCOES_LEITURA = {
    "paciente:paciente_api": {"buscar_dados"},
}


class ModoVisitanteMiddleware:
    """Bloqueia qualquer escrita (POST/PUT/PATCH/DELETE) em sessões do modo visitante."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in METODOS_SEGUROS or not is_visitante(request):
            return None

        rota = request.resolver_match.view_name if request.resolver_match else ""
        if rota in ROTAS_LIBERADAS:
            return None
        if request.POST.get("funcao") in FUNCOES_LEITURA.get(rota, set()):
            return None

        return self._bloquear(request)

    def _bloquear(self, request):
        aceita_html = "text/html" in request.headers.get("accept", "")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax or not aceita_html:
            return JsonResponse(
                {
                    "success": False,
                    "status": "ERROR",
                    "message": MENSAGEM_SOMENTE_LEITURA,
                    "modo_visitante": True,
                },
                status=403,
            )

        messages.warning(request, MENSAGEM_SOMENTE_LEITURA)
        destino = request.headers.get("referer", "")
        if not url_has_allowed_host_and_scheme(
            destino,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            destino = "usuario:home"
        return redirect(destino)
