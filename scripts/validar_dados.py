#!/usr/bin/env python3
"""Valida os arquivos levantados na mudança s2-fontes-df:
- dados/rede_protecao_df.csv
- dados/normas.csv
- dados/fonar/notas.md

Garante que todas as colunas obrigatórias estão preenchidas, os valores categóricos
estão dentro do esperado, os CEPs e datas seguem o formato correto e todas as URLs
pertencem a domínios públicos oficiais.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent

ARQUIVO_REDE = RAIZ / "dados" / "rede_protecao_df.csv"
ARQUIVO_NORMAS = RAIZ / "dados" / "normas.csv"
ARQUIVO_FONAR = RAIZ / "dados" / "fonar" / "notas.md"

COLUNAS_REDE = [
    "nome",
    "tipo",
    "ra",
    "endereco",
    "cep",
    "telefone",
    "horario",
    "fonte_url",
    "data_verificacao",
]
TIPOS_REDE_VALIDOS = {"CMB", "CEAM", "DEAM", "Defensoria", "Juizado", "outro"}

COLUNAS_NORMAS = [
    "norma",
    "esfera",
    "tema",
    "artigos_relevantes",
    "resumo",
    "vigencia_inicio",
    "fonte_url",
    "data_verificacao",
]
ESFERAS_VALIDAS = {"federal", "distrital"}
TEMAS_VALIDOS = {"juridico", "beneficio", "risco"}

SUFIXOS_DOMINIOS_OFICIAIS = (
    ".gov.br",
    ".df.gov.br",
    ".leg.br",
    ".jus.br",
    ".mp.br",
    ".def.br",
)

PADRAO_CEP = re.compile(r"^\d{5}-\d{3}$")
CLASSIFICACOES_FONAR = {
    "adaptável para autoaplicação",
    "adaptável com cuidado",
    "não adaptável",
}


def _data_iso_valida(valor: str) -> bool:
    try:
        date.fromisoformat(valor)
        return True
    except ValueError:
        return False


def _url_oficial_valida(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.netloc.lower().split(":")[0]
    return any(
        host == sufixo.lstrip(".") or host.endswith(sufixo)
        for sufixo in SUFIXOS_DOMINIOS_OFICIAIS
    )


def validar_rede_protecao(caminho: Path = ARQUIVO_REDE) -> list[str]:
    erros: list[str] = []
    if not caminho.exists():
        return [f"Arquivo não encontrado: {caminho}"]

    with caminho.open(encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS_REDE:
            erros.append(
                f"{caminho.name}: cabeçalho inválido {leitor.fieldnames}; esperado {COLUNAS_REDE}"
            )
            return erros

        linhas = list(leitor)
        if not linhas:
            erros.append(f"{caminho.name}: arquivo sem registros")
            return erros

        tipos_encontrados: set[str] = set()
        for idx, linha in enumerate(linhas, start=2):
            for col in COLUNAS_REDE:
                valor = (linha.get(col) or "").strip()
                if not valor:
                    erros.append(f"{caminho.name}:{idx}: coluna '{col}' vazia")

            tipo = (linha.get("tipo") or "").strip()
            if tipo and tipo not in TIPOS_REDE_VALIDOS:
                erros.append(
                    f"{caminho.name}:{idx}: tipo '{tipo}' inválido (esperado um de {sorted(TIPOS_REDE_VALIDOS)})"
                )
            tipos_encontrados.add(tipo)

            cep = (linha.get("cep") or "").strip()
            if cep and not PADRAO_CEP.match(cep):
                erros.append(f"{caminho.name}:{idx}: CEP '{cep}' fora do formato 00000-000")

            url = (linha.get("fonte_url") or "").strip()
            if url and not _url_oficial_valida(url):
                erros.append(f"{caminho.name}:{idx}: fonte_url '{url}' não pertence a domínio oficial")

            data_ver = (linha.get("data_verificacao") or "").strip()
            if data_ver and not _data_iso_valida(data_ver):
                erros.append(f"{caminho.name}:{idx}: data_verificacao '{data_ver}' inválida")

        obrigatorios = {"CMB", "CEAM", "DEAM", "Defensoria", "Juizado"}
        faltando = obrigatorios - tipos_encontrados
        if faltando:
            erros.append(
                f"{caminho.name}: faltam categorias obrigatórias da rede do DF: {sorted(faltando)}"
            )

    return erros


def validar_normas(caminho: Path = ARQUIVO_NORMAS) -> list[str]:
    erros: list[str] = []
    if not caminho.exists():
        return [f"Arquivo não encontrado: {caminho}"]

    with caminho.open(encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS_NORMAS:
            erros.append(
                f"{caminho.name}: cabeçalho inválido {leitor.fieldnames}; esperado {COLUNAS_NORMAS}"
            )
            return erros

        linhas = list(leitor)
        if not linhas:
            erros.append(f"{caminho.name}: arquivo sem registros")
            return erros

        esferas_encontradas: set[str] = set()
        for idx, linha in enumerate(linhas, start=2):
            for col in COLUNAS_NORMAS:
                valor = (linha.get(col) or "").strip()
                if not valor:
                    erros.append(f"{caminho.name}:{idx}: coluna '{col}' vazia")

            esfera = (linha.get("esfera") or "").strip()
            if esfera and esfera not in ESFERAS_VALIDAS:
                erros.append(
                    f"{caminho.name}:{idx}: esfera '{esfera}' inválida (esperado {sorted(ESFERAS_VALIDAS)})"
                )
            esferas_encontradas.add(esfera)

            tema = (linha.get("tema") or "").strip()
            if tema and tema not in TEMAS_VALIDOS:
                erros.append(
                    f"{caminho.name}:{idx}: tema '{tema}' inválido (esperado {sorted(TEMAS_VALIDOS)})"
                )

            for col_data in ("vigencia_inicio", "data_verificacao"):
                valor_data = (linha.get(col_data) or "").strip()
                if valor_data and not _data_iso_valida(valor_data):
                    erros.append(f"{caminho.name}:{idx}: {col_data} '{valor_data}' inválida")

            url = (linha.get("fonte_url") or "").strip()
            if url and not _url_oficial_valida(url):
                erros.append(f"{caminho.name}:{idx}: fonte_url '{url}' não pertence a domínio oficial")

        if esferas_encontradas != ESFERAS_VALIDAS:
            erros.append(
                f"{caminho.name}: deve conter normas federais e distritais (encontrado: {sorted(esferas_encontradas)})"
            )

    return erros


def validar_fonar(caminho: Path = ARQUIVO_FONAR) -> list[str]:
    erros: list[str] = []
    if not caminho.exists():
        return [f"Arquivo não encontrado: {caminho}"]

    texto = caminho.read_text(encoding="utf-8")
    if not texto.strip():
        return [f"{caminho.name}: arquivo vazio"]

    if "Portaria Conjunta" not in texto or "14.149" not in texto:
        erros.append(
            f"{caminho.name}: deve citar a Lei 14.149/2021 e a Portaria Conjunta CNJ/CNMP nº 6/2025"
        )

    padrao_linha_pergunta = re.compile(
        r"^\|\s*\*\*(\d+)\*\*\s*\|([^|]+)\|([^|]+)\|([^|]+)\|",
        re.MULTILINE,
    )
    perguntas_encontradas: dict[int, tuple[str, str, str]] = {}
    for match in padrao_linha_pergunta.finditer(texto):
        numero = int(match.group(1))
        enunciado = match.group(2).strip()
        classificacao = match.group(3).strip().strip("`")
        motivo = match.group(4).strip()
        perguntas_encontradas[numero] = (enunciado, classificacao, motivo)

        if not enunciado:
            erros.append(f"{caminho.name}: pergunta {numero} sem enunciado")
        if classificacao not in CLASSIFICACOES_FONAR:
            erros.append(
                f"{caminho.name}: pergunta {numero} com classificação inválida '{classificacao}'"
            )
        if not motivo:
            erros.append(f"{caminho.name}: pergunta {numero} sem motivo/justificativa")

    esperadas = set(range(1, 28))
    faltantes = sorted(esperadas - set(perguntas_encontradas.keys()))
    if faltantes:
        erros.append(
            f"{caminho.name}: faltam perguntas numeradas da Parte I do Fonar: {faltantes}"
        )

    return erros


def validar_tudo() -> list[str]:
    return validar_rede_protecao() + validar_normas() + validar_fonar()


def main() -> int:
    erros = validar_tudo()
    if erros:
        print("Erros encontrados na validação de dados (s2-fontes-df):", file=sys.stderr)
        for erro in erros:
            print(f"  - {erro}", file=sys.stderr)
        return 1

    print("OK: dados/rede_protecao_df.csv, dados/normas.csv e dados/fonar/notas.md válidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
