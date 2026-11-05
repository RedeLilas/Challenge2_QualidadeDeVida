"""Rota de pergunta jurídica e verificação de citação (s2-rag-juridico, tarefas 2.1 e 2.2).

O índice e o LLM são simulados: os testes não carregam o modelo de embeddings nem chamam o Ollama.
"""
import logging

import pytest
from fastapi.testclient import TestClient

from app import llm
from app.main import app, cliente_llm, indice_juridico
from app.rag.resposta import RECUSA, extrair_referencias

# Pergunta fictícia: nunca usar relatos reais em testes.
PERGUNTA = "Pergunta fictícia: ele quebrou meu celular, isso é violência?"


def trecho(lei, artigo, texto="Texto fictício do dispositivo.", norma_id="lei-11340-2006"):
    sufixo = "º" if artigo.isdigit() and int(artigo) < 10 else ""
    return {
        "id": f"{norma_id}:art{artigo}",
        "norma_id": norma_id,
        "eixo": "juridico",
        "lei": lei,
        "artigo": artigo,
        "citacao": f"{lei}, art. {artigo}{sufixo}",
        "capitulo": "",
        "texto": texto,
        "url": f"https://www.planalto.gov.br/exemplo.htm#art{artigo}",
        "data_acesso": "2026-11-03",
    }


RECUPERADOS = [
    trecho("Lei 11.340/2006", "7", "Art. 7º São formas de violência ... IV - a violência patrimonial ..."),
    trecho("Lei 11.340/2006", "5"),
    trecho("Lei 11.340/2006", "22"),
    trecho("Código Penal", "147", norma_id="decreto-lei-2848-1940"),
    trecho("Lei 11.340/2006", "24-A"),
]


class IndiceFalso:
    def __init__(self, trechos=RECUPERADOS):
        self.trechos, self.chamadas = trechos, []

    def buscar(self, pergunta, k=5, eixos=None):
        self.chamadas.append({"pergunta": pergunta, "k": k, "eixos": eixos})
        return [(t, 0.9 - i * 0.01) for i, t in enumerate(self.trechos[:k])]


class LLMFalso:
    def __init__(self, resposta="", erro=None):
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


def usar(resposta_llm="", erro=None, indice=None):
    falso_llm, falso_indice = LLMFalso(resposta_llm, erro), indice or IndiceFalso()
    app.dependency_overrides[cliente_llm] = lambda: falso_llm
    app.dependency_overrides[indice_juridico] = lambda: falso_indice
    return falso_llm, falso_indice


# --- 2.1: rota de pergunta jurídica -------------------------------------------------------


def test_responde_com_resposta_e_citacoes(cliente):
    usar("Quebrar suas coisas pode ser violência patrimonial (Lei 11.340/2006, art. 7º, IV).")
    resposta = cliente.post("/juridico", json={"pergunta": PERGUNTA})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["recusada"] is False
    assert "violência patrimonial" in corpo["resposta"]
    assert corpo["citacoes"] == [
        {
            "lei": "Lei 11.340/2006",
            "artigo": "7",
            "citacao": "Lei 11.340/2006, art. 7º",
            "url": "https://www.planalto.gov.br/exemplo.htm#art7",
            "data_acesso": "2026-11-03",
        }
    ]
    assert resposta.headers["cache-control"] == "no-store"


def test_busca_5_trechos_so_no_eixo_juridico(cliente):
    _, indice = usar("Resposta (Lei 11.340/2006, art. 7º).")
    cliente.post("/juridico", json={"pergunta": PERGUNTA})
    assert indice.chamadas == [{"pergunta": PERGUNTA, "k": 5, "eixos": {"juridico"}}]


def test_prompt_leva_os_trechos_recuperados_e_a_pergunta(cliente):
    falso, _ = usar("Resposta (Lei 11.340/2006, art. 7º).")
    cliente.post("/juridico", json={"pergunta": PERGUNTA})

    sistema, usuaria = falso.recebido
    assert sistema["role"] == "system" and usuaria["role"] == "user"
    assert "(Lei 11.340/2006, art. 7º)" in sistema["content"]  # formato de citação pedido
    assert PERGUNTA in usuaria["content"]
    for t in RECUPERADOS:
        assert t["texto"] in usuaria["content"]
    assert "[Código Penal, art. 147]" in usuaria["content"]


def test_varias_citacoes_validas_sem_repetir(cliente):
    usar(
        "Pode ser violência (Lei 11.340/2006, art. 7º). O juiz pode afastá-lo (Lei 11.340/2006, art. 22, III). "
        "Ameaça é crime (Código Penal, art. 147). De novo: art. 7º da Lei Maria da Penha."
    )
    corpo = cliente.post("/juridico", json={"pergunta": PERGUNTA}).json()
    assert corpo["recusada"] is False
    assert [(c["lei"], c["artigo"]) for c in corpo["citacoes"]] == [
        ("Lei 11.340/2006", "7"),
        ("Lei 11.340/2006", "22"),
        ("Código Penal", "147"),
    ]


def test_llm_indisponivel_indica_o_180(cliente):
    usar(erro=llm.LLMIndisponivel("APITimeoutError"))
    resposta = cliente.post("/juridico", json={"pergunta": PERGUNTA})
    assert resposta.status_code == 503
    assert "180" in resposta.json()["erro"]


@pytest.mark.parametrize("corpo", [{"pergunta": ""}, {"pergunta": "x" * 2001}, {}])
def test_pergunta_invalida(cliente, corpo):
    usar("Resposta (Lei 11.340/2006, art. 7º).")
    assert cliente.post("/juridico", json=corpo).status_code == 422


def test_pergunta_nao_vai_para_o_log(cliente, caplog):
    usar("Resposta (Lei 11.340/2006, art. 7º).")
    with caplog.at_level(logging.DEBUG):
        cliente.post("/juridico", json={"pergunta": PERGUNTA})
    log = "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))
    assert "POST /juridico 200" in log
    assert "celular" not in log


# --- 2.2: verificação de citação ----------------------------------------------------------


@pytest.mark.parametrize(
    "resposta_llm",
    [
        # Artigo que não está entre os recuperados (o 7º, o 5º, o 22, o 24-A e o 147 do CP estão).
        "Ele pode ser preso na hora (Lei 11.340/2006, art. 20).",
        # Artigo recuperado, mas atribuído à lei errada.
        "Isso é crime (Código Penal, art. 7º).",
        # Lei fora da base.
        "A Constituição garante isso (Constituição Federal, art. 226).",
        # Uma citação certa e outra inventada: descarta a resposta inteira.
        "É violência (Lei 11.340/2006, art. 7º) e cabe prisão (Lei 11.340/2006, art. 20).",
        # Lista de artigos com um que não foi recuperado.
        "Veja os arts. 22 e 23 da Lei Maria da Penha.",
        # Sem nenhuma citação: a spec exige citação em toda resposta jurídica.
        "Sim, isso é violência e você pode pedir ajuda.",
    ],
    ids=["artigo-nao-recuperado", "lei-errada", "lei-fora-da-base", "uma-inventada", "lista", "sem-citacao"],
)
def test_resposta_com_citacao_nao_sustentada_e_descartada(cliente, resposta_llm):
    usar(resposta_llm)
    resposta = cliente.post("/juridico", json={"pergunta": PERGUNTA})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo == {"resposta": RECUSA, "citacoes": [], "recusada": True}
    # Nada do texto descartado chega à usuária.
    assert resposta_llm not in resposta.text
    assert "180" in RECUSA and "Defensoria Pública do DF" in RECUSA


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("(Lei 11.340/2006, art. 7º, IV)", [("Lei 11.340/2006", "7")]),
        ("segundo o artigo 5 da Lei Maria da Penha", [("Lei 11.340/2006", "5")]),
        ("o Art. 24-a da Lei nº 11.340", [("Lei 11.340/2006", "24-A")]),
        ("art. 129, § 9º, do Código Penal", [("Código Penal", "129")]),
        ("(Lei 14.149/2021, art. 2°)", [("Lei 14.149/2021", "2")]),
        ("arts. 18, 19 e 22 da Lei 11.340/2006", [("Lei 11.340/2006", "18"), ("Lei 11.340/2006", "19"), ("Lei 11.340/2006", "22")]),
        ("como diz o art. 7º", [(None, "7")]),
        ("sem nenhuma referência", []),
    ],
)
def test_extrai_referencias(texto, esperado):
    assert extrair_referencias(texto, ["Lei 11.340/2006", "Lei 14.149/2021", "Código Penal"]) == esperado
