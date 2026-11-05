"""Checagem de risco no servidor antes do LLM (s2-alerta-risco-190, tarefa 2.1)."""
import logging

import pytest
from fastapi.testclient import TestClient

from app import main, risco
from app.config import ConfigIncompleta
from app.main import app

# Frase fictícia de risco da suíte (tests/casos_risco.yaml).
FRASE_DE_RISCO = "ele está aqui em casa com uma faca"
ROTAS = [("/juridico", "pergunta"), ("/mensagem", "texto")]


def nao_pode_ser_chamado(nome):
    def falhar():
        raise AssertionError(f"{nome} não deveria ser usado quando há risco imediato")

    return falhar


@pytest.fixture
def cliente():
    originais = main.cliente_llm, main.indice_juridico
    main.cliente_llm = nao_pode_ser_chamado("o LLM")
    main.indice_juridico = nao_pode_ser_chamado("o índice")
    yield TestClient(app)
    main.cliente_llm, main.indice_juridico = originais


@pytest.mark.parametrize("rota, campo", ROTAS)
def test_frase_de_risco_responde_so_o_alerta_sem_llm_nem_indice(cliente, rota, campo):
    resposta = cliente.post(rota, json={campo: FRASE_DE_RISCO})

    assert resposta.status_code == 200
    assert resposta.json() == {"risco_imediato": True, "categoria": "arma", "resposta": risco.ALERTA}
    assert "190" in risco.ALERTA and "180" in risco.ALERTA
    assert resposta.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("rota, campo", ROTAS)
def test_alerta_funciona_sem_llm_configurado(cliente, rota, campo):
    def sem_config():
        raise ConfigIncompleta("Variável de ambiente não definida: LLM_MODEL")

    main.cliente_llm = sem_config
    resposta = cliente.post(rota, json={campo: "ELE VAI ME MATAH"})
    assert resposta.status_code == 200
    assert resposta.json()["risco_imediato"] is True


@pytest.mark.parametrize("rota, campo", ROTAS)
def test_frase_sem_risco_segue_para_o_llm(cliente, rota, campo):
    chamado = []

    class LLMFalso:
        def responder(self, mensagens, **_):
            chamado.append(True)
            return "Resposta fictícia (Lei 11.340/2006, art. 7º)."

    class IndiceFalso:
        def buscar(self, pergunta, k=5, eixos=None):
            trecho = {"lei": "Lei 11.340/2006", "artigo": "7", "texto": "Texto fictício.",
                      "url": "https://www.planalto.gov.br/exemplo.htm", "data_acesso": "2026-11-03"}  # fmt: skip
            return [(trecho, 0.9)]

    main.cliente_llm = LLMFalso
    main.indice_juridico = IndiceFalso
    resposta = cliente.post(rota, json={campo: "o que é medida protetiva?"})
    assert resposta.status_code == 200
    assert "risco_imediato" not in resposta.json()
    assert chamado == [True]


def test_alerta_nao_registra_o_texto_no_log(cliente, caplog):
    with caplog.at_level(logging.DEBUG):
        cliente.post("/juridico", json={"pergunta": FRASE_DE_RISCO})
    log = "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))
    assert "POST /juridico 200" in log
    assert "faca" not in log
