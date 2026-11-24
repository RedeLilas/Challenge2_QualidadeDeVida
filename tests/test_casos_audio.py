"""Estrutura dos casos fictícios de áudio (s5-entrada-audio, tarefa 1.2).

Não usa o Whisper: confere os arquivos, os textos e a regra de risco sobre os textos lidos.
"""
from pathlib import Path

import pytest
import yaml

from app import risco

PASTA = Path(__file__).parent / "audios"
DADOS = yaml.safe_load((PASTA / "casos_audio.yaml").read_text(encoding="utf-8"))
CASOS = DADOS["casos"]
POR_ID = {c["id"]: c for c in CASOS}
LIMITE_BYTES = 1024 * 1024  # limite da rota /transcrever (design)
ASSINATURA = {"webm": lambda b: b[:4] == b"\x1a\x45\xdf\xa3", "mp4": lambda b: b[4:8] == b"ftyp"}


def test_casos_a1_a_a7_com_ids_unicos():
    assert DADOS["versao"] == 1
    assert [c["id"] for c in CASOS] == [f"A{i}" for i in range(1, 8)]
    assert len({c["arquivo"] for c in CASOS}) == len(CASOS)


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_arquivo_existe_no_formato_e_no_limite(caso):
    arquivo = PASTA / caso["arquivo"]
    conteudo = arquivo.read_bytes()
    assert caso["formato"] in ASSINATURA and arquivo.suffix == f".{caso['formato']}"
    assert ASSINATURA[caso["formato"]](conteudo), "o arquivo não é do formato declarado"
    assert 0 < len(conteudo) < LIMITE_BYTES


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_texto_e_palavras_chave(caso):
    for campo in ("texto", "palavras_chave", "risco_esperado", "agente_esperado"):
        assert campo in caso
    if caso["id"] == "A7":
        assert caso["texto"] == "" and caso["palavras_chave"] == [] and caso["duracao_silencio_s"] == 5
        return
    assert caso["texto"].strip() and caso["palavras_chave"]
    normalizado = risco.normalizar(caso["texto"])
    for palavra in caso["palavras_chave"]:
        assert palavra == risco.normalizar(palavra), "palavra-chave deve estar normalizada"
        assert palavra in normalizado


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_regra_de_risco_sobre_o_texto_lido(caso):
    assert bool(risco.avaliar(caso["texto"])) is caso["risco_esperado"]


def test_a5_e_a6_disparam_o_190():
    assert risco.avaliar(POR_ID["A5"]["texto"])["categoria"] in {"arma", "ameaca_morte"}
    assert risco.avaliar(POR_ID["A6"]["texto"]) is not None


def test_ha_casos_nos_dois_formatos_dos_navegadores():
    assert {c["formato"] for c in CASOS} == {"webm", "mp4"}


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_duracao_ate_30_segundos(caso):
    av = pytest.importorskip("av")
    with av.open(str(PASTA / caso["arquivo"])) as container:
        segundos = sum(q.samples / q.sample_rate for q in container.decode(audio=0))
    assert 0 < segundos <= 30
    if caso["id"] == "A7":
        assert 4.5 <= segundos <= 5.5
