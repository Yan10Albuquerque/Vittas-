import json
import logging
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)

_BRASIL_API_CEP_URL = "https://brasilapi.com.br/api/cep/v2/{cep}"


class CepLookupError(Exception):
    pass


def consultar_cep(cep: str, timeout: int = 5) -> dict[str, Any]:
    cep_limpo = re.sub(r"\D", "", cep or "")
    if len(cep_limpo) != 8:
        raise ValueError("CEP inválido. Informe um CEP com 8 dígitos.")

    request = Request(
        _BRASIL_API_CEP_URL.format(cep=cep_limpo),
        headers={
            "Accept": "application/json",
            "User-Agent": "Vittas/1.0 (+https://vittas.local)",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", 200)
            if status_code != 200:
                raise CepLookupError("Não foi possível consultar o CEP no momento.")

            payload = response.read().decode("utf-8")
            data = json.loads(payload)
    except HTTPError as exc:
        if exc.code == 404:
            raise CepLookupError("CEP não encontrado.") from exc
        logger.warning("Erro HTTP ao consultar CEP %s: %s", cep_limpo, exc)
        raise CepLookupError("Erro ao consultar o serviço de CEP.") from exc
    except (URLError, TimeoutError) as exc:
        logger.warning("Falha de conexão ao consultar CEP %s: %s", cep_limpo, exc)
        raise CepLookupError("Serviço de CEP indisponível no momento.") from exc
    except json.JSONDecodeError as exc:
        logger.warning("Resposta inválida ao consultar CEP %s: %s", cep_limpo, exc)
        raise CepLookupError("Resposta inválida do serviço de CEP.") from exc

    return {
        "cep": data.get("cep", cep_limpo),
        "state": data.get("state"),
        "city": data.get("city"),
        "neighborhood": data.get("neighborhood"),
        "street": data.get("street"),
        "location": data.get("location"),
    }
