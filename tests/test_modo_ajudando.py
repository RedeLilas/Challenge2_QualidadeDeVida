"""Modo "ajudando outra pessoa" no jurídico (s4-orquestrador-agentes, tarefa 3.4).

Índice e LLM simulados. Textos fictícios.
"""
import pytest
from fastapi.testclient import TestClient

from app import main, orquestrador as mod_orquestrador
from app.main import app
from app.orquestrador import INSTRUCOES_AJUDANDO, INSTRUCOES_JURIDICO_CONVERSA
from app.rag.resposta import INSTRUCOES

RESPOSTA = "Ela pode pedir a medida protetiva (Lei 11.340/2006, art. 19)."


def trecho(artigo):
    return {
        "id": f"lei-11340-2006:art{artigo}", "norma_id": "lei-11340-2006", "eixo": "juridico",
        "lei": "Lei 11.340/2006", "artigo": artigo, "citacao": f"Lei 11.340/2006, art. {artigo}", "capitulo": "",
        "texto": "Texto fictício.", "url": f"https://www.planalto.gov.br/exemplo.htm#art{artigo}",
        "data_acesso": "2026-11-03",
    }  # fmt: skip


class IndiceFalso:
    def buscar(self, pergunta, k=5, eixos=None):
        return [(trecho(a), 0.9) for a in ("19", "22")]


class LLMFalso:
    def __init__(self):
        self.sistemas = []

    def responder(self, mensagens, temperatura=0.2):
        self.sistemas.append(mensagens[0]["content"])
        return RESPOSTA


@pytest.fixture
def llm():
    originais = main.cliente_llm, main.indice_juridico
    falso = LLMFalso()
    main.cliente_llm = lambda: falso
    main.indice_juridico = lambda: IndiceFalso()
    yield falso
    main.cliente_llm, main.indice_juridico = originais


def orquestrar(texto, **flags):
    resposta = TestClient(app).post("/orquestrar", json={"texto": texto, **flags})
    assert resposta.status_code == 200
    return resposta.json()


@pytest.mark.parametrize("ajudando, instrucoes", [(True, INSTRUCOES_AJUDANDO), (False, INSTRUCOES_JURIDICO_CONVERSA)])
def test_instrucao_enviada_ao_llm_com_e_sem_a_flag(llm, ajudando, instrucoes):
    # "medida protetiva": a regra escolhe o jurídico, e o LLM só é chamado para a resposta.
    corpo = orquestrar("minha amiga quer pedir medida protetiva, como ela faz?", ajudando=ajudando)
    assert corpo["agente"] == "juridico" and corpo["resposta"]["recusada"] is False
    assert llm.sistemas == [instrucoes]


def test_sem_a_flag_o_padrao_e_a_instrucao_do_juridico_na_conversa(llm):
    orquestrar("como peço medida protetiva?")
    assert llm.sistemas == [INSTRUCOES_JURIDICO_CONVERSA]


def test_explicacao_de_beneficio_pelo_juridico_tambem_usa_o_modo(llm, monkeypatch):
    monkeypatch.setattr(mod_orquestrador, "explicar_beneficio", None)
    corpo = orquestrar("como funciona o cartão gás?", ajudando=True)
    assert (corpo["agente"], corpo["tipo"]) == ("beneficios", "explicacao")
    assert llm.sistemas == [INSTRUCOES_AJUDANDO]


def test_juridico_nunca_usa_o_modo(llm):
    resposta = TestClient(app).post("/juridico", json={"pergunta": "como peço medida protetiva?"})
    assert resposta.status_code == 200
    assert llm.sistemas == [INSTRUCOES]


def test_modo_mantem_todas_as_regras_do_juridico():
    # Nenhuma regra do jurídico sai: o modo só acrescenta linhas no fim.
    assert INSTRUCOES_AJUDANDO.startswith(INSTRUCOES + "\n")
    acrescimo = INSTRUCOES_AJUDANDO[len(INSTRUCOES) :]
    assert "terceira pessoa" in acrescimo
    assert "sem expor a vítima ao agressor" in acrescimo
    assert "decisões da vítima" in acrescimo and "consentimento" in acrescimo
    assert "190" in acrescimo
    assert "direito garantido" not in acrescimo
