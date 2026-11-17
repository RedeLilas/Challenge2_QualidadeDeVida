#!/usr/bin/env python3
"""Valida os conjuntos de avaliação (S3 e perguntas de desenvolvimento de benefícios da S4) sem depender de perguntas reais."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from functools import cache
from pathlib import Path

import yaml

from app.risco import avaliar, normalizar


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


# --- s4-rag-beneficios, tarefa 1.2: perguntas de desenvolvimento de benefícios -------------------

PASTA_LEIS = RAIZ / "dados" / "leis"
ARQUIVO_DESENVOLVIMENTO_BENEFICIOS = PASTA_CONJUNTOS / "s4" / "desenvolvimento_beneficios.yaml"
# Se o RAG de benefícios for medido depois da S4, a medição usa este arquivo, separado e congelado antes.
ARQUIVO_MEDICAO_BENEFICIOS = PASTA_CONJUNTOS / "s4" / "medicao_beneficios.yaml"
PROGRAMAS_BENEFICIOS = {
    "bolsa_familia", "bpc", "prato_cheio", "cartao_gas", "aluguel_social_df", "beneficios_eventuais",
}  # fmt: skip
EIXOS_BENEFICIOS = {"beneficios", "df"}
# "Lei 14.601/2023, art. 5º", "Lei 8.742/1993 (LOAS), art. 20", "Lei Distrital 5.165/2013, art. 10"
RE_NORMA_ACEITA = re.compile(r"^(?P<lei>.+), art\. (?P<artigo>\d+(?:\.\d{3})?(?:-[A-Z])?)[º°]?$")


@cache
def _artigos_por_norma(eixos: frozenset[str]) -> dict[str, set[str]]:
    """Rótulo de cada norma dos eixos dados -> artigos que existem na base (dados/leis/)."""
    artigos: dict[str, set[str]] = {}
    for arquivo in sorted(PASTA_LEIS.glob("*.jsonl")):
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            trecho = json.loads(linha)
            if trecho["eixo"] in eixos:
                artigos.setdefault(trecho["lei"], set()).add(trecho["artigo"])
    return artigos


def _sem_pontuacao(texto: str) -> str:
    return re.sub(r"[^\w ]", "", normalizar(texto)).strip()


def _validar_normas(normas: object, eixos: set[str], referencia: str) -> list[str]:
    if not _lista_textos(normas):
        return [f"{referencia}: campo 'normas_aceitas' deve ser lista não vazia de textos"]
    base = _artigos_por_norma(frozenset(eixos))
    erros = []
    for norma in normas:
        lida = RE_NORMA_ACEITA.match(norma.strip())
        if lida is None:
            erros.append(f"{referencia}: norma '{norma}' sem a forma 'Norma, art. N'")
        elif lida["lei"] not in base:
            erros.append(f"{referencia}: norma '{lida['lei']}' fora da base dos eixos {sorted(eixos)}")
        elif lida["artigo"] not in base[lida["lei"]]:
            erros.append(f"{referencia}: art. {lida['artigo']} não existe em '{lida['lei']}' na base")
    return erros


def _validar_item_beneficios(item: object, referencia: str, ids: set[str], *, eixos: set[str]) -> list[str]:
    """Pergunta com gabarito: campos, norma e artigo existentes na base, conferência e regra de risco."""
    if not isinstance(item, dict):
        return [f"{referencia}: registro deve ser um objeto"]
    erros = []
    for campo in ("id", "pergunta", "autor", "resposta_esperada", "fonte"):
        if not _texto(item.get(campo)):
            erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
    if _texto(item.get("id")):
        if item["id"] in ids:
            erros.append(f"{referencia}: id duplicado '{item['id']}'")
        ids.add(item["id"])
    if not _lista_textos(item.get("pontos_obrigatorios")):
        erros.append(f"{referencia}: campo 'pontos_obrigatorios' deve ser lista não vazia de textos")
    erros += _validar_normas(item.get("normas_aceitas"), eixos, referencia)
    if _texto(item.get("pergunta")) and (regra := avaliar(item["pergunta"])):
        erros.append(f"{referencia}: pergunta dispara alerta de risco ({regra['id']})")
    conferencia = item.get("conferencia")
    revisor = conferencia.get("revisor") if isinstance(conferencia, dict) else None
    if not _texto(revisor):
        erros.append(f"{referencia}: conferencia.revisor obrigatório e não vazio (conferência pendente)")
    elif _texto(item.get("autor")) and revisor.strip().casefold() in item["autor"].casefold():
        erros.append(f"{referencia}: revisor deve ser diferente do autor")
    return erros


def validar_desenvolvimento_beneficios(caminho: Path = ARQUIVO_DESENVOLVIMENTO_BENEFICIOS) -> list[str]:
    """Erros do conjunto de desenvolvimento de benefícios; lista vazia indica conjunto válido."""
    try:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{caminho}: não foi possível ler YAML: {exc}"]
    if not isinstance(dados, dict):
        return [f"{caminho}: raiz deve ser um objeto com versao, perguntas, extras e juridico"]

    erros: list[str] = []
    if type(dados.get("versao")) is not int or dados["versao"] != 1:
        erros.append(f"{caminho}: 'versao' deve ser 1")
    listas = {}
    for chave in ("perguntas", "extras", "juridico"):
        listas[chave] = dados.get(chave) if isinstance(dados.get(chave), list) else []
        if not listas[chave]:
            erros.append(f"{caminho}: '{chave}' deve ser uma lista não vazia")

    ids: set[str] = set()
    for indice, item in enumerate(listas["perguntas"], start=1):
        referencia = f"{caminho}:perguntas[{indice}]"
        erros += _validar_item_beneficios(item, referencia, ids, eixos=EIXOS_BENEFICIOS)
        if isinstance(item, dict):
            if item.get("programa") not in PROGRAMAS_BENEFICIOS:
                erros.append(f"{referencia}: programa inválido '{item.get('programa')}'")
            if not isinstance(item.get("sem_nome_oficial"), bool):
                erros.append(f"{referencia}: 'sem_nome_oficial' deve ser verdadeiro ou falso")

    perguntas = [p for p in listas["perguntas"] if isinstance(p, dict)]
    faltando = PROGRAMAS_BENEFICIOS - {p.get("programa") for p in perguntas}
    if faltando:
        erros.append(f"{caminho}: programas sem pergunta: {sorted(faltando)}")
    if perguntas and not any(p.get("sem_nome_oficial") is True for p in perguntas):
        erros.append(f"{caminho}: nenhuma pergunta sem o nome oficial do programa")

    for indice, item in enumerate(listas["extras"], start=1):
        referencia = f"{caminho}:extras[{indice}]"
        if not isinstance(item, dict):
            erros.append(f"{referencia}: registro deve ser um objeto")
            continue
        for campo in ("id", "pergunta", "autor"):
            if not _texto(item.get(campo)):
                erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
        if item.get("categoria") != "quase_do_tema":
            erros.append(f"{referencia}: categoria de extra deve ser 'quase_do_tema'")
        if _texto(item.get("id")):
            if item["id"] in ids:
                erros.append(f"{referencia}: id duplicado '{item['id']}'")
            ids.add(item["id"])
        if _texto(item.get("pergunta")) and (regra := avaliar(item["pergunta"])):
            erros.append(f"{referencia}: pergunta dispara alerta de risco ({regra['id']})")

    tem_aluguel_mp = False
    for indice, item in enumerate(listas["juridico"], start=1):
        referencia = f"{caminho}:juridico[{indice}]"
        erros += _validar_item_beneficios(item, referencia, ids, eixos={"juridico"})
        if isinstance(item, dict):
            if item.get("eixo_esperado") != "juridico":
                erros.append(f"{referencia}: 'eixo_esperado' deve ser 'juridico'")
            tem_aluguel_mp |= "aluguel da maria da penha" in _sem_pontuacao(str(item.get("pergunta", "")))
    if not tem_aluguel_mp:
        erros.append(f"{caminho}: falta a pergunta 'como funciona o aluguel da Maria da Penha?' no eixo jurídico")
    return erros


def validar_medicao_beneficios(
    caminho: Path = ARQUIVO_MEDICAO_BENEFICIOS, desenvolvimento: Path = ARQUIVO_DESENVOLVIMENTO_BENEFICIOS
) -> list[str]:
    """A medição do RAG de benefícios não pode repetir perguntas usadas para calibrar o limite."""
    try:
        medicao = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        calibracao = yaml.safe_load(desenvolvimento.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"não foi possível ler os conjuntos de benefícios: {exc}"]

    def perguntas(dados: dict) -> list[dict]:
        return [i for chave in ("perguntas", "extras", "juridico") for i in dados.get(chave) or [] if isinstance(i, dict)]

    usadas = {_sem_pontuacao(i["pergunta"]) for i in perguntas(calibracao) if _texto(i.get("pergunta"))}
    return [
        f"{caminho}: '{i.get('id')}' repete uma pergunta do conjunto de desenvolvimento de benefícios"
        for i in perguntas(medicao)
        if _texto(i.get("pergunta")) and _sem_pontuacao(i["pergunta"]) in usadas
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tipo", choices=("desenvolvimento", "oficial", "todos", "beneficios"),
        help="Conjunto a validar ('beneficios': perguntas de desenvolvimento de benefícios da S4)",
    )
    parser.add_argument(
        "--diretorio", type=Path, default=PASTA_CONJUNTOS,
        help="Pasta dos conjuntos (padrão: avaliacao/conjuntos/)",
    )
    args = parser.parse_args()
    if args.tipo == "beneficios":
        erros = validar_desenvolvimento_beneficios()
        if ARQUIVO_MEDICAO_BENEFICIOS.is_file():
            erros += validar_medicao_beneficios()
        for erro in erros:
            print(erro)
        if not erros:
            print("Conjunto válido: perguntas de desenvolvimento de benefícios")
        return 1 if erros else 0
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
