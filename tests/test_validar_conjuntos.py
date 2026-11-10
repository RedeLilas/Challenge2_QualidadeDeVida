"""Fixtures fictícias para o contrato dos conjuntos da S3."""

from copy import deepcopy
from pathlib import Path

import yaml

from scripts.validar_conjuntos import DISTRIBUICAO_OFICIAL, validar_conjunto


def _pergunta(numero: int, categoria: str, *, conferir: bool) -> dict:
    item = {
        "id": f"q-{numero:03d}",
        "categoria": categoria,
        "pergunta": f"Pergunta fictícia {numero} sobre uma situação passada e hipotética?",
        "autor": "Pessoa A",
        "resposta_esperada": "Resposta fictícia para testar a estrutura.",
        "pontos_obrigatorios": ["Ponto fictício"],
        "normas_aceitas": ["Norma fictícia"],
        "fonte": "Referência fictícia ao texto legal",
    }
    if conferir:
        item["conferencia"] = {
            "revisor": "Pessoa B",
            "fonte_conferida": "Referência fictícia conferida",
        }
    return item


def _dados(tipo: str) -> dict:
    categorias = (
        [categoria for categoria, total in DISTRIBUICAO_OFICIAL.items() for _ in range(total)]
        if tipo == "oficial"
        else list(DISTRIBUICAO_OFICIAL) * 2 + list(DISTRIBUICAO_OFICIAL)[:3]
    )
    return {
        "versao": 1,
        "perguntas": [
            _pergunta(i, categoria, conferir=tipo == "oficial")
            for i, categoria in enumerate(categorias, start=1)
        ],
        "extras": [
            {
                "id": f"extra-{i:03d}",
                "categoria": "fora_do_tema",
                "pergunta": f"Pergunta extra fictícia {i}?",
                "autor": "Pessoa A",
            }
            for i in range(1, 11)
        ],
    }


def _validar(tmp_path: Path, dados: dict, tipo: str) -> list[str]:
    arquivo = tmp_path / f"{tipo}.yaml"
    arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    return validar_conjunto(arquivo, tipo)


def test_conjuntos_ficticios_validos(tmp_path: Path):
    assert _validar(tmp_path, _dados("desenvolvimento"), "desenvolvimento") == []
    assert _validar(tmp_path, _dados("oficial"), "oficial") == []


def test_campo_obrigatorio_ausente_falha(tmp_path: Path):
    dados = _dados("oficial")
    del dados["perguntas"][0]["pontos_obrigatorios"]
    erros = _validar(tmp_path, dados, "oficial")
    assert any("perguntas[1]" in erro and "pontos_obrigatorios" in erro for erro in erros)


def test_distribuicao_oficial_errada_falha(tmp_path: Path):
    dados = _dados("oficial")
    dados["perguntas"][0]["categoria"] = "crime"
    erros = _validar(tmp_path, dados, "oficial")
    assert any("violencia_e_protecao" in erro and "exige 5" in erro for erro in erros)
    assert any("crime" in erro and "exige 9" in erro for erro in erros)


def test_falta_de_segunda_pessoa_falha(tmp_path: Path):
    dados = _dados("oficial")
    del dados["perguntas"][0]["conferencia"]
    erros = _validar(tmp_path, dados, "oficial")
    assert any("perguntas[1]" in erro and "conferencia" in erro for erro in erros)

    outro = deepcopy(_dados("oficial"))
    outro["perguntas"][0]["conferencia"]["revisor"] = "pessoa a"
    erros = _validar(tmp_path, outro, "oficial")
    assert any("revisor deve ser diferente do autor" in erro for erro in erros)


def test_pergunta_que_dispara_alerta_falha(tmp_path: Path):
    dados = _dados("oficial")
    dados["perguntas"][0]["pergunta"] = "Ele está aqui em casa com uma faca"
    erros = _validar(tmp_path, dados, "oficial")
    assert any("perguntas[1]" in erro and "dispara alerta de risco" in erro for erro in erros)


def test_desenvolvimento_exige_totais_mas_nao_distribuicao(tmp_path: Path):
    dados = _dados("desenvolvimento")
    for item in dados["perguntas"]:
        item["categoria"] = "crime"
    assert _validar(tmp_path, dados, "desenvolvimento") == []
    dados["extras"].pop()
    assert any("esperadas 10 perguntas fora do tema" in erro for erro in _validar(tmp_path, dados, "desenvolvimento"))
