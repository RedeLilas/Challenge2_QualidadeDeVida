#!/usr/bin/env python3
"""Valida os conjuntos de avaliação da S3 sem depender de perguntas reais."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

from app.risco import avaliar


RAIZ = Path(__file__).resolve().parent.parent
PASTA_CONJUNTOS = RAIZ / "avaliacao" / "conjuntos"

# Chaves estáveis definidas para os conjuntos da S3.
DISTRIBUICAO_OFICIAL = {
    "violencia_e_protecao": 5,
    "medidas_protetivas": 7,
    "policia_processo_defensoria": 4,
    "crime": 9,
    "guarda": 2,
    "auxilio_fonar_trabalho": 3,
}
CATEGORIAS = set(DISTRIBUICAO_OFICIAL)


def _texto(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _lista_textos(valor: object) -> bool:
    return isinstance(valor, list) and bool(valor) and all(_texto(item) for item in valor)


def _validar_pergunta(
    item: object,
    referencia: str,
    *,
    extra: bool,
    exigir_conferencia: bool,
    ids: set[str],
) -> list[str]:
    erros: list[str] = []
    if not isinstance(item, dict):
        return [f"{referencia}: registro deve ser um objeto"]

    for campo in ("id", "pergunta", "autor"):
        if not _texto(item.get(campo)):
            erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")

    identificador = item.get("id")
    if _texto(identificador):
        if identificador in ids:
            erros.append(f"{referencia}: id duplicado '{identificador}'")
        ids.add(identificador)

    if extra:
        if item.get("categoria") != "fora_do_tema":
            erros.append(f"{referencia}: categoria de extra deve ser 'fora_do_tema'")
    elif not isinstance(item.get("categoria"), str) or item["categoria"] not in CATEGORIAS:
        erros.append(f"{referencia}: categoria inválida '{item.get('categoria')}'")

    pergunta = item.get("pergunta")
    if _texto(pergunta):
        regra = avaliar(pergunta)
        if regra is not None:
            erros.append(f"{referencia}: pergunta dispara alerta de risco ({regra['id']})")

    if not extra:
        for campo in ("resposta_esperada", "fonte"):
            if not _texto(item.get(campo)):
                erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
        for campo in ("pontos_obrigatorios", "normas_aceitas"):
            if not _lista_textos(item.get(campo)):
                erros.append(f"{referencia}: campo '{campo}' deve ser lista não vazia de textos")

        if exigir_conferencia:
            conferencia = item.get("conferencia")
            if not isinstance(conferencia, dict):
                erros.append(f"{referencia}: campo 'conferencia' obrigatório")
            else:
                for campo in ("revisor", "fonte_conferida"):
                    if not _texto(conferencia.get(campo)):
                        erros.append(f"{referencia}: conferencia.{campo} obrigatório e não vazio")
                if _texto(conferencia.get("revisor")) and _texto(item.get("autor")):
                    if conferencia["revisor"].strip().casefold() == item["autor"].strip().casefold():
                        erros.append(f"{referencia}: revisor deve ser diferente do autor")

    return erros


def validar_conjunto(caminho: Path, tipo: str) -> list[str]:
    """Retorna erros do arquivo; lista vazia indica conjunto válido."""
    if tipo not in {"desenvolvimento", "oficial"}:
        raise ValueError(f"Tipo de conjunto desconhecido: {tipo}")
    if not caminho.is_file():
        return [f"Arquivo não encontrado: {caminho}"]

    try:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{caminho}: não foi possível ler YAML: {exc}"]

    if not isinstance(dados, dict):
        return [f"{caminho}: raiz deve ser um objeto com versao, perguntas e extras"]

    erros: list[str] = []
    if type(dados.get("versao")) is not int or dados["versao"] != 1:
        erros.append(f"{caminho}: 'versao' deve ser 1")

    perguntas = dados.get("perguntas")
    extras = dados.get("extras")
    if not isinstance(perguntas, list):
        erros.append(f"{caminho}: 'perguntas' deve ser uma lista")
        perguntas = []
    if not isinstance(extras, list):
        erros.append(f"{caminho}: 'extras' deve ser uma lista")
        extras = []

    esperado_perguntas = 15 if tipo == "desenvolvimento" else 30
    if len(perguntas) != esperado_perguntas:
        erros.append(f"{caminho}: esperadas {esperado_perguntas} perguntas do tema; encontradas {len(perguntas)}")
    if len(extras) != 10:
        erros.append(f"{caminho}: esperadas 10 perguntas fora do tema; encontradas {len(extras)}")

    ids: set[str] = set()
    for indice, item in enumerate(perguntas, start=1):
        erros.extend(
            _validar_pergunta(
                item,
                f"{caminho}:perguntas[{indice}]",
                extra=False,
                exigir_conferencia=tipo == "oficial",
                ids=ids,
            )
        )
    for indice, item in enumerate(extras, start=1):
        erros.extend(
            _validar_pergunta(
                item,
                f"{caminho}:extras[{indice}]",
                extra=True,
                exigir_conferencia=False,
                ids=ids,
            )
        )

    if tipo == "oficial":
        contagem = Counter(
            item.get("categoria")
            for item in perguntas
            if isinstance(item, dict)
            and isinstance(item.get("categoria"), str)
            and item["categoria"] in CATEGORIAS
        )
        for categoria, esperado in DISTRIBUICAO_OFICIAL.items():
            if contagem[categoria] != esperado:
                erros.append(
                    f"{caminho}: categoria '{categoria}' exige {esperado} perguntas; encontradas {contagem[categoria]}"
                )

    return erros


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tipo", choices=("desenvolvimento", "oficial", "todos"),
        help="Conjunto a validar",
    )
    parser.add_argument(
        "--diretorio", type=Path, default=PASTA_CONJUNTOS,
        help="Pasta dos conjuntos (padrão: avaliacao/conjuntos/)",
    )
    args = parser.parse_args()
    tipos = ("desenvolvimento", "oficial") if args.tipo == "todos" else (args.tipo,)
    erros = [
        erro
        for tipo in tipos
        for erro in validar_conjunto(args.diretorio / f"{tipo}.yaml", tipo)
    ]
    for erro in erros:
        print(erro)
    if erros:
        return 1
    print(f"Conjunto(s) válido(s): {', '.join(tipos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
