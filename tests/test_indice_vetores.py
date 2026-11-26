"""Vetores do índice gerados no build e carregados ao subir (s5-deploy, tarefa 2.3, #134).

Os vetores prontos só valem se os trechos e o modelo forem os mesmos de quando foram gerados.
Se não baterem, o índice recalcula na hora, como antes, e nunca usa vetores desatualizados.
"""
import re
from pathlib import Path

import numpy as np
import pytest
import yaml

from app.rag import indice as modulo_indice
from app.rag.indice import Indice, carregar_trechos, salvar_vetores

PERGUNTAS = Path(__file__).parent / "perguntas_juridicas.yaml"


@pytest.fixture(scope="module")
def indice_montado(indice_real):
    return indice_real


@pytest.fixture(scope="module")
def poucos_trechos():
    # Um recorte pequeno deixa rápidos os testes que precisam recalcular os vetores.
    return carregar_trechos()[:12]


def test_vetores_prontos_devolvem_os_mesmos_trechos_que_o_indice_montado(indice_montado, tmp_path):
    arquivo = tmp_path / "vetores.npz"
    salvar_vetores(indice_montado, arquivo)

    carregado = Indice(carregar_trechos(), vetores=arquivo)

    assert carregado.origem == "arquivo"
    perguntas = yaml.safe_load(PERGUNTAS.read_text(encoding="utf-8"))["perguntas"]
    assert len(perguntas) == 10
    for p in perguntas:
        montado = [t["id"] for t, _ in indice_montado.buscar(p["pergunta"], eixos={"juridico"})]
        pronto = [t["id"] for t, _ in carregado.buscar(p["pergunta"], eixos={"juridico"})]
        assert pronto == montado, p["pergunta"]


def test_sem_arquivo_de_vetores_o_indice_e_montado_na_hora(poucos_trechos, tmp_path):
    indice = Indice(poucos_trechos, vetores=tmp_path / "nao_existe.npz")
    assert indice.origem == "calculado"


def test_trechos_diferentes_dos_do_arquivo_recalculam(poucos_trechos, tmp_path):
    arquivo = tmp_path / "vetores.npz"
    salvar_vetores(Indice(poucos_trechos), arquivo)
    alterados = [dict(t) for t in poucos_trechos]
    alterados[0]["texto"] += " (texto alterado numa nova coleta)"

    indice = Indice(alterados, vetores=arquivo)

    assert indice.origem == "calculado"
    assert np.allclose(indice.matriz, Indice(alterados).matriz, atol=1e-5)


def test_modelo_diferente_do_que_gerou_o_arquivo_recalcula(poucos_trechos, tmp_path):
    arquivo = tmp_path / "vetores.npz"
    salvar_vetores(Indice(poucos_trechos), arquivo)
    # Simula vetores gerados por outro modelo: a sentinela gravada não bate com a do modelo atual.
    dados = dict(np.load(arquivo))
    dados["sentinela"] = -dados["sentinela"]
    np.savez(arquivo, **dados)

    assert Indice(poucos_trechos, vetores=arquivo).origem == "calculado"


def test_indice_padrao_usa_o_arquivo_de_vetores_do_build(monkeypatch, poucos_trechos, tmp_path):
    arquivo = tmp_path / "vetores.npz"
    salvar_vetores(Indice(poucos_trechos), arquivo)
    monkeypatch.setattr(modulo_indice, "ARQUIVO_VETORES", arquivo)
    monkeypatch.setattr(modulo_indice, "carregar_trechos", lambda: poucos_trechos)
    monkeypatch.setattr(modulo_indice, "_indice", None)

    assert modulo_indice.indice_padrao().origem == "arquivo"


def test_indice_padrao_registra_a_origem_e_o_tempo_ao_montar(monkeypatch, poucos_trechos, tmp_path, caplog):
    # Para medir a partida a frio na plataforma (tarefa 3.2): só a origem e o tempo, nenhum dado da usuária.
    arquivo = tmp_path / "vetores.npz"
    salvar_vetores(Indice(poucos_trechos), arquivo)
    monkeypatch.setattr(modulo_indice, "ARQUIVO_VETORES", arquivo)
    monkeypatch.setattr(modulo_indice, "carregar_trechos", lambda: poucos_trechos)
    monkeypatch.setattr(modulo_indice, "_indice", None)

    with caplog.at_level("INFO", logger="rede_lilas.indice"):
        modulo_indice.indice_padrao()
        modulo_indice.indice_padrao()

    linhas = [r.getMessage() for r in caplog.records if r.name == "rede_lilas.indice"]
    assert len(linhas) == 1
    assert re.fullmatch(r"índice pronto: origem=arquivo em \d+\.\d s", linhas[0])
