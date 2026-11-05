"""PWA servida pelo FastAPI e rota de mensagem (tarefas 2.1 a 2.3 de s2-plataforma-base)."""
import json
import logging

import pytest
from fastapi.testclient import TestClient

from app import llm
from app.config import ConfigIncompleta
from app.main import app, cliente_llm

# Frase fictícia: nunca usar relatos reais em testes.
PERGUNTA = "Pergunta fictícia de teste sobre auxílio"


class LLMFalso:
    def __init__(self, resposta="Resposta fictícia.", erro=None):
        self.resposta, self.erro, self.recebido = resposta, erro, None

    def responder(self, mensagens):
        self.recebido = mensagens
        if self.erro:
            raise self.erro
        return self.resposta


@pytest.fixture
def cliente():
    yield TestClient(app)
    app.dependency_overrides.clear()


def usar(llm_falso):
    app.dependency_overrides[cliente_llm] = lambda: llm_falso
    return llm_falso


def test_raiz_serve_a_tela_de_conversa(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert "<title>Anotações</title>" in resposta.text
    assert 'id="sair"' in resposta.text


@pytest.mark.parametrize("caminho", ["/app.js", "/styles.css", "/sw.js", "/icones/icone-192.png", "/icones/icone-512.png"])
def test_arquivos_da_interface(cliente, caminho):
    assert cliente.get(caminho).status_code == 200


def test_manifest_discreto_e_instalavel(cliente):
    resposta = cliente.get("/manifest.webmanifest")
    assert resposta.headers["content-type"].startswith("application/manifest+json")
    manifest = json.loads(resposta.text)
    assert manifest["display"] == "standalone"
    assert {"192x192", "512x512"} <= {icone["sizes"] for icone in manifest["icons"]}
    visivel = " ".join([manifest["name"], manifest["short_name"], manifest["description"]]).lower()
    for palavra in ("violência", "mulher", "denúncia", "lilás", "rede"):
        assert palavra not in visivel


def test_service_worker_nao_guarda_a_conversa(cliente):
    sw = cliente.get("/sw.js")
    assert sw.headers["cache-control"] == "no-cache"
    assert '"/mensagem"' not in sw.text
    assert 'pedido.method !== "GET"' in sw.text


def test_interface_nao_usa_armazenamento_do_aparelho(cliente):
    codigo = cliente.get("/app.js").text + cliente.get("/sw.js").text
    for api in ("localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert f"{api}." not in codigo and f"{api}[" not in codigo


def test_saida_rapida_substitui_a_pagina(cliente):
    codigo = cliente.get("/app.js").text
    assert "location.replace(SITE_NEUTRO)" in codigo


def test_mensagem_responde_com_o_llm(cliente):
    falso = usar(LLMFalso("Resposta fictícia."))
    historico = [{"papel": "usuaria", "texto": "Oi"}, {"papel": "assistente", "texto": "Olá"}]
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA, "historico": historico})

    assert resposta.status_code == 200
    assert resposta.json() == {"resposta": "Resposta fictícia."}
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.headers["referrer-policy"] == "no-referrer"
    papeis = [m["role"] for m in falso.recebido]
    assert papeis == ["system", "user", "assistant", "user"]
    assert falso.recebido[-1]["content"] == PERGUNTA


def test_llm_indisponivel_indica_o_180(cliente):
    usar(LLMFalso(erro=llm.LLMIndisponivel("APITimeoutError")))
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA})
    assert resposta.status_code == 503
    assert "180" in resposta.json()["erro"]


def test_sem_configuracao_responde_indisponivel(cliente):
    def sem_config():
        raise ConfigIncompleta("Variável de ambiente não definida: LLM_MODEL")

    app.dependency_overrides[cliente_llm] = sem_config
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA})
    assert resposta.status_code == 503
    assert "LLM_MODEL" not in resposta.text


@pytest.mark.parametrize(
    "corpo",
    [{"texto": ""}, {"texto": "x" * 2001}, {"texto": "oi", "historico": [{"papel": "sistema", "texto": "x"}]}],
)
def test_mensagem_invalida(cliente, corpo):
    usar(LLMFalso())
    assert cliente.post("/mensagem", json=corpo).status_code == 422


def test_texto_da_mensagem_nao_vai_para_o_log(cliente, caplog):
    usar(LLMFalso())
    with caplog.at_level(logging.DEBUG):
        cliente.post("/mensagem", json={"texto": PERGUNTA})
    log = "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))
    assert "POST /mensagem 200" in log
    assert "auxílio" not in log
