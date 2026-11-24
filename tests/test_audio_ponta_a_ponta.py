"""Pergunta por áudio de ponta a ponta (s5-entrada-audio, tarefa 4.1; critério de pronto da S5).

Caminho de verdade: áudio fictício → POST /transcrever (Whisper de verdade) → tela (tratarTranscricao
de web/app.js, com a regra de web/risco.js, no QuickJS) → POST /orquestrar. Só o índice e o LLM
são falsos. Marca `whisper`: rodar com `uv run pytest -m whisper`.
"""
import json
import re
from pathlib import Path

import pytest
import quickjs
from fastapi.testclient import TestClient

from app import main, risco, transcricao
from app.main import app
from app.orquestrador import RespostaOrquestrar

pytestmark = pytest.mark.whisper

RAIZ = Path(__file__).resolve().parents[1]
AUDIOS = RAIZ / "tests" / "audios"
RESPOSTA_JURIDICA = "A guarda dos filhos é decidida pelo juiz, que pode fixar medidas protetivas (Lei 11.340/2006, art. 22)."


def trecho(artigo):
    return {
        "id": f"lei-11340-2006:art{artigo}", "norma_id": "lei-11340-2006", "eixo": "juridico",
        "lei": "Lei 11.340/2006", "artigo": artigo, "citacao": f"Lei 11.340/2006, art. {artigo}", "capitulo": "",
        "texto": "Texto fictício.", "url": f"https://www.planalto.gov.br/exemplo.htm#art{artigo}",
        "data_acesso": "2026-11-03",
    }  # fmt: skip


class IndiceFalso:
    def buscar(self, pergunta, k=5, eixos=None):
        return [(trecho(a), 0.9) for a in ("22", "19", "7")]


class LLMFalso:
    """Classifica como jurídico (se o orquestrador perguntar) e responde citando o art. 22."""

    def __init__(self):
        self.chamadas = []

    def responder(self, mensagens, temperatura=0.2, **_opcoes):
        self.chamadas.append(mensagens)
        instrucoes = mensagens[0]["content"]
        if '"perguntas"' in instrucoes:
            pergunta = mensagens[-1]["content"]
            return json.dumps({"perguntas": [{"agente": "juridico", "tipo": None, "pergunta": pergunta, "beneficio": None,
                                              "ra": None, "violencia_sexual_recente": None}]}, ensure_ascii=False)  # fmt: skip
        return RESPOSTA_JURIDICA


@pytest.fixture(scope="module")
def whisper():
    return transcricao.carregar()


@pytest.fixture
def servidor(whisper):
    originais = main.transcritor, main.cliente_llm, main.indice_juridico
    llm = LLMFalso()
    main.transcritor = lambda: whisper
    main.cliente_llm = lambda: llm
    main.indice_juridico = lambda: IndiceFalso()
    yield TestClient(app), llm
    main.transcritor, main.cliente_llm, main.indice_juridico = originais


@pytest.fixture
def tela():
    """A tela de verdade (tratarTranscricao de web/app.js) com espiões no lugar do DOM e da rede."""
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "risco.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "audio.js").read_text(encoding="utf-8"))
    regras = (RAIZ / "regras" / "risco_imediato.json").read_text(encoding="utf-8")
    contexto.eval(
        f"var regrasDeRisco = Risco.compilar({regras});"
        """
        var pedidos = [];
        function fetch(url) { pedidos.push(url); return Promise.resolve({}); }
        function enviar(texto) { pedidos.push("enviar:" + texto); return Promise.resolve(true); }
        var alertas = [];
        function mostrarAlerta(opcoes) { alertas.push(!!opcoes.comContinuar); }
        function adicionar() { return { remove: function () {} }; }
        function ajustarAltura() {}
        var textoAguardandoAlerta = "";
        var campo = { value: "", focus: function () {} };
        """
    )
    codigo = (RAIZ / "web" / "app.js").read_text(encoding="utf-8")
    inicio = codigo.index("function tratarTranscricao(")
    contexto.eval(codigo[inicio : codigo.index("\n}\n", inicio) + 3])
    return contexto


def transcrever(cliente, arquivo, tipo):
    resposta = cliente.post("/transcrever", content=(AUDIOS / arquivo).read_bytes(), headers={"Content-Type": tipo})
    assert resposta.status_code == 200 and resposta.headers["cache-control"] == "no-store"
    return resposta.json()["texto"]


def orquestrar(cliente, texto, **flags):
    resposta = cliente.post("/orquestrar", json={"texto": texto, **flags})
    assert resposta.status_code == 200
    return RespostaOrquestrar.model_validate(resposta.json()).model_dump()


def estado(tela):
    return json.loads(tela.eval("JSON.stringify({pedidos: pedidos, alertas: alertas, campo: campo.value, pendente: textoAguardandoAlerta})"))


def test_pergunta_por_audio_respondida_de_ponta_a_ponta(servidor, tela):
    cliente, llm = servidor
    # 1. A1 (Android, webm/opus) é transcrito no servidor da aplicação.
    texto = transcrever(cliente, "a1.webm", "audio/webm;codecs=opus")
    assert re.search(r"\btirar\b.*\bfilhos\b", risco.normalizar(texto))
    # 2. Na tela: sem sinal de risco, o texto vai para a caixa, e nada é enviado ainda.
    assert tela.eval(f"tratarTranscricao({json.dumps(texto)})") == "caixa"
    assert estado(tela) == {"pedidos": [], "alertas": [], "campo": texto, "pendente": ""}
    assert llm.chamadas == []
    # 3. A usuária confere e envia: o texto da caixa segue para o orquestrador, como o digitado.
    corpo = orquestrar(cliente, estado(tela)["campo"])
    assert corpo["risco_imediato"] is False and corpo["agente"] == "juridico"
    assert corpo["resposta"]["resposta"] == RESPOSTA_JURIDICA
    assert [c["citacao"] for c in corpo["resposta"]["citacoes"]] == ["Lei 11.340/2006, art. 22"]


def test_audio_com_risco_so_chega_ao_llm_depois_do_continuar(servidor, tela):
    cliente, llm = servidor
    # 1. A6 (iPhone, mp4/aac) é transcrito; o servidor não aplica regra nem chama o LLM.
    texto = transcrever(cliente, "a6.mp4", "audio/mp4")
    assert llm.chamadas == []
    # 2. Na tela: o 190 aparece na hora, com "Continuar com minha pergunta", e nada é enviado.
    assert tela.eval(f"tratarTranscricao({json.dumps(texto)})") == "alerta"
    assert estado(tela) == {"pedidos": [], "alertas": [True], "campo": "", "pendente": texto}
    # 3. Um pedido sem alerta visto (ex.: versão antiga da tela) recebe só o alerta, sem LLM.
    sem_toque = orquestrar(cliente, texto)
    assert sem_toque["risco_imediato"] is True and sem_toque["agente"] is None and sem_toque["resposta"] is None
    assert llm.chamadas == []
    # 4. Depois do toque em "Continuar", vai ao jurídico, e o risco volta junto com a resposta.
    com_toque = orquestrar(cliente, texto, alerta_visto=True)
    assert com_toque["risco_imediato"] is True and com_toque["categoria_risco"] == "ameaca_morte"
    assert com_toque["agente"] == "juridico" and com_toque["resposta"]["citacoes"]
    assert llm.chamadas != []
