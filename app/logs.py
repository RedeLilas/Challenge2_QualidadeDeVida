"""Log de requisições só com dados técnicos: método, rota, status, duração e tipo de erro.

Nunca registra corpo, query string, cabeçalhos nem a mensagem de exceções, que podem
conter o relato da usuária. Por isso as rotas recebem texto no corpo, não na URL.
"""
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger("rede_lilas.http")


async def registrar_requisicao(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    inicio = time.perf_counter()
    # url.path não inclui a query string.
    rota = f"{request.method} {request.url.path}"
    try:
        resposta = await call_next(request)
    except Exception as erro:
        # Só o tipo: a mensagem e o traceback podem carregar o texto da requisição.
        # A exceção não é relançada para o servidor não imprimir o traceback.
        logger.error("%s 500 %.0fms erro=%s", rota, _ms(inicio), type(erro).__name__)
        return JSONResponse({"erro": "erro interno"}, status_code=500)

    logger.info("%s %d %.0fms", rota, resposta.status_code, _ms(inicio))
    return resposta


def _ms(inicio: float) -> float:
    return (time.perf_counter() - inicio) * 1000
