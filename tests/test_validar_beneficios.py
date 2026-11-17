"""Perguntas de desenvolvimento de benefícios e sua validação (s4-rag-beneficios, tarefas 1.1 e 1.2)."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.validar_conjuntos import (
    ARQUIVO_DESENVOLVIMENTO_BENEFICIOS,
    PROGRAMAS_BENEFICIOS,
    validar_desenvolvimento_beneficios,
    validar_medicao_beneficios,
)

REAL = yaml.safe_load(ARQUIVO_DESENVOLVIMENTO_BENEFICIOS.read_text(encoding="utf-8"))


def conferido() -> dict:
    """O conjunto real com a conferência preenchida por outra pessoa: deve ser válido."""
    dados = deepcopy(REAL)
    for item in dados["perguntas"] + dados["juridico"]:
        item["conferencia"] = {"revisor": "Pessoa Revisora", "fonte_conferida": "texto conferido", "status": "ok"}
    return dados


def validar(tmp_path: Path, dados: dict) -> list[str]:
    arquivo = tmp_path / "desenvolvimento_beneficios.yaml"
    arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    return validar_desenvolvimento_beneficios(arquivo)


# --- 1.1: o conjunto real -----------------------------------------------------------------------


def test_conjunto_real_e_valido_e_conferido():
    assert validar_desenvolvimento_beneficios() == []
    itens = REAL["perguntas"] + REAL["juridico"]
    assert all(i["conferencia"]["status"] == "conferida" for i in itens)


def test_conjunto_real_cobre_o_que_a_tarefa_pede():
    perguntas = REAL["perguntas"]
    assert 18 <= len(perguntas) <= 25
    assert {p["programa"] for p in perguntas} == PROGRAMAS_BENEFICIOS
    assert sum(p["sem_nome_oficial"] for p in perguntas) >= len(perguntas) // 3
    assert len(REAL["extras"]) >= 8
    textos = " ".join(e["pergunta"].lower() for e in REAL["extras"])
    for assunto in ("imposto de renda", "fgts", "seguro", "aposentadoria"):
        assert assunto in textos
    assert REAL["juridico"][0]["pergunta"] == "como funciona o aluguel da maria da penha?"


def test_conjunto_conferido_e_valido(tmp_path):
    assert validar(tmp_path, conferido()) == []


# --- 1.2: o validador ---------------------------------------------------------------------------


def test_pergunta_sem_norma_falha(tmp_path):
    dados = conferido()
    del dados["perguntas"][0]["normas_aceitas"]
    assert any("perguntas[1]" in e and "normas_aceitas" in e for e in validar(tmp_path, dados))


@pytest.mark.parametrize(
    "norma, trecho_do_erro",
    [
        ("Lei 14.601/2023", "sem a forma"),
        ("Lei 14.601/2023, art. 99", "não existe"),
        ("Lei 11.340/2006, art. 23", "fora da base"),  # eixo jurídico numa pergunta de benefício
    ],
)
def test_norma_fora_da_base_falha(tmp_path, norma, trecho_do_erro):
    dados = conferido()
    dados["perguntas"][0]["normas_aceitas"] = [norma]
    assert any("perguntas[1]" in e and trecho_do_erro in e for e in validar(tmp_path, dados))


def test_revisor_igual_ao_autor_falha(tmp_path):
    dados = conferido()
    dados["perguntas"][0]["conferencia"]["revisor"] = "Túlio Celeri"  # o autor é "Túlio Celeri (com o Claude)"
    assert any("revisor deve ser diferente do autor" in e for e in validar(tmp_path, dados))


def test_conferencia_pendente_falha(tmp_path):
    dados = conferido()
    dados["perguntas"][0]["conferencia"]["revisor"] = ""
    assert any("perguntas[1]" in e and "conferência pendente" in e for e in validar(tmp_path, dados))


def test_programa_sem_pergunta_falha(tmp_path):
    dados = conferido()
    dados["perguntas"] = [p for p in dados["perguntas"] if p["programa"] != "cartao_gas"]
    assert any("cartao_gas" in e for e in validar(tmp_path, dados))


def test_sem_pergunta_leiga_falha(tmp_path):
    dados = conferido()
    for p in dados["perguntas"]:
        p["sem_nome_oficial"] = False
    assert any("sem o nome oficial" in e for e in validar(tmp_path, dados))


def test_extra_fora_da_categoria_falha(tmp_path):
    dados = conferido()
    dados["extras"][0]["categoria"] = "fora_do_tema"
    assert any("extras[1]" in e and "quase_do_tema" in e for e in validar(tmp_path, dados))


def test_falta_a_pergunta_do_aluguel_da_maria_da_penha(tmp_path):
    dados = conferido()
    dados["juridico"][0]["pergunta"] = "o que é medida protetiva?"
    assert any("aluguel da Maria da Penha" in e for e in validar(tmp_path, dados))


def test_pergunta_que_dispara_alerta_falha(tmp_path):
    dados = conferido()
    dados["perguntas"][0]["pergunta"] = "ele está aqui em casa com uma faca, posso pedir o bolsa família?"
    assert any("perguntas[1]" in e and "dispara alerta de risco" in e for e in validar(tmp_path, dados))


def test_medicao_nao_pode_repetir_pergunta_da_calibracao(tmp_path):
    medicao = tmp_path / "medicao_beneficios.yaml"
    repetida = {"id": "m-001", "pergunta": "O que é o BPC?"}  # mesma de bd-005, com maiúscula e acento
    nova = {"id": "m-002", "pergunta": "o cartão gás vale para quem mora em goiânia?"}
    medicao.write_text(yaml.safe_dump({"versao": 1, "perguntas": [repetida, nova]}, allow_unicode=True), encoding="utf-8")
    erros = validar_medicao_beneficios(medicao)
    assert len(erros) == 1 and "m-001" in erros[0]


def test_medicao_sem_repeticao_e_valida(tmp_path):
    medicao = tmp_path / "medicao_beneficios.yaml"
    medicao.write_text(yaml.safe_dump({"versao": 1, "perguntas": [{"id": "m-001", "pergunta": "pergunta nova?"}]}), encoding="utf-8")
    assert validar_medicao_beneficios(medicao) == []
