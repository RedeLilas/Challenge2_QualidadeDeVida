"""web/rede.js no QuickJS (s4-rede-atendimento, tarefas 2.1 e 2.2).

Faixas, CEPs e serviços são fictícios ou públicos (faixas dos Correios); nenhum dado de usuária.
"""
import json
import re
from pathlib import Path

import pytest
import quickjs

from scripts.validar_dados import RAS_OFICIAIS_DF

RAIZ = Path(__file__).resolve().parents[1]
FAIXAS = [
    {"cep_inicio": "70000-000", "cep_fim": "72799-999"},
    {"cep_inicio": "73000-000", "cep_fim": "73699-999"},
]
RAS_DO_SITE = re.findall(
    r'"([^"]+)"', re.search(r"var RAS_DF = \[(.*?)\];", (RAIZ / "web" / "dados.js").read_text(encoding="utf-8"), re.S).group(1)
)
RAS_DO_SITE = [ra for ra in RAS_DO_SITE if ra not in ("Outra RA do DF", "Prefiro não informar")]


@pytest.fixture(scope="module")
def js():
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "rede.js").read_text(encoding="utf-8"))
    contexto.eval(f"var FAIXAS = {json.dumps(FAIXAS)};")
    return contexto


def chamar(js, expressao):
    return json.loads(js.eval(f"JSON.stringify({expressao})"))


# --- cepParaRa: o CEP só diz se é do DF ---


@pytest.mark.parametrize(
    "cep, esperado",
    [
        ("70000-000", True),  # início da primeira faixa
        ("72215-110", True),  # meio da primeira faixa
        ("72799-999", True),  # fim da primeira faixa
        ("73000-000", True),  # início da segunda faixa
        ("73699-999", True),  # fim da segunda faixa
        ("72800-000", False),  # entre as duas faixas: não é do DF
        ("72999-999", False),
        ("73700-000", False),
        ("74000-000", False),  # Goiânia
        ("01310-100", False),  # São Paulo
    ],
)
def test_cep_dentro_ou_fora_do_df(js, cep, esperado):
    assert chamar(js, f"Rede.cepParaRa({json.dumps(cep)}, FAIXAS)") == {"dentroDF": esperado}


@pytest.mark.parametrize("cep", ["72215-110", "72.215-110", "72215110", " 72215-110 "])
def test_formatos_de_cep(js, cep):
    assert chamar(js, f"Rede.cepParaRa({json.dumps(cep)}, FAIXAS)") == {"dentroDF": True}


@pytest.mark.parametrize("valor", ["", "abc", "7221511", "722151100", None])
def test_texto_que_nao_e_cep_nao_diz_fora_do_df(js, valor):
    assert chamar(js, f"Rede.cepParaRa({json.dumps(valor)}, FAIXAS)") == {"dentroDF": None}


def test_sem_tabela_nao_decide(js):
    assert chamar(js, 'Rede.cepParaRa("72215-110", [])') == {"dentroDF": None}
    assert chamar(js, 'Rede.cepParaRa("72215-110")') == {"dentroDF": None}


# --- tirarCep: nenhum CEP sai do aparelho ---


@pytest.mark.parametrize(
    "texto, limpo",
    [
        ("meu cep é 72215-110, onde tem delegacia?", "meu cep é [CEP], onde tem delegacia?"),
        ("cep 72.215-110", "cep [CEP]"),
        ("cep 72215110.", "cep [CEP]."),
    ],
)
def test_tira_o_cep_do_texto(js, texto, limpo):
    assert chamar(js, f"Rede.tirarCep({json.dumps(texto)}, FAIXAS)") == {"texto": limpo, "dentroDF": True}


def test_cep_de_goiania_no_texto(js):
    resultado = chamar(js, 'Rede.tirarCep("moro no 74000-000", FAIXAS)')
    assert resultado == {"texto": "moro no [CEP]", "dentroDF": False}


def test_varios_ceps_saem_e_vale_o_primeiro(js):
    resultado = chamar(js, 'Rede.tirarCep("74000-000 ou 72215-110", FAIXAS)')
    assert resultado == {"texto": "[CEP] ou [CEP]", "dentroDF": False}


def test_texto_sem_cep(js):
    texto = "ligue (61) 3181-1474 ou 99117-3406; nasci em 12.05.1990"
    assert chamar(js, f"Rede.tirarCep({json.dumps(texto)}, FAIXAS)") == {"texto": texto, "dentroDF": None}


def test_numero_maior_que_cep_fica(js):
    texto = "protocolo 1234567890"
    assert chamar(js, f"Rede.tirarCep({json.dumps(texto)}, FAIXAS)")["texto"] == texto


# --- ordenar ---

SERVICOS = [
    {"nome": "CEAM Plano", "tipo": "CEAM", "ra": "Plano Piloto", "horario": "Segunda a sexta"},
    {"nome": "DEAM Plano", "tipo": "DEAM", "ra": "Plano Piloto", "horario": "24 horas, todos os dias"},
    {"nome": "CRAS Sol Nascente", "tipo": "CRAS", "ra": "Sol Nascente/Pôr do Sol", "horario": "Segunda a sexta"},
    {"nome": "CEAM Ceilândia", "tipo": "CEAM", "ra": "Ceilândia", "horario": "Segunda a sexta"},
    {"nome": "CEPAV Gama", "tipo": "Saúde", "ra": "Gama", "horario": "Segunda a sexta"},
    {"nome": "Juizado Samambaia", "tipo": "Juizado", "ra": "Samambaia", "horario": "Segunda a sexta"},
    {"nome": "CRAS Estrutural", "tipo": "CRAS", "ra": "SCIA/Estrutural", "horario": "Segunda a sexta"},
    {"nome": "DEAM Ceilândia", "tipo": "DEAM", "ra": "Ceilândia", "horario": "24 horas, todos os dias"},
]


def nomes(js, opcoes):
    return [s["nome"] for s in chamar(js, f"Rede.ordenar({json.dumps(SERVICOS)}, {json.dumps(opcoes)})")]


def test_mesma_ra_depois_ra_que_ordena_igual_depois_vizinhas(js):
    assert nomes(js, {"ra": "Ceilândia"}) == [
        "DEAM Ceilândia",  # mesma RA, plantão 24 horas primeiro
        "CEAM Ceilândia",
        "CRAS Sol Nascente",  # Sol Nascente ordena como Ceilândia
        "Juizado Samambaia",  # vizinha de maior fronteira
        "DEAM Plano",  # o resto: plantão 24 horas primeiro
        "CEAM Plano",
        "CEPAV Gama",
        "CRAS Estrutural",
    ]


def test_sem_violencia_sexual_saude_nao_sobe(js):
    assert nomes(js, {"ra": "Ceilândia", "violencia_sexual_recente": False})[0] == "DEAM Ceilândia"


@pytest.mark.parametrize("chave", ["violencia_sexual_recente", "violenciaSexualRecente"])
def test_violencia_sexual_recente_poe_a_saude_primeiro(js, chave):
    assert nomes(js, {"ra": "Ceilândia", chave: True})[:2] == ["CEPAV Gama", "DEAM Ceilândia"]


def test_sem_ra_plantoes_24_horas_primeiro(js):
    for ra in (None, "", "Outra RA do DF", "Prefiro não informar"):
        assert nomes(js, {"ra": ra})[:2] == ["DEAM Plano", "DEAM Ceilândia"]


def test_estrutural_com_os_dois_nomes(js):
    assert nomes(js, {"ra": "Estrutural (SCIA)"})[0] == "CRAS Estrutural"


def test_filtro_por_tipo(js):
    assert nomes(js, {"ra": "Plano Piloto", "tipo": "DEAM"}) == ["DEAM Plano", "DEAM Ceilândia"]


def test_ordenar_nao_muda_a_lista_recebida(js):
    js.eval(f"var LISTA = {json.dumps(SERVICOS)}; Rede.ordenar(LISTA, {{ ra: 'Ceilândia' }});")
    assert [s["nome"] for s in chamar(js, "LISTA")] == [s["nome"] for s in SERVICOS]


def test_entrada_vazia(js):
    assert chamar(js, "Rede.ordenar([], {})") == []
    assert chamar(js, "Rede.ordenar(null)") == []


# --- tabelas conferidas no mapa ---


def test_vizinhas_cobrem_as_17_ras_do_site_e_sao_simetricas(js):
    vizinhas = chamar(js, "Rede.VIZINHAS")
    assert sorted(vizinhas) == sorted(RAS_DO_SITE)
    for ra, lista in vizinhas.items():
        assert lista and len(lista) == len(set(lista)) and ra not in lista
        for outra in lista:
            assert outra in RAS_DO_SITE
            assert ra in vizinhas[outra], f"{ra} -> {outra} sem volta"


def test_toda_ra_oficial_tem_lugar_na_ordenacao(js):
    ordenacao = chamar(js, "Rede.RA_ORDENACAO")
    assert all(destino in RAS_DO_SITE for destino in ordenacao.values())
    nomes_do_site = {"Estrutural (SCIA)": "SCIA/Estrutural"}
    cobertas = {nomes_do_site.get(ra, ra) for ra in RAS_DO_SITE} | set(ordenacao)
    assert cobertas == RAS_OFICIAIS_DF


# --- texto de saúde (tarefa 2.2) ---


@pytest.mark.parametrize("chamada", ["Rede.textoSaude(false)", "Rede.textoSaude({ ajudando: false })", "Rede.textoSaude()"])
def test_texto_saude_para_ela(js, chamada):
    texto = js.eval(chamada)
    assert "você tem direito" in texto and "pessoa que você está ajudando" not in texto


@pytest.mark.parametrize("chamada", ["Rede.textoSaude(true)", "Rede.textoSaude({ ajudando: true })"])
def test_texto_saude_ajudando(js, chamada):
    texto = js.eval(chamada)
    assert "a pessoa que você está ajudando tem direito" in texto and "se ela quiser" in texto


@pytest.mark.parametrize("ajudando", ["false", "true"])
def test_texto_saude_cita_a_lei_e_e_condicional(js, ajudando):
    texto = js.eval(f"Rede.textoSaude({ajudando})")
    assert "Lei 12.845/2013, arts. 1º e 3º" in texto
    assert "art. 3º, IV e V" in texto
    assert "Se foi nas últimas 72 horas" in texto
    assert "pronto-socorro de um hospital público" in texto
    # A Lei 12.845/2013 não fala em boletim de ocorrência: o texto não promete isso.
    assert "boletim" not in texto.lower()
