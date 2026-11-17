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
PASTA_CONJUNTOS_S4 = PASTA_CONJUNTOS / "s4"

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


def _ler_yaml(caminho: Path, raiz_esperada: str = "casos") -> tuple[dict | None, list[str]]:
    """Lê um conjunto S4 e devolve erros de arquivo/estrutura básica."""
    if not caminho.is_file():
        return None, [f"Arquivo não encontrado: {caminho}"]
    try:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return None, [f"{caminho}: não foi possível ler YAML: {exc}"]
    if not isinstance(dados, dict):
        return None, [f"{caminho}: raiz deve ser um objeto com versao e {raiz_esperada}"]
    erros = []
    if type(dados.get("versao")) is not int or dados["versao"] != 1:
        erros.append(f"{caminho}: 'versao' deve ser 1")
    if not _texto(dados.get("descricao")):
        erros.append(f"{caminho}: 'descricao' obrigatória e não vazia")
    casos = dados.get(raiz_esperada)
    if not isinstance(casos, list):
        erros.append(f"{caminho}: '{raiz_esperada}' deve ser uma lista")
        return dados, erros
    return dados, erros


def _validar_identidade_caso(item: dict, referencia: str, ids: set[str]) -> list[str]:
    erros = []
    identificador = item.get("id")
    if not _texto(identificador):
        erros.append(f"{referencia}: campo 'id' obrigatório e não vazio")
    elif identificador in ids:
        erros.append(f"{referencia}: id duplicado '{identificador}'")
    else:
        ids.add(identificador)
    for campo in ("autor",):
        if not _texto(item.get(campo)):
            erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
    conferencia = item.get("conferencia")
    revisor = conferencia.get("revisor") if isinstance(conferencia, dict) else None
    if not _texto(revisor):
        erros.append(f"{referencia}: conferencia.revisor obrigatório e não vazio")
    elif _texto(item.get("autor")) and revisor.strip().casefold() == item["autor"].strip().casefold():
        erros.append(f"{referencia}: revisor deve ser diferente do autor")
    return erros


def validar_elegibilidade_s4(caminho: Path = PASTA_CONJUNTOS_S4 / "elegibilidade.yaml") -> list[str]:
    """Valida estrutura, fontes, conferência e cobertura do conjunto de elegibilidade S4."""
    dados, erros = _ler_yaml(caminho)
    if dados is None:
        return erros
    casos = dados.get("casos") if isinstance(dados.get("casos"), list) else []
    beneficios = dados.get("beneficios")
    if not isinstance(beneficios, list) or not beneficios or not all(_texto(b) for b in beneficios):
        erros.append(f"{caminho}: 'beneficios' deve ser uma lista não vazia de textos")
        beneficios = []
    if not 20 <= len(casos) <= 30:
        erros.append(f"{caminho}: esperados de 20 a 30 perfis; encontrados {len(casos)}")

    ids: set[str] = set()
    por_id: dict[str, dict] = {}
    for indice, item in enumerate(casos, start=1):
        referencia = f"{caminho}:casos[{indice}]"
        if not isinstance(item, dict):
            erros.append(f"{referencia}: registro deve ser um objeto")
            continue
        referencia += f" ({item.get('id', 'sem id')})"
        erros.extend(_validar_identidade_caso(item, referencia, ids))
        if _texto(item.get("id")):
            por_id[item["id"]] = item
        if not _texto(item.get("descricao")):
            erros.append(f"{referencia}: campo 'descricao' obrigatório e não vazio")
        perfil = item.get("perfil")
        if not isinstance(perfil, dict):
            erros.append(f"{referencia}: campo 'perfil' deve ser um objeto")
        esperado = item.get("esperado")
        if not isinstance(esperado, dict) or not esperado:
            erros.append(f"{referencia}: campo 'esperado' deve ser um objeto não vazio")
            esperado = {}
        elif beneficios and set(esperado) != set(beneficios):
            erros.append(f"{referencia}: 'esperado' deve conter exatamente os benefícios declarados")
        if any(not _texto(v) for v in esperado.values()):
            erros.append(f"{referencia}: cada benefício em 'esperado' deve ter uma situação não vazia")
        if not _texto(item.get("fonte")):
            erros.append(f"{referencia}: campo 'fonte' obrigatório e não vazio")
        fontes = item.get("fontes_por_beneficio")
        if not isinstance(fontes, dict) or (beneficios and set(fontes) != set(esperado)):
            erros.append(f"{referencia}: 'fontes_por_beneficio' deve citar a fonte de cada benefício esperado")
        elif any(not _texto(fontes.get(b)) for b in esperado):
            erros.append(f"{referencia}: fonte ausente para um benefício esperado")

    # A cobertura é aferida pelos dados dos perfis e pelos limites versionados na regra.
    try:
        regra = json.loads((RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8"))
        regras = {r["id"]: r for r in regra["regras"]}
        salario = regra["salario_minimo"]["valor"]
        bf_corte = regras["bolsa_familia"]["requisitos"]["renda_per_capita_max"]
        bpc_corte = salario * regras["bpc"]["requisitos"]["renda_per_capita_fracao_sm"]
        aluguel = regras["aluguel_social_df"]["requisitos"]
        aluguel_pc = salario * aluguel["renda_per_capita_fracao_sm"]
        aluguel_total = salario * aluguel["renda_familiar_multiplo_sm"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return erros + [f"{caminho}: não foi possível ler limites de regras/beneficios.json: {exc}"]

    perfis = [i.get("perfil") for i in casos if isinstance(i, dict) and isinstance(i.get("perfil"), dict)]
    rendas = [p.get("renda_total") for p in perfis]
    pessoas = [p.get("numero_pessoas") for p in perfis]
    validos = [(r, n) for r, n in zip(rendas, pessoas) if isinstance(r, (int, float)) and not isinstance(r, bool) and isinstance(n, int) and not isinstance(n, bool) and n > 0]
    bate_corte = lambda r, n: (
        r / n == bf_corte or r / n == bpc_corte or r / n == aluguel_pc or r == aluguel_total
    )
    bate_acima = lambda r, n: (
        r / n == bf_corte + 1 or r / n == bpc_corte + 1 or r / n == aluguel_pc + 1 or r == aluguel_total + 1
    )
    if not any(bate_corte(r, n) for r, n in validos):
        erros.append(f"{caminho}: falta caso com renda per capita ou familiar exatamente no limite")
    if not any(bate_acima(r, n) for r, n in validos):
        erros.append(f"{caminho}: falta caso com renda um real acima do limite")
    if not any(isinstance(r, str) and "prefiro" in r.casefold() and "informar" in r.casefold() for r in rendas):
        erros.append(f"{caminho}: falta caso com 'prefiro não informar' em dado necessário")
    campos_necessarios = ("renda_total", "numero_pessoas")
    if not any(any(p.get(campo) is None for campo in campos_necessarios) for p in perfis):
        erros.append(f"{caminho}: falta perfil incompleto com dado necessário ausente")
    return erros


def validar_triagem_s4(caminho: Path = PASTA_CONJUNTOS_S4 / "triagem.yaml") -> list[str]:
    """Valida casos de triagem, fonte do gabarito e conferência independente."""
    dados, erros = _ler_yaml(caminho)
    if dados is None:
        return erros
    casos = dados.get("casos") if isinstance(dados.get("casos"), list) else []
    ids: set[str] = set()
    for indice, item in enumerate(casos, start=1):
        referencia = f"{caminho}:casos[{indice}]"
        if not isinstance(item, dict):
            erros.append(f"{referencia}: registro deve ser um objeto")
            continue
        referencia += f" ({item.get('id', 'sem id')})"
        erros.extend(_validar_identidade_caso(item, referencia, ids))
        for campo in ("descricao", "nivel_esperado", "itens_fonar", "fonte"):
            if not _texto(item.get(campo)):
                erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
        if not isinstance(item.get("respostas"), dict) or not item["respostas"]:
            erros.append(f"{referencia}: campo 'respostas' deve ser um objeto não vazio")
    if not casos:
        erros.append(f"{caminho}: deve conter ao menos um caso de triagem")
    return erros


def validar_roteamento_s4(caminho: Path = PASTA_CONJUNTOS_S4 / "roteamento.yaml") -> list[str]:
    """Valida mensagens e cobertura dos pares e tipos essenciais de roteamento S4."""
    dados, erros = _ler_yaml(caminho)
    if dados is None:
        return erros
    casos = dados.get("casos") if isinstance(dados.get("casos"), list) else []
    ids: set[str] = set()
    itens: list[dict] = []
    for indice, item in enumerate(casos, start=1):
        referencia = f"{caminho}:casos[{indice}]"
        if not isinstance(item, dict):
            erros.append(f"{referencia}: registro deve ser um objeto")
            continue
        referencia += f" ({item.get('id', 'sem id')})"
        itens.append(item)
        erros.extend(_validar_identidade_caso(item, referencia, ids))
        for campo in ("texto", "agente_esperado"):
            if not _texto(item.get(campo)):
                erros.append(f"{referencia}: campo '{campo}' obrigatório e não vazio")
        if item.get("tipo_esperado") is not None and not _texto(item.get("tipo_esperado")):
            erros.append(f"{referencia}: 'tipo_esperado' deve ser texto não vazio ou null")
        texto = item.get("texto")
        if _texto(texto) and (regra := avaliar(texto)):
            erros.append(f"{referencia}: mensagem dispara alerta de risco ({regra['id']})")

    def tem(predicado) -> bool:
        return any(predicado(i) for i in itens)

    if not tem(lambda i: i.get("agente_esperado") == "beneficios" and i.get("tipo_esperado") == "direito"):
        erros.append(f"{caminho}: falta pergunta de direito roteada para benefícios")
    if not tem(lambda i: i.get("agente_esperado") == "beneficios" and i.get("tipo_esperado") == "explicacao"):
        erros.append(f"{caminho}: falta pergunta de explicação roteada para benefícios")
    if not tem(lambda i: "aluguel da maria da penha" in str(i.get("texto", "")).casefold() and i.get("agente_esperado") == "juridico"):
        erros.append(f"{caminho}: falta o par 'aluguel da Maria da Penha' com agente juridico")
    if not tem(lambda i: "aluguel social" in str(i.get("texto", "")).casefold() and i.get("agente_esperado") == "beneficios"):
        erros.append(f"{caminho}: falta pergunta sobre Aluguel Social do DF com agente beneficios")
    if not tem(lambda i: str(i.get("texto", "")).count("?") >= 2 or any(m in str(i.get("texto", "")).casefold() for m in ("e também", "outra coisa", "além disso"))):
        erros.append(f"{caminho}: falta mensagem com mais de uma pergunta")
    if not tem(lambda i: i.get("agente_esperado") == "fora_do_tema"):
        erros.append(f"{caminho}: falta mensagem fora do tema")
    if not itens:
        erros.append(f"{caminho}: deve conter ao menos uma mensagem")
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
        "tipo", choices=("desenvolvimento", "oficial", "todos", "beneficios", "s4"),
        help="Conjunto a validar ('beneficios': perguntas de desenvolvimento; 's4': três conjuntos da avaliação)",
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
    if args.tipo == "s4":
        diretorio_s4 = args.diretorio / "s4"
        validadores = (
            ("elegibilidade", validar_elegibilidade_s4),
            ("triagem", validar_triagem_s4),
            ("roteamento", validar_roteamento_s4),
        )
        erros = [erro for nome, validar in validadores for erro in validar(diretorio_s4 / f"{nome}.yaml")]
        for erro in erros:
            print(erro)
        if not erros:
            print("Conjuntos válidos: elegibilidade, triagem, roteamento (S4)")
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
