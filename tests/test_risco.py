"""Suíte de risco imediato / 190 (s2-alerta-risco-190, tarefas 1.2 a 1.4).

Rodar antes de concluir qualquer mudança. Um falso negativo reprova a suíte.
"""
import json
import re
import warnings
from pathlib import Path

import pytest
import yaml

from app import risco

RAIZ = Path(__file__).resolve().parents[1]
CASOS = yaml.safe_load((Path(__file__).parent / "casos_risco.yaml").read_text(encoding="utf-8"))
ARQUIVO = json.loads((RAIZ / "regras" / "risco_imediato.json").read_text(encoding="utf-8"))
CAMPOS = ("id", "categoria", "padrao", "exemplo", "justificativa")


# --- 1.2: estrutura do arquivo de regras --------------------------------------------------


def test_arquivo_tem_versao_e_categorias():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", ARQUIVO["versao"])
    assert set(ARQUIVO["categorias"]) == {
        "arma", "ameaca_morte", "agressao_em_andamento", "carcere", "ferimento_grave", "crianca_em_perigo",
    }  # fmt: skip


@pytest.mark.parametrize("regra", ARQUIVO["regras"], ids=lambda r: r.get("id", "?"))
def test_regra_tem_campos_obrigatorios(regra):
    for campo in CAMPOS:
        assert isinstance(regra.get(campo), str) and regra[campo].strip(), f"campo vazio: {campo}"
    assert regra["categoria"] in ARQUIVO["categorias"]
    re.compile(regra["padrao"])


def test_ids_unicos_e_toda_categoria_tem_regra():
    ids = [r["id"] for r in ARQUIVO["regras"]]
    assert len(ids) == len(set(ids))
    assert {r["categoria"] for r in ARQUIVO["regras"]} == set(ARQUIVO["categorias"])


@pytest.mark.parametrize("regra", ARQUIVO["regras"], ids=lambda r: r["id"])
def test_exemplo_de_cada_regra_dispara_a_propria_regra(regra):
    assert re.search(regra["padrao"], risco.normalizar(regra["exemplo"]))


# --- 1.3: normalização e avaliação --------------------------------------------------------


def test_normalizacao():
    assert risco.normalizar("  ELE ESTÁ\n aqui   com uma FACA!  ") == "ele esta aqui com uma faca!"
    assert risco.normalizar("ameaçou, pescoço, bebê") == "ameacou, pescoco, bebe"


@pytest.mark.parametrize("caso", CASOS["risco"], ids=lambda c: c["frase"][:40])
def test_frase_de_risco_dispara_o_alerta(caso):
    # Zero falso negativo: se falhar, amplie as regras; nunca tire a frase da suíte.
    assert risco.avaliar(caso["frase"]) is not None, f"FALSO NEGATIVO: {caso['frase']!r}"


@pytest.mark.parametrize(
    "variacao",
    ["ele vai me matar", "ELE VAI ME MATAR", "ele vai me matah", "Ele vai me MATÁ", "ele   vai\nme matar!!"],
)
def test_variacoes_de_escrita_disparam(variacao):
    assert risco.avaliar(variacao) is not None


def test_toda_categoria_tem_frase_na_suite():
    assert {c["categoria"] for c in CASOS["risco"]} == set(ARQUIVO["categorias"])
    assert len(CASOS["risco"]) >= 30 and len(CASOS["nao_risco"]) >= 30


def test_falsos_positivos_sao_contados_sem_reprovar():
    falsos = [f for f in CASOS["nao_risco"] if risco.avaliar(f)]
    if falsos:
        warnings.warn(f"{len(falsos)} falso(s) positivo(s) de {len(CASOS['nao_risco'])}: {falsos}")


def test_resultado_traz_regra_e_categoria():
    resultado = risco.avaliar("ele esta aqui em casa com uma faca")
    assert resultado == {"id": "presenca-com-arma", "categoria": "arma"}
    assert risco.avaliar("o que é medida protetiva?") is None


# --- 1.4: só sintaxe de regex que o JavaScript dos celulares aceita -----------------------

# Lookbehind só existe no Safari a partir do iOS 16.4; grupos nomeados e flags no meio do
# padrão têm sintaxe diferente (ou não existem) no JavaScript.
SINTAXE_PROIBIDA = {
    "lookbehind": r"\(\?<[=!]",
    "grupo nomeado": r"\(\?P?<\w",
    "referência a grupo nomeado": r"\(\?P=|\\k<",
    "flag no padrão": r"\(\?[aiLmsux]+[):]",
    "grupo atômico ou comentário": r"\(\?[>#]",
    "âncora só do Python": r"\\[AZz]",
    "quantificador possessivo": r"[*+?}]\+",
}


@pytest.mark.parametrize("regra", ARQUIVO["regras"], ids=lambda r: r["id"])
def test_padrao_usa_so_sintaxe_compativel_com_javascript(regra):
    for nome, proibido in SINTAXE_PROIBIDA.items():
        assert not re.search(proibido, regra["padrao"]), f"{regra['id']}: {nome}"


@pytest.mark.parametrize(
    "padrao, nome",
    [
        (r"(?<=ele )faca", "lookbehind"),
        (r"(?<!nao )matar", "lookbehind"),
        (r"(?P<arma>faca)", "grupo nomeado"),
        (r"(?i)faca", "flag no padrão"),
        (r"faca\Z", "âncora só do Python"),
    ],
)
def test_checagem_pega_sintaxe_proibida(padrao, nome):
    assert re.search(SINTAXE_PROIBIDA[nome], padrao)
