"""Parametrização de responder() em app/rag/resposta.py (s4-orquestrador-agentes, tarefa 1.1).

Garante que /juridico continua usando os mesmos parâmetros da S3 ({"juridico"}, INSTRUCOES e 0,81)
e que responder() aceita eixos, instrucoes e limite personalizados.
"""
import inspect

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.rag import resposta
from app.rag.resposta import EIXOS, INSTRUCOES, LIMITE_SIMILARIDADE, RECUSA, responder
from tests.test_juridico import PERGUNTA, RECUPERADOS, IndiceFalso, LLMFalso


@pytest.fixture
def cliente():
    originais = main.cliente_llm, main.indice_juridico
    yield TestClient(app)
    main.cliente_llm, main.indice_juridico = originais


def test_padroes_de_responder_sao_os_valores_da_s3():
    parametros = inspect.signature(responder).parameters
    assert parametros["eixos"].default == {"juridico"} == EIXOS
    assert parametros["instrucoes"].default == INSTRUCOES
    assert parametros["limite"].default == 0.81 == LIMITE_SIMILARIDADE


def test_rota_juridico_usa_eixos_instrucoes_e_limite_da_s3(cliente, monkeypatch):
    falso_llm, falso_indice = LLMFalso("Quebrar suas coisas pode ser violência patrimonial (Lei 11.340/2006, art. 7º)."), IndiceFalso()
    main.cliente_llm = lambda: falso_llm
    main.indice_juridico = lambda: falso_indice

    chamadas = []
    original = resposta.responder

    def espiao(pergunta, indice, cliente_arg, *, eixos=EIXOS, instrucoes=INSTRUCOES, limite=LIMITE_SIMILARIDADE):
        chamadas.append({"eixos": eixos, "instrucoes": instrucoes, "limite": limite})
        return original(pergunta, indice, cliente_arg, eixos=eixos, instrucoes=instrucoes, limite=limite)

    monkeypatch.setattr(resposta, "responder", espiao)
    r = cliente.post("/juridico", json={"pergunta": PERGUNTA})

    assert r.status_code == 200
    assert chamadas == [{"eixos": {"juridico"}, "instrucoes": INSTRUCOES, "limite": 0.81}]
    assert falso_indice.chamadas == [{"pergunta": PERGUNTA, "k": 5, "eixos": {"juridico"}}]
    assert falso_llm.recebido[0] == {"role": "system", "content": INSTRUCOES}


def test_responder_aceita_eixos_instrucoes_e_limite_personalizados():
    indice = IndiceFalso()
    llm_falso = LLMFalso("Resposta fictícia (Lei 11.340/2006, art. 7º).")
    instrucoes_custom = "Instruções personalizadas para outro agente."

    resultado = responder(
        PERGUNTA,
        indice,
        llm_falso,
        eixos={"beneficios", "df"},
        instrucoes=instrucoes_custom,
        limite=0.75,
    )

    assert resultado["recusada"] is False
    assert indice.chamadas == [{"pergunta": PERGUNTA, "k": 5, "eixos": {"beneficios", "df"}}]
    assert llm_falso.recebido[0] == {"role": "system", "content": instrucoes_custom}


def test_responder_respeita_limite_personalizado():
    class IndiceComSimilaridadeFixa(IndiceFalso):
        def buscar(self, pergunta, k=5, eixos=None):
            return [(t, 0.83) for t in RECUPERADOS[:k]]

    llm_falso = LLMFalso("Resposta fictícia (Lei 11.340/2006, art. 7º).")
    # 0.83 passaria no padrão 0.81, mas deve recusar com limite=0.85 sem chamar o LLM
    resultado = responder(PERGUNTA, IndiceComSimilaridadeFixa(), llm_falso, limite=0.85)

    assert resultado == {"resposta": RECUSA, "citacoes": [], "recusada": True}
    assert llm_falso.recebido is None
