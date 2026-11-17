"""Etapa de regra do orquestrador e campos do texto (s4-orquestrador-agentes, tarefas 2.1 e 2.2)."""
import json
import typing
from pathlib import Path

import pytest

from app.orquestrador import (
    ARQUIVO_ROTEAMENTO,
    RAS_DO_SITE,
    Agente,
    Beneficio,
    campos_do_texto,
    por_regra,
    varias_perguntas,
)

ROTEAMENTO = json.loads(ARQUIVO_ROTEAMENTO.read_text(encoding="utf-8"))
EXEMPLOS = json.loads((Path(__file__).parent / "orquestrar_exemplos.json").read_text(encoding="utf-8"))["exemplos"]


# --- 2.1: regra de roteamento -------------------------------------------------------------------


def test_arquivo_de_regras_cobre_os_agentes_e_os_campos():
    # fora_do_tema não tem palavras: só o LLM escolhe esse agente.
    assert set(ROTEAMENTO["agentes"]) == set(typing.get_args(Agente)) - {"fora_do_tema"}
    assert set(ROTEAMENTO["beneficios"]) == set(typing.get_args(Beneficio))
    assert tuple(ROTEAMENTO["ras"]) == RAS_DO_SITE


@pytest.mark.parametrize(
    "texto, agente, tipo",
    [
        ("onde fica a delegacia da mulher?", "rede", None),
        ("como peço medida protetiva?", "juridico", None),
        ("isso que ele faz é crime?", "juridico", None),
        ("será que eu corro perigo?", "triagem", None),
        ("Tenho direito ao Bolsa Família?", "beneficios", "direito"),
        ("como funciona o cartão gás?", "beneficios", "explicacao"),
        ("como peço medida protetiva??", "juridico", None),
    ],
)
def test_regra_decide_com_um_agente(texto, agente, tipo):
    decisao = por_regra(texto)
    assert decisao is not None
    assert (decisao.agente, decisao.tipo) == (agente, tipo)


@pytest.mark.parametrize(
    "texto",
    [
        "onde fica a delegacia pra pedir medida protetiva?",
        "tenho direito ao bolsa família se eu pedir o divórcio?",
    ],
)
def test_regra_nao_decide_com_dois_agentes(texto):
    assert por_regra(texto) is None


@pytest.mark.parametrize(
    "texto",
    [
        "o que é medida protetiva? quanto tempo ela dura?",
        "como peço medida protetiva, e também quanto tempo ela dura",
        "como peço medida protetiva. outra coisa: ela vale em outro estado",
        "como peço medida protetiva, além disso ela vale em outro estado",
        "o que é medida protetiva e onde eu peço ela?",
    ],
)
def test_regra_nao_decide_com_varias_perguntas(texto):
    # Todos casam só o jurídico: quem impede a regra é a marca de várias perguntas.
    assert varias_perguntas(texto)
    assert por_regra(texto) is None


@pytest.mark.parametrize(
    "texto, agente, tipo",
    [
        ("como funciona o aluguel da maria da penha?", "juridico", None),
        ("o que é o auxílio-aluguel?", "juridico", None),
        ("o juiz pode me dar o aluguel do juiz?", "juridico", None),
        ("tenho direito ao auxílio-aluguel?", "beneficios", "direito"),
        ("posso receber o aluguel da lei maria da penha?", "beneficios", "direito"),
    ],
)
def test_par_do_auxilio_aluguel(texto, agente, tipo):
    decisao = por_regra(texto)
    assert (decisao.agente, decisao.tipo) == (agente, tipo)
    assert decisao.campos.beneficio == "auxilio_aluguel"


@pytest.mark.parametrize(
    "texto, tipo",
    [
        ("como funciona o aluguel social do DF?", "explicacao"),
        ("tenho direito ao auxílio aluguel social?", "direito"),
    ],
)
def test_aluguel_social_vai_para_beneficios(texto, tipo):
    decisao = por_regra(texto)
    assert (decisao.agente, decisao.tipo) == ("beneficios", tipo)
    assert decisao.campos.beneficio == "aluguel_social_df"


def test_sem_palavra_de_agente_o_llm_escolhe():
    assert por_regra("qual a previsão do tempo amanhã?") is None


@pytest.mark.parametrize(
    "exemplo",
    [e for e in EXEMPLOS if e["status"] == 200 and e["resposta"]["agente"]],
    ids=lambda e: e["nome"],
)
def test_exemplos_do_contrato_batem_com_a_regra(exemplo):
    # Os exemplos marcados "regra" são decididos assim pela regra real; os demais vão ao LLM.
    corpo = exemplo["resposta"]
    decisao = por_regra(exemplo["pedido"]["texto"])
    if corpo["decidido_por"] != "regra":
        assert decisao is None
        return
    assert decisao.agente == corpo["agente"]
    assert decisao.tipo == corpo["tipo"]
    assert decisao.campos.model_dump() == corpo["campos"]


# --- 2.2: campos do texto -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto, ra",
    [
        ("moro em ceilandia, onde tem delegacia?", "Ceilândia"),
        ("sou da ASA SUL", "Plano Piloto"),
        ("moro em são sebastião", "São Sebastião"),
        ("moro na estrutural", "Estrutural (SCIA)"),
        ("moro em sobradinho", "Sobradinho"),
    ],
)
def test_ra_da_lista_do_site(texto, ra):
    assert campos_do_texto(texto).ra == ra


@pytest.mark.parametrize(
    "texto",
    [
        "moro no sol nascente",
        "moro em vicente pires",
        "moro em sobradinho 2",
        "moro em goiânia",
        "moro em ceilandia mas trabalho em taguatinga",
    ],
)
def test_ra_fora_da_lista_ou_ambigua_fica_nula(texto):
    assert campos_do_texto(texto).ra is None


@pytest.mark.parametrize(
    "texto, beneficio",
    [
        ("tenho direito ao bolsa família?", "bolsa_familia"),
        ("o bpc é pra quem?", "bpc"),
        ("tenho direito ao auxílio-aluguel?", "auxilio_aluguel"),
        ("como funciona o auxílio aluguel social?", "aluguel_social_df"),
        ("tenho direito ao cartão gás?", "outro"),
        ("como saco meu fgts?", "outro"),
        ("tenho direito a algum auxílio?", None),
        ("tenho direito ao bolsa família ou ao bpc?", None),
    ],
)
def test_beneficio_do_texto(texto, beneficio):
    assert campos_do_texto(texto).beneficio == beneficio


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("fui estuprada ontem, onde posso ser atendida?", True),
        ("fui abusada e não sei o que fazer", True),
        ("ele me forçou a transar há 2 anos", False),
        ("sofri violência sexual quando eu era criança", False),
        ("ele me xinga todo dia", None),
    ],
)
def test_violencia_sexual_recente(texto, esperado):
    assert campos_do_texto(texto).violencia_sexual_recente is esperado
