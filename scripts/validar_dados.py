#!/usr/bin/env python3
"""Valida os arquivos levantados na mudança s2-fontes-df:
- dados/rede_protecao_df.csv
- dados/normas.csv
- dados/fonar/notas.md

Garante que todas as colunas obrigatórias estão preenchidas, os valores categóricos
estão dentro do esperado, os CEPs estão na faixa oficial do DF, as Regiões
Administrativas (RAs) pertencem à lista oficial do DF, não há linhas duplicadas,
as normas do fontes.yaml batem com o normas.csv e todas as URLs pertencem a
domínios públicos oficiais.
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
ARQUIVO_FONTES_YAML = RAIZ / "dados" / "fontes" / "fontes.yaml"
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

# Lista oficial das 35 Regiões Administrativas do Distrito Federal
RAS_OFICIAIS_DF = {
    "Plano Piloto",
    "Gama",
    "Taguatinga",
    "Brazlândia",
    "Sobradinho",
    "Planaltina",
    "Paranoá",
    "Núcleo Bandeirante",
    "Ceilândia",
    "Guará",
    "Cruzeiro",
    "Samambaia",
    "Santa Maria",
    "São Sebastião",
    "Recanto das Emas",
    "Lago Sul",
    "Riacho Fundo",
    "Lago Norte",
    "Candangolândia",
    "Águas Claras",
    "Riacho Fundo II",
    "Sudoeste/Octogonal",
    "Varjão",
    "Park Way",
    "SCIA/Estrutural",
    "Sobradinho II",
    "Jardim Botânico",
    "Itapoã",
    "SIA",
    "Vicente Pires",
    "Fercal",
    "Sol Nascente/Pôr do Sol",
    "Arniqueira",
    "Arapoanga",
    "Água Quente",
}

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
CEP_DF_MIN = 70000000
CEP_DF_MAX = 73699999

CLASSIFICACOES_FONAR = {
    "adaptável para autoaplicação",
    "adaptável com cuidado",
    "não adaptável",
}

# Numeração oficial do Anexo Único da Portaria Conjunta CNJ/CNMP nº 6/2025 (Parte I)
PERGUNTAS_FONAR_2025_ESPERADAS = {
    *[str(n) for n in range(1, 25)],
    "2.1",
    "2.2",
    "5.1",
    "12.1",
    "14.1",
    "14.2",
    "14.3",
    "14.4",
}


def _data_iso_valida(valor: str) -> bool:
    try:
        date.fromisoformat(valor)
        return True
    except ValueError:
        return False


def _cep_df_valido(cep: str) -> tuple[bool, str]:
    if not PADRAO_CEP.match(cep):
        return False, f"CEP '{cep}' fora do formato 00000-000"
    numero = int(cep.replace("-", ""))
    if not (CEP_DF_MIN <= numero <= CEP_DF_MAX):
        return False, f"CEP '{cep}' fora da faixa do Distrito Federal (70000-000 a 73699-999)"
    return True, ""


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


def _carregar_urls_fontes_yaml(caminho_yaml: Path) -> list[tuple[str, str]]:
    """Extrai pares (citacao, url) de dados/fontes/fontes.yaml."""
    texto = caminho_yaml.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-untyped]

        dados = yaml.safe_load(texto) or {}
        normas = dados.get("normas") or []
        return [
            (str(item.get("citacao") or "").strip(), str(item.get("url") or "").strip())
            for item in normas
            if item.get("citacao") and item.get("url")
        ]
    except ModuleNotFoundError:
        pares: list[tuple[str, str]] = []
        citacao_atual: str | None = None
        for linha in texto.splitlines():
            m_cit = re.match(r'^\s*citacao:\s*["\']?([^"\']+)["\']?\s*$', linha)
            if m_cit:
                citacao_atual = m_cit.group(1).strip()
                continue
            m_url = re.match(r'^\s*url:\s*["\']?([^"\']+)["\']?\s*$', linha)
            if m_url and citacao_atual:
                pares.append((citacao_atual, m_url.group(1).strip()))
                citacao_atual = None
        return pares


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
        nomes_vistos: set[str] = set()
        linhas_vistas: set[tuple[str, ...]] = set()

        for idx, linha in enumerate(linhas, start=2):
            for col in COLUNAS_REDE:
                valor = (linha.get(col) or "").strip()
                if not valor:
                    erros.append(f"{caminho.name}:{idx}: coluna '{col}' vazia")

            chave_linha = tuple((linha.get(c) or "").strip() for c in COLUNAS_REDE)
            if chave_linha in linhas_vistas:
                erros.append(f"{caminho.name}:{idx}: linha duplicada")
            linhas_vistas.add(chave_linha)

            nome = (linha.get("nome") or "").strip()
            if nome:
                nome_norm = nome.lower()
                if nome_norm in nomes_vistos:
                    erros.append(f"{caminho.name}:{idx}: serviço duplicado '{nome}'")
                nomes_vistos.add(nome_norm)

            tipo = (linha.get("tipo") or "").strip()
            if tipo and tipo not in TIPOS_REDE_VALIDOS:
                erros.append(
                    f"{caminho.name}:{idx}: tipo '{tipo}' inválido (esperado um de {sorted(TIPOS_REDE_VALIDOS)})"
                )
            tipos_encontrados.add(tipo)

            ra = (linha.get("ra") or "").strip()
            if ra and ra not in RAS_OFICIAIS_DF:
                erros.append(
                    f"{caminho.name}:{idx}: RA '{ra}' não pertence à lista oficial de Regiões Administrativas do DF"
                )

            cep = (linha.get("cep") or "").strip()
            if cep:
                ok_cep, msg_cep = _cep_df_valido(cep)
                if not ok_cep:
                    erros.append(f"{caminho.name}:{idx}: {msg_cep}")

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


def validar_normas(
    caminho: Path = ARQUIVO_NORMAS,
    caminho_fontes_yaml: Path | None = ARQUIVO_FONTES_YAML,
) -> list[str]:
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
        normas_vistas: set[str] = set()
        urls_vistos: set[str] = set()

        for idx, linha in enumerate(linhas, start=2):
            for col in COLUNAS_NORMAS:
                valor = (linha.get(col) or "").strip()
                if not valor:
                    erros.append(f"{caminho.name}:{idx}: coluna '{col}' vazia")

            nome_norma = (linha.get("norma") or "").strip()
            if nome_norma:
                chave_norma = nome_norma.lower()
                if chave_norma in normas_vistas:
                    erros.append(f"{caminho.name}:{idx}: norma duplicada '{nome_norma}'")
                normas_vistas.add(chave_norma)

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
            if url:
                if not _url_oficial_valida(url):
                    erros.append(f"{caminho.name}:{idx}: fonte_url '{url}' não pertence a domínio oficial")
                if url in urls_vistos:
                    erros.append(f"{caminho.name}:{idx}: fonte_url duplicada '{url}'")
                urls_vistos.add(url)

        if esferas_encontradas != ESFERAS_VALIDAS:
            erros.append(
                f"{caminho.name}: deve conter normas federais e distritais (encontrado: {sorted(esferas_encontradas)})"
            )

        if caminho_fontes_yaml and caminho_fontes_yaml.exists():
            for citacao, url_yaml in _carregar_urls_fontes_yaml(caminho_fontes_yaml):
                if url_yaml not in urls_vistos:
                    erros.append(
                        f"{caminho.name}: norma '{citacao}' de {caminho_fontes_yaml.name} ausente ou com URL divergente (esperado '{url_yaml}')"
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
        r"^\|\s*\*\*(\d+(?:\.\d+)?)\*\*\s*\|([^|]+)\|([^|]+)\|([^|]+)\|",
        re.MULTILINE,
    )
    perguntas_encontradas: dict[str, tuple[str, str, str]] = {}
    for match in padrao_linha_pergunta.finditer(texto):
        codigo = match.group(1).strip()
        enunciado = match.group(2).strip()
        classificacao = match.group(3).strip().strip("`")
        motivo = match.group(4).strip()

        if codigo in perguntas_encontradas:
            erros.append(f"{caminho.name}: pergunta {codigo} duplicada")
        perguntas_encontradas[codigo] = (enunciado, classificacao, motivo)

        if not enunciado:
            erros.append(f"{caminho.name}: pergunta {codigo} sem enunciado")
        if classificacao not in CLASSIFICACOES_FONAR:
            erros.append(
                f"{caminho.name}: pergunta {codigo} com classificação inválida '{classificacao}'"
            )
        if not motivo:
            erros.append(f"{caminho.name}: pergunta {codigo} sem motivo/justificativa")

    faltantes = sorted(
        PERGUNTAS_FONAR_2025_ESPERADAS - set(perguntas_encontradas.keys()),
        key=lambda x: [int(p) for p in x.split(".")],
    )
    if faltantes:
        erros.append(
            f"{caminho.name}: faltam perguntas numeradas da Parte I do Fonar 2025: {faltantes}"
        )

    extras = sorted(
        set(perguntas_encontradas.keys()) - PERGUNTAS_FONAR_2025_ESPERADAS,
        key=lambda x: [int(p) for p in x.split(".")],
    )
    if extras:
        erros.append(
            f"{caminho.name}: perguntas fora da numeração oficial da Parte I do Fonar 2025: {extras}"
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
