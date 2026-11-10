"""Testes das regras versionadas de benefícios (s3-beneficios, tarefas 1.1 e 1.2)."""

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO = json.loads((RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8"))
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CAMPOS_REGRA = ("id", "nome", "norma", "artigo", "inicio_vigencia", "data_verificacao", "onde_pedir")
IDS_ESPERADOS = ("bolsa_familia", "bpc", "auxilio_aluguel", "aluguel_social_df")


def _coletar_textos(valor):
    """Percorre recursivamente dicionários e listas extraindo todas as strings."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _coletar_textos(v)
    elif isinstance(valor, list):
        for item in valor:
            yield from _coletar_textos(item)


def test_arquivo_tem_versao_e_salario_minimo_verificado():
    assert DATA_ISO.fullmatch(ARQUIVO["versao"])

    sm = ARQUIVO["salario_minimo"]
    assert isinstance(sm["valor"], (int, float)) and sm["valor"] > 0
    assert isinstance(sm["norma"], str) and sm["norma"].strip()
    assert isinstance(sm["fonte"], str) and sm["fonte"].strip()
    assert isinstance(sm["fonte_url"], str) and sm["fonte_url"].startswith("https://")
    assert DATA_ISO.fullmatch(sm["inicio_vigencia"])
    assert DATA_ISO.fullmatch(sm["data_verificacao"])

    verificacao = ARQUIVO["verificacao_valores"]
    assert verificacao["salario_minimo"]["valor_vigente"] == sm["valor"]
    assert DATA_ISO.fullmatch(verificacao["salario_minimo"]["data_verificacao"])
    assert verificacao["bolsa_familia_limite_per_capita"]["valor_vigente"] == 218.0
    assert isinstance(verificacao["bolsa_familia_limite_per_capita"]["reajustado"], bool)
    assert DATA_ISO.fullmatch(verificacao["bolsa_familia_limite_per_capita"]["data_verificacao"])


def test_quatro_regras_na_ordem_esperada():
    ids = tuple(r["id"] for r in ARQUIVO["regras"])
    assert ids == IDS_ESPERADOS


@pytest.mark.parametrize("regra", ARQUIVO["regras"], ids=lambda r: r.get("id", "?"))
def test_toda_regra_tem_norma_artigo_vigencia_verificacao_requisitos_e_textos(regra):
    for campo in CAMPOS_REGRA:
        assert isinstance(regra.get(campo), str) and regra[campo].strip(), f"campo vazio ou ausente: {campo}"
    assert DATA_ISO.fullmatch(regra["inicio_vigencia"]), f"inicio_vigencia inválido em {regra['id']}"
    assert DATA_ISO.fullmatch(regra["data_verificacao"]), f"data_verificacao inválida em {regra['id']}"
    assert isinstance(regra.get("requisitos"), dict) and regra["requisitos"]
    assert isinstance(regra.get("textos"), dict) and regra["textos"]
    for chave, texto in regra["textos"].items():
        assert isinstance(texto, str) and texto.strip(), f"texto vazio: {regra['id']}.{chave}"


def test_nenhum_texto_usa_direito_garantido():
    for texto in _coletar_textos(ARQUIVO):
        assert "direito garantido" not in texto.lower(), f"Expressão proibida encontrada em: {texto!r}"

