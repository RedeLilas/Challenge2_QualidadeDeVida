"""PWA servida pelo FastAPI e rota de mensagem (tarefas 2.1 a 2.3 de s2-plataforma-base)."""
import json
import logging
import re

import pytest
from fastapi.testclient import TestClient

from app import llm, main
from app.config import TIMEOUT_PADRAO, ConfigIncompleta
from app.main import app

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
    # As rotas chamam main.cliente_llm() depois da checagem de risco; os testes trocam a função.
    original = main.cliente_llm
    yield TestClient(app)
    main.cliente_llm = original


def usar(llm_falso):
    main.cliente_llm = lambda: llm_falso
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


def test_tela_espera_mais_que_o_servidor(cliente):
    # O servidor desiste primeiro e devolve a mensagem com o Ligue 180; o limite da tela
    # é só a rede de segurança para quando a conexão cai.
    codigo = cliente.get("/app.js").text
    limite_ms = int(re.search(r"const TEMPO_LIMITE_MS = (\d+);", codigo).group(1))
    assert TIMEOUT_PADRAO * 1000 < limite_ms <= TIMEOUT_PADRAO * 1000 + 10_000


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

    main.cliente_llm = sem_config
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


def test_tela_usa_a_rota_juridica_e_mostra_fontes_sem_link(cliente):
    # s2-rag-juridico, tarefa 2.4: toda mensagem vai para /juridico (decisão de 05/11, até a S4).
    codigo = cliente.get("/app.js").text
    assert 'const ROTA = "/juridico";' in codigo
    assert "JSON.stringify({ pergunta: texto })" in codigo
    assert "texto verificado em" in codigo
    # Sem link para sites (a página da lei ficaria no histórico do navegador); só tel:190 e tel:180.
    assert "planalto" not in codigo
    assert set(re.findall(r'\.href = "([^"]*)"', codigo)) == {"tel:190", "tel:180"}


def test_alerta_de_190_na_tela_antes_do_envio_e_offline(cliente):
    # s2-alerta-risco-190, tarefas 2.2 e 2.3. A paridade com o servidor está em test_risco_js.py.
    html = cliente.get("/").text
    assert html.index('src="/risco.js"') < html.index('src="/app.js"')
    codigo = cliente.get("/app.js").text
    # A checagem local vem antes do aviso de "sem internet" e do envio ao servidor.
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("if (!navigator.onLine)")
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("await fetch(ROTA")
    assert "dados.risco_imediato" in codigo  # o servidor também pode mandar o alerta
    sw = cliente.get("/sw.js").text
    assert '"/risco.js"' in sw and '"/regras/risco_imediato.json"' in sw
    regras = cliente.get("/regras/risco_imediato.json")
    assert regras.status_code == 200 and regras.json()["regras"]
