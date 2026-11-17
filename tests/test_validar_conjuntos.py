"""Fixtures fictícias para o contrato dos conjuntos da S3."""

from copy import deepcopy
from pathlib import Path

import yaml

from conjuntos_ficticios import dados_ficticios as _dados
from scripts.validar_conjuntos import (
    validar_conjunto,
    validar_elegibilidade_s4,
    validar_roteamento_s4,
    validar_triagem_s4,
)


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


def _s4(tmp_path: Path, nome: str, dados: dict) -> Path:
    arquivo = tmp_path / f"{nome}.yaml"
    arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    return arquivo


def _carregar_s4(nome: str) -> dict:
    raiz = Path(__file__).resolve().parents[1] / "avaliacao" / "conjuntos" / "s4"
    return yaml.safe_load((raiz / f"{nome}.yaml").read_text(encoding="utf-8"))


def test_conjuntos_s4_existentes_validos():
    assert validar_elegibilidade_s4() == []
    assert validar_triagem_s4() == []
    assert validar_roteamento_s4() == []


def test_fonte_e_revisor_s4_obrigatorios(tmp_path: Path):
    triagem = _carregar_s4("triagem")
    triagem["casos"][0]["fonte"] = ""
    erros = validar_triagem_s4(_s4(tmp_path, "triagem", triagem))
    assert any("t-001" in erro and "fonte" in erro for erro in erros)

    elegibilidade = _carregar_s4("elegibilidade")
    elegibilidade["casos"][0]["conferencia"]["revisor"] = elegibilidade["casos"][0]["autor"]
    erros = validar_elegibilidade_s4(_s4(tmp_path, "elegibilidade", elegibilidade))
    assert any("e-001" in erro and "revisor deve ser diferente" in erro for erro in erros)


def test_elegibilidade_detecta_cada_limite_ausente(tmp_path: Path):
    dados = _carregar_s4("elegibilidade")
    # Deixa perfis e demais campos intactos, mas retira os valores que cobrem os cortes.
    for caso in dados["casos"]:
        perfil = caso["perfil"]
        if isinstance(perfil.get("renda_total"), (int, float)):
            perfil["renda_total"] += 0.37
        perfil["numero_pessoas"] = 1
    erros = validar_elegibilidade_s4(_s4(tmp_path, "sem-cortes", dados))
    assert any("exatamente no limite" in erro for erro in erros)
    assert any("um real acima" in erro for erro in erros)

    dados = _carregar_s4("elegibilidade")
    for caso in dados["casos"]:
        perfil = caso["perfil"]
        if isinstance(perfil.get("renda_total"), str) and "prefiro" in perfil["renda_total"].casefold():
            perfil["renda_total"] = 500
        for campo in ("renda_total", "numero_pessoas"):
            if perfil.get(campo) is None:
                perfil[campo] = 1
    erros = validar_elegibilidade_s4(_s4(tmp_path, "sem-incompletos", dados))
    assert any("prefiro não informar" in erro for erro in erros)
    assert any("perfil incompleto" in erro for erro in erros)
