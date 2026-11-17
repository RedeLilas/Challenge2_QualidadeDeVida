"""Rota POST /orquestrar: alerta, respostas e registro (s4-orquestrador-agentes, tarefas 3.1 a 3.3).

O índice e o LLM são simulados: nenhum teste carrega o modelo de embeddings nem chama um provedor.
Textos fictícios.
"""
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import llm, main, orquestrador, risco
from app.config import ConfigIncompleta
from app.main import app
from app.orquestrador import FORA_DO_TEMA, RespostaOrquestrar

EXEMPLOS = {
    e["nome"]: e
    for e in json.loads((Path(__file__).parent / "orquestrar_exemplos.json").read_text(encoding="utf-8"))["exemplos"]
}
COM_RISCO = "ele está aqui em casa com uma faca, como peço medida protetiva?"


def trecho(artigo, lei="Lei 11.340/2006"):
    return {
        "id": f"lei-11340-2006:art{artigo}", "norma_id": "lei-11340-2006", "eixo": "juridico", "lei": lei,
        "artigo": artigo, "citacao": f"{lei}, art. {artigo}", "capitulo": "", "texto": "Texto fictício.",
        "url": f"https://www.planalto.gov.br/exemplo.htm#art{artigo}", "data_acesso": "2026-11-03",
    }  # fmt: skip


class IndiceFalso:
    def __init__(self):
        self.chamadas = []

    def buscar(self, pergunta, k=5, eixos=None):
        self.chamadas.append({"pergunta": pergunta, "eixos": eixos})
        return [(trecho(a), 0.9) for a in ("19", "22", "7")]


class LLMRoteiro:
    """Devolve as saídas na ordem das chamadas (classificação e depois resposta) ou lança o erro."""

    def __init__(self, *saidas):
        self.saidas, self.chamadas = list(saidas), []

    def responder(self, mensagens, temperatura=0.2):
        self.chamadas.append(mensagens)
        saida = self.saidas.pop(0)
        if isinstance(saida, Exception):
            raise saida
        return saida


def nao_pode_ser_chamado(o_que):
    def falhar(*_args, **_kwargs):
        raise AssertionError(f"{o_que} não deveria ser usado")

    return falhar


def classificacao(*perguntas):
    itens = [
        {"agente": "juridico", "tipo": None, "pergunta": "?", "beneficio": None, "ra": None,
         "violencia_sexual_recente": None} | p
        for p in perguntas
    ]  # fmt: skip
    return json.dumps({"perguntas": itens}, ensure_ascii=False)


@pytest.fixture
def cliente():
    originais = main.cliente_llm, main.indice_juridico, orquestrador.explicar_beneficio
    yield TestClient(app)
    main.cliente_llm, main.indice_juridico, orquestrador.explicar_beneficio = originais


def usar(*saidas_llm):
    falso_llm, falso_indice = LLMRoteiro(*saidas_llm), IndiceFalso()
    main.cliente_llm = lambda: falso_llm
    main.indice_juridico = lambda: falso_indice
    return falso_llm, falso_indice


def sem_llm_nem_indice():
    main.cliente_llm = nao_pode_ser_chamado("o LLM")
    main.indice_juridico = nao_pode_ser_chamado("o índice")


def enviar(cliente, texto, **flags):
    resposta = cliente.post("/orquestrar", json={"texto": texto, **flags})
    if resposta.status_code == 200:
        RespostaOrquestrar.model_validate(resposta.json())
    return resposta


# --- 3.1: pedido, risco antes de tudo e alerta_visto ----------------------------------------------


@pytest.mark.parametrize(
    "corpo",
    [
        {"texto": "como peço medida protetiva?", "perfil": {"ra": "Ceilândia"}},
        {"texto": "como peço medida protetiva?", "historico": []},
        {"texto": ""},
        {"texto": "x" * 2001},
        {},
    ],
)
def test_pedido_fora_do_contrato_da_422(cliente, corpo):
    sem_llm_nem_indice()
    assert cliente.post("/orquestrar", json=corpo).status_code == 422


def test_risco_sem_alerta_visto_devolve_so_o_alerta(cliente):
    sem_llm_nem_indice()
    resposta = enviar(cliente, COM_RISCO)
    assert resposta.status_code == 200
    assert resposta.headers["Cache-Control"] == "no-store"
    assert resposta.json() == EXEMPLOS["alerta_sem_alerta_visto"]["resposta"]


def test_risco_com_alerta_visto_responde_com_o_risco_junto(cliente):
    falso_llm, _ = usar("A medida protetiva é concedida pelo juiz (Lei 11.340/2006, art. 19).")
    corpo = enviar(cliente, COM_RISCO, alerta_visto=True).json()
    assert corpo["risco_imediato"] is True
    assert corpo["alerta"] == risco.ALERTA and corpo["categoria_risco"] == "arma"
    assert corpo["agente"] == "juridico" and corpo["decidido_por"] == "regra"
    assert corpo["resposta"]["citacoes"][0]["citacao"] == "Lei 11.340/2006, art. 19"
    # A regra decidiu: o LLM só foi chamado para a resposta jurídica, não para classificar.
    assert len(falso_llm.chamadas) == 1


def test_sem_risco_a_resposta_nao_traz_alerta(cliente):
    usar("A medida protetiva é concedida pelo juiz (Lei 11.340/2006, art. 19).")
    corpo = enviar(cliente, "como peço medida protetiva?").json()
    assert (corpo["risco_imediato"], corpo["alerta"], corpo["categoria_risco"]) == (False, None, None)


# --- 3.2: respostas no mesmo pedido ---------------------------------------------------------------


def test_juridico_responde_com_responder_e_citacoes(cliente):
    _, falso_indice = usar("A medida protetiva é concedida pelo juiz (Lei 11.340/2006, art. 19).")
    corpo = enviar(cliente, "como peço medida protetiva?").json()
    assert corpo["resposta"]["recusada"] is False
    assert corpo["resposta"]["citacoes"][0]["citacao"] == "Lei 11.340/2006, art. 19"
    assert falso_indice.chamadas == [{"pergunta": "como peço medida protetiva?", "eixos": {"juridico"}}]


def test_fora_do_tema_usa_o_texto_fixo_sem_indice_nem_llm_de_resposta(cliente):
    main.indice_juridico = nao_pode_ser_chamado("o índice")
    falso_llm = LLMRoteiro(classificacao({"agente": "fora_do_tema", "pergunta": "Vai chover amanhã?"}))
    main.cliente_llm = lambda: falso_llm
    corpo = enviar(cliente, "qual a previsão do tempo amanhã?").json()
    assert corpo["resposta"] == {"resposta": FORA_DO_TEMA, "citacoes": [], "recusada": True, "aviso": None}
    assert len(falso_llm.chamadas) == 1  # só a classificação
    assert corpo == EXEMPLOS["fora_do_tema"]["resposta"]


def test_explicacao_de_beneficio_vai_ao_juridico_sem_o_rag_de_beneficios(cliente):
    orquestrador.explicar_beneficio = None
    _, falso_indice = usar("O juiz pode conceder (Lei 11.340/2006, art. 22).")
    corpo = enviar(cliente, "como funciona o cartão gás?").json()
    assert (corpo["agente"], corpo["tipo"]) == ("beneficios", "explicacao")
    assert falso_indice.chamadas[0]["eixos"] == {"juridico"}
    assert corpo["resposta"] is not None


def test_explicacao_de_beneficio_usa_rag_de_beneficios_nos_eixos_e_limite_proprios(cliente):
    class IndiceBeneficios:
        def __init__(self, similaridade=0.9):
            self.similaridade = similaridade
            self.chamadas = []

        def buscar(self, pergunta, k=5, eixos=None):
            self.chamadas.append({"pergunta": pergunta, "k": k, "eixos": eixos})
            return [
                (
                    {
                        "id": "lei-distrital-6938-2021:art1",
                        "norma_id": "lei-distrital-6938-2021",
                        "eixo": "df",
                        "lei": "Lei Distrital 6.938/2021",
                        "artigo": "1",
                        "citacao": "Lei Distrital 6.938/2021, art. 1º",
                        "capitulo": "",
                        "texto": "Texto fictício.",
                        "url": "https://www.sinj.df.gov.br/exemplo.html#art1",
                        "data_acesso": "2026-11-03",
                    },
                    self.similaridade,
                )
            ]

    falso_llm = LLMRoteiro(
        "O Cartão Gás auxilia na compra do botijão (Lei Distrital 6.938/2021, art. 1º). "
        "Consulte a tela Benefícios ou procure o CRAS."
    )
    falso_indice = IndiceBeneficios(similaridade=0.9)
    main.cliente_llm = lambda: falso_llm
    main.indice_juridico = lambda: falso_indice

    corpo = enviar(cliente, "como funciona o cartão gás?").json()
    assert (corpo["agente"], corpo["tipo"]) == ("beneficios", "explicacao")
    assert falso_indice.chamadas == [
        {"pergunta": "como funciona o cartão gás?", "k": 5, "eixos": {"beneficios", "df"}}
    ]
    assert corpo["resposta"]["recusada"] is False
    assert corpo["resposta"]["citacoes"][0]["citacao"] == "Lei Distrital 6.938/2021, art. 1º"
    assert corpo["resposta"]["aviso"] == "Valores e regras podem mudar por decreto. Norma consultada em 03/11/2026."

    # Similaridade 0,812 passa no 0,81 do jurídico, mas é barrada pelo LIMITE_BENEFICIOS (0,815) sem chamar o LLM.
    main.cliente_llm = nao_pode_ser_chamado("o LLM")
    main.indice_juridico = lambda: IndiceBeneficios(similaridade=0.812)
    corpo_recusado = enviar(cliente, "como funciona o cartão gás?").json()
    assert corpo_recusado["resposta"]["recusada"] is True
    assert "CRAS" in corpo_recusado["resposta"]["resposta"]
    assert corpo_recusado["resposta"]["aviso"] is None


def test_explicacao_de_beneficio_usa_o_ponto_de_troca(cliente):
    falso_llm, falso_indice = usar()
    recebido = {}

    def explicar(pergunta, indice, cliente_llm):
        recebido.update(pergunta=pergunta, indice=indice, cliente=cliente_llm)
        return {"resposta": "Explicação.", "citacoes": [], "recusada": True, "aviso": "Norma consultada em 03/11/2026."}

    orquestrador.explicar_beneficio = explicar
    corpo = enviar(cliente, "como funciona o cartão gás?").json()
    assert recebido["pergunta"] == "como funciona o cartão gás?" and recebido["indice"] is falso_indice
    assert corpo["resposta"]["aviso"] == "Norma consultada em 03/11/2026."


def test_llm_fora_do_ar_na_resposta_juridica_da_503(cliente):
    usar(llm.LLMIndisponivel("APITimeoutError"))
    resposta = cliente.post("/orquestrar", json={"texto": "como peço medida protetiva?"})
    assert resposta.status_code == 503
    assert resposta.json() == {"erro": main.INDISPONIVEL}


def test_llm_fora_do_ar_na_classificacao_cai_no_juridico(cliente):
    _, falso_indice = usar(llm.LLMIndisponivel("APITimeoutError"), "Resposta (Lei 11.340/2006, art. 7).")
    corpo = enviar(cliente, "ele fica olhando meu celular escondido, pode isso?").json()
    assert (corpo["decidido_por"], corpo["agente"]) == ("reserva", "juridico")
    assert falso_indice.chamadas


def test_varias_perguntas_respondem_a_reescrita_e_sugerem_a_outra(cliente):
    _, falso_indice = usar(
        classificacao(
            {"agente": "juridico", "pergunta": "O que é medida protetiva?"},
            {"agente": "juridico", "pergunta": "Onde posso pedir medida protetiva no DF?"},
        ),
        "É uma ordem do juiz (Lei 11.340/2006, art. 22).",
    )
    corpo = enviar(cliente, "o que é medida protetiva e onde eu peço ela?").json()
    assert falso_indice.chamadas[0]["pergunta"] == "O que é medida protetiva?"
    assert corpo["outras_perguntas"] == ["Onde posso pedir medida protetiva no DF?"]


@pytest.mark.parametrize(
    "nome",
    [
        "beneficios_direito",
        "beneficios_direito_sem_beneficio",
        "beneficios_direito_outro",
        "triagem",
        "rede_com_ra",
        "rede_violencia_sexual",
    ],
)
def test_agentes_do_aparelho_respondem_sem_llm_e_sem_indice(cliente, nome):
    # Mesmo sem LLM configurado, a rota devolve exatamente o exemplo do contrato.
    def sem_config():
        raise ConfigIncompleta("LLM_BASE_URL")

    main.cliente_llm = sem_config
    main.indice_juridico = nao_pode_ser_chamado("o índice")
    exemplo = EXEMPLOS[nome]
    corpo = enviar(cliente, **exemplo["pedido"]).json()
    assert corpo == exemplo["resposta"]


# --- 3.3: registro do roteamento sem texto -------------------------------------------------------


def _log(caplog):
    return "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))


def test_registro_tem_so_quem_decidiu_e_o_agente(cliente, caplog):
    # Dois "?": a regra não decide, e o texto vai ao LLM, que reescreve e tira os campos.
    texto = "MARCADOR-XYZ moro em ceilandia? e o bolsa família, pode?"
    usar(
        classificacao(
            {"agente": "beneficios", "tipo": "direito", "pergunta": "PERGUNTA-REESCRITA-ABC?",
             "beneficio": "bolsa_familia", "ra": "Ceilândia", "violencia_sexual_recente": True},
            {"agente": "rede", "pergunta": "SUGESTAO-DEF?"},
        )
    )  # fmt: skip
    with caplog.at_level(logging.DEBUG):
        enviar(cliente, texto)
    log = _log(caplog)
    assert "roteamento decidido_por=llm agente=beneficios" in log
    for proibido in ("MARCADOR", "ceilandia", "Ceilândia", "bolsa", "REESCRITA", "SUGESTAO", "True"):
        assert proibido not in log


def test_registro_da_regra_e_do_alerta(cliente, caplog):
    sem_llm_nem_indice()
    with caplog.at_level(logging.DEBUG):
        enviar(cliente, "onde fica a delegacia da mulher?")
        enviar(cliente, COM_RISCO)
    log = _log(caplog)
    assert "roteamento decidido_por=regra agente=rede" in log
    assert "delegacia" not in log and "faca" not in log
    # Só o alerta: não houve roteamento para registrar.
    assert log.count("roteamento") == 1
