"""Aplicação FastAPI: rotas do backend e a PWA estática em web/."""
import csv
import logging
import mimetypes
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app import llm, orquestrador, risco, transcricao
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
    # O Whisper também carrega em segundo plano; até ficar pronto, /transcrever responde 503.
    threading.Thread(target=transcricao.carregar_em_segundo_plano, name="whisper", daemon=True).start()
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


@app.get("/rede-protecao")
def rede_protecao() -> list[dict]:
    """Devolve os serviços verificados da rede de proteção do DF (sem receber dados da usuária)."""
    caminho = WEB.parent / "dados" / "rede_protecao_df.csv"
    with caminho.open(encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


@app.get("/cep-ra")
def cep_ra() -> list[dict]:
    """Faixas de CEP do DF (Busca Faixa de CEP dos Correios), sem receber dados da usuária.

    O CEP da usuária nunca chega ao servidor: o navegador confere se ele é do DF (web/rede.js).
    """
    caminho = WEB.parent / "dados" / "cep_ra_df.csv"
    with caminho.open(encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


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
        return resposta_juridica.responder(
            corpo.pergunta, indice_juridico(), cliente_llm(), verificacao=resposta_juridica.JURIDICO
        )
    except llm.LLMIndisponivel:
        return JSONResponse({"erro": INDISPONIVEL}, status_code=503, headers={"Cache-Control": "no-store"})


class _ClienteSobDemanda:
    """Cria o cliente de LLM só quando uma etapa precisa dele.

    A regra e os agentes do aparelho (benefícios "tenho direito?", triagem e rede) respondem
    mesmo sem LLM configurado.
    """

    def responder(self, mensagens, **opcoes):
        return cliente_llm().responder(mensagens, **opcoes)


@app.post("/orquestrar")
def orquestrar(corpo: orquestrador.PedidoOrquestrar, response: Response):
    """Alerta de 190, agente escolhido (regra, LLM ou reserva) e, quando é do servidor, a resposta.

    O pedido leva só texto, alerta_visto e ajudando: campos a mais (perfil, histórico) dão 422.
    O /juridico continua igual, para a rodada da S3 seguir reproduzível.
    """
    response.headers["Cache-Control"] = "no-store"
    try:
        return orquestrador.orquestrar(corpo, indice=indice_juridico, cliente=_ClienteSobDemanda())
    except llm.LLMIndisponivel:
        return JSONResponse({"erro": INDISPONIVEL}, status_code=503, headers={"Cache-Control": "no-store"})


def transcritor() -> transcricao.Transcritor:
    # Os testes trocam esta função por um transcritor falso.
    return transcricao.transcritor_pronto()


def _erro_transcricao(chave: str, status: int) -> JSONResponse:
    return JSONResponse({"erro": transcricao.MENSAGENS[chave]}, status_code=status, headers={"Cache-Control": "no-store"})


async def _ler_audio(request: Request) -> bytes | None:
    """O corpo até LIMITE_BYTES, ou None se passar disso. Nunca grava em disco."""
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > transcricao.LIMITE_BYTES:
        return None
    pedacos, total = [], 0
    async for pedaco in request.stream():
        total += len(pedaco)
        if total > transcricao.LIMITE_BYTES:
            return None
        pedacos.append(pedaco)
    return b"".join(pedacos)


@app.post("/transcrever")
async def transcrever(request: Request):
    """Só transcreve o áudio do corpo e devolve {"texto"}: sem regra de risco, sem índice e sem LLM.

    A regra de risco roda no navegador sobre o texto devolvido (exceção à decisão de 17/11, no design
    da s5-entrada-audio). O áudio fica só em memória, e nada dele nem do texto vai para os logs.
    """
    try:
        modelo = transcritor()
    except transcricao.TranscricaoIniciando:
        return _erro_transcricao("iniciando", 503)
    except transcricao.TranscricaoIndisponivel:
        return _erro_transcricao("indisponivel", 503)
    audio = await _ler_audio(request)
    if audio is None:
        return _erro_transcricao("limite", 413)
    if not audio:
        return _erro_transcricao("ilegivel", 422)
    tipo = request.headers.get("content-type", "")
    try:
        # Em outra thread: a transcrição leva segundos e não pode travar as outras rotas.
        texto = await run_in_threadpool(transcricao.transcrever, modelo, audio, tipo)
    except transcricao.AudioLongo:
        return _erro_transcricao("limite", 422)
    except transcricao.AudioIlegivel:
        return _erro_transcricao("ilegivel", 422)
    except Exception as erro:  # erro do modelo: só o tipo vai para o log
        logging.getLogger("rede_lilas.transcricao").error("transcrição falhou: %s", type(erro).__name__)
        return _erro_transcricao("indisponivel", 503)
    if not texto:
        return _erro_transcricao("sem_fala", 422)
    return JSONResponse({"texto": texto}, headers={"Cache-Control": "no-store"})


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
    # Sem isso o navegador reaproveita arquivos antigos por conta própria (cache heurístico), e uma
    # tela ou regra de risco nova demora a chegar. no-cache guarda, mas confere com o servidor (ETag).
    # As rotas da API já mandam no-store, que não é sobrescrito.
    resposta.headers.setdefault("Cache-Control", "no-cache")
    if request.url.path == "/sw.js":
        # O service worker precisa ser revalidado para as atualizações chegarem.
        resposta.headers["Cache-Control"] = "no-cache"
    return resposta


# Regras do alerta de 190, lidas pela PWA (web/risco.js) e guardadas pelo service worker.
app.mount("/regras", StaticFiles(directory=WEB.parent / "regras"), name="regras")
# Por último: as rotas da API acima têm prioridade sobre os arquivos estáticos.
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
