import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logs import registrar_requisicao
from app.main import app as app_real

# Frase fictícia: nunca usar relatos reais em testes.
MENSAGEM = "Frase fictícia de teste: ele quebrou meu celular ontem"


def log_do_servidor(caplog) -> str:
    # O httpx do TestClient registra a URL que ele mesmo chamou; isso é o lado do cliente.
    return "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))


@pytest.fixture
def cliente():
    app = FastAPI()
    app.middleware("http")(registrar_requisicao)

    @app.post("/mensagem")
    def mensagem(corpo: dict) -> dict:
        return {"recebido": True}

    @app.post("/falha")
    def falha(corpo: dict) -> dict:
        # Exceção carregando o texto: o log não pode repeti-lo.
        raise ValueError(corpo["texto"])

    return TestClient(app)


def test_mensagem_nao_aparece_no_log(cliente, caplog):
    with caplog.at_level(logging.DEBUG):
        resposta = cliente.post("/mensagem", json={"texto": MENSAGEM})

    assert resposta.status_code == 200
    assert "POST /mensagem 200" in log_do_servidor(caplog)
    assert MENSAGEM not in log_do_servidor(caplog)
    assert "celular" not in log_do_servidor(caplog)


def test_query_string_nao_aparece_no_log(cliente, caplog):
    with caplog.at_level(logging.DEBUG):
        cliente.post("/mensagem?q=celular", json={"texto": "x"})

    assert "POST /mensagem 200" in log_do_servidor(caplog)
    assert "celular" not in log_do_servidor(caplog)


def test_erro_registra_tipo_e_rota_sem_conteudo(cliente, caplog):
    with caplog.at_level(logging.DEBUG):
        resposta = cliente.post("/falha", json={"texto": MENSAGEM})

    assert resposta.status_code == 500
    assert MENSAGEM not in resposta.text
    assert "POST /falha 500" in log_do_servidor(caplog)
    assert "ValueError" in log_do_servidor(caplog)
    assert "celular" not in log_do_servidor(caplog)


def test_app_real_usa_o_middleware(caplog):
    with caplog.at_level(logging.INFO, logger="rede_lilas.http"):
        TestClient(app_real).get("/saude")
    assert "GET /saude 200" in log_do_servidor(caplog)
