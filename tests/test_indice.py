from pathlib import Path

import pytest
import yaml

from app.rag.indice import Indice, carregar_trechos

PERGUNTAS = Path(__file__).parent / "perguntas_juridicas.yaml"


@pytest.fixture(scope="module")
def indice():
    return Indice(carregar_trechos())


def test_violencia_patrimonial_recupera_art_7(indice):
    artigos = [t["artigo"] for t, _ in indice.buscar("violência patrimonial")]
    assert "7" in artigos


def test_perguntas_das_personas_top5(indice):
    perguntas = yaml.safe_load(PERGUNTAS.read_text(encoding="utf-8"))["perguntas"]
    erros = []
    for p in perguntas:
        recuperados = [t["artigo"] for t, _ in indice.buscar(p["pergunta"])]
        if not set(p["artigos"]) & set(recuperados):
            erros.append(f"{p['pergunta']!r}: esperado {p['artigos']}, recuperado {recuperados}")
    acertos = len(perguntas) - len(erros)
    assert acertos >= 9, f"{acertos}/{len(perguntas)} no top 5:\n" + "\n".join(erros)
