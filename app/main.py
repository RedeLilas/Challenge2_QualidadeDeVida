"""Aplicação FastAPI: rotas do backend e a PWA estática em web/."""
import logging
import mimetypes
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import llm, risco
from app.config import ConfigIncompleta
from app.logs import registrar_requisicao
from app.rag import resposta as resposta_juridica

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

WEB = Path(__file__).resolve().parent.parent / "web"
mimetypes.add_type("application/manifest+json", ".webmanifest")

# Provisório até o orquestrador e o RAG: só garante o tom e o encaminhamento básico.
INSTRUCOES = (
    "Você responde em português do Brasil, com linguagem simples e frases curtas. "
    "Quando usar um termo jurídico, explique-o em uma frase simples. "
    "Não invente leis nem números de artigo. "
    "Se a pessoa estiver em perigo agora, diga para ligar 190. "
    "Para conversar com alguém, indique o Ligue 180 (gratuito, 24 horas)."
)
INDISPONIVEL = (
    "Não consegui responder agora. Tente de novo em alguns instantes. "
    "Se precisar falar com alguém, ligue 180 (gratuito, 24 horas)."
)

def indice_juridico():
    # Import tardio: o modelo de embeddings (torch) só carrega quando o índice é usado.
    from app.rag import indice

    return indice.indice_padrao()


@asynccontextmanager
async def _ciclo_de_vida(_app):
    # Monta o índice em segundo plano (cerca de 20 s em CPU) para a primeira pergunta não esperar.
    # O servidor já responde enquanto isso; uma pergunta que chegue antes aguarda o índice ficar pronto.
    threading.Thread(target=indice_juridico, name="indice-juridico", daemon=True).start()
    yield


app = FastAPI(title="Rede Lilás", docs_url=None, redoc_url=None, openapi_url=None, lifespan=_ciclo_de_vida)
app.middleware("http")(registrar_requisicao)


class Turno(BaseModel):
    papel: Literal["usuaria", "assistente"]
    texto: str = Field(min_length=1, max_length=4000)


class Mensagem(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    # A conversa vive só na aba; o navegador reenvia os turnos anteriores a cada mensagem.
    historico: list[Turno] = Field(default_factory=list, max_length=20)


def cliente_llm() -> llm.ClienteLLM:
    # Chamada dentro das rotas, depois da checagem de risco. Os testes trocam esta função.
    return llm.cliente()


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok"}


def alerta_de_risco(texto: str) -> dict | None:
    """Resposta de alerta de 190 se o texto tiver sinal de risco imediato (regra, sem LLM)."""
    resultado = risco.avaliar(texto)
    if resultado is None:
        return None
    return {"risco_imediato": True, "categoria": resultado["categoria"], "resposta": risco.ALERTA}


@app.post("/mensagem")
def mensagem(corpo: Mensagem, response: Response):
    # Respostas com o texto da usuária nunca ficam em cache (navegador, proxy ou service worker).
    response.headers["Cache-Control"] = "no-store"
    # O risco é checado antes de preparar o LLM: o alerta funciona mesmo sem LLM configurado.
    if alerta := alerta_de_risco(corpo.texto):
        return alerta
    cliente = cliente_llm()
    mensagens = [{"role": "system", "content": INSTRUCOES}]
    mensagens += [
        {"role": "user" if t.papel == "usuaria" else "assistant", "content": t.texto} for t in corpo.historico
    ]
    mensagens.append({"role": "user", "content": corpo.texto})
    try:
        return {"resposta": cliente.responder(mensagens)}
    except llm.LLMIndisponivel:
        return JSONResponse({"erro": INDISPONIVEL}, status_code=503, headers={"Cache-Control": "no-store"})


class PerguntaJuridica(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)


@app.post("/juridico")
def juridico(corpo: PerguntaJuridica, response: Response):
    """Alerta de 190, resposta com as citações conferidas ou recusa com o Ligue 180 e a Defensoria."""
    response.headers["Cache-Control"] = "no-store"
    # Antes do índice e do LLM: o alerta não espera o índice ser montado (cerca de 20 s ao subir)
    # nem depende do LLM estar configurado.
    if alerta := alerta_de_risco(corpo.pergunta):
        return alerta
    try:
        return resposta_juridica.responder(corpo.pergunta, indice_juridico(), cliente_llm())
    except llm.LLMIndisponivel:
        return JSONResponse({"erro": INDISPONIVEL}, status_code=503, headers={"Cache-Control": "no-store"})


@app.exception_handler(ConfigIncompleta)
def _sem_config(_request, _erro):
    # Ambiente sem LLM configurado: a PWA mostra a mesma mensagem de indisponibilidade.
    return JSONResponse({"erro": INDISPONIVEL}, status_code=503, headers={"Cache-Control": "no-store"})


@app.middleware("http")
async def _cabecalhos_de_privacidade(request, call_next):
    resposta = await call_next(request)
    # Ao sair para o site neutro, ele não fica sabendo de onde a usuária veio.
    resposta.headers.setdefault("Referrer-Policy", "no-referrer")
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.url.path == "/sw.js":
        # O service worker precisa ser revalidado para as atualizações chegarem.
        resposta.headers["Cache-Control"] = "no-cache"
    return resposta


# Regras do alerta de 190, lidas pela PWA (web/risco.js) e guardadas pelo service worker.
app.mount("/regras", StaticFiles(directory=WEB.parent / "regras"), name="regras")
# Por último: as rotas da API acima têm prioridade sobre os arquivos estáticos.
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
