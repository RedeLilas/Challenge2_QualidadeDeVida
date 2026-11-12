#!/usr/bin/env python3
"""Confere o retorno do corretor externo e calcula as métricas da comparação LLM x RAG.

    uv run python -m scripts.conferir avaliacao/rodadas/<rodada>

Espera, dentro da pasta da rodada:
- retornos/A-precisao.json, A-fidelidade.json, B-precisao.json e B-fidelidade.json: o JSON
  devolvido pelo corretor, no formato pedido pela rubrica (uma lista com um item por código);
- retornos/registro.yaml: modelo corretor e data de cada envio, por exemplo
  `A-precisao: {modelo: <nome>, data: 2026-11-12}`.

Regras:
- Linha faltando: a correção daquele arquivo não é aceita, e os códigos faltantes são listados.
- Trecho que não existe no texto enviado: a linha é apontada e a marcação conta contra a resposta
  (ponto "presente" vira ausente, afirmação "com suporte" vira sem suporte).
- Resposta errada de propósito aprovada pelo corretor: a correção daquele arquivo é rejeitada.
- Recusa (resposta igual ao texto de recusa do sistema) e presença de citação são calculadas
  por código. Recusa dentro do tema conta como erro de precisão.

Grava resultado.yaml na pasta da rodada.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from app.rag.resposta import LEIS_JURIDICAS, RECUSA, extrair_referencias

ARQUIVOS = ("A", "B")
TIPOS = ("precisao", "fidelidade")
VERSOES = ("rag", "sem_rag")
SUPORTES = ("sim", "nao", "fora_da_base")


class ErroConferencia(RuntimeError):
    """A conferência não pode começar (faltam arquivos da rodada ou dos retornos)."""


def _ler(caminho: Path):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def _normalizar(texto) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip().strip("\"'“”…").strip()


def _contido(trecho, texto: str) -> bool:
    trecho = _normalizar(trecho)
    return bool(trecho) and trecho in _normalizar(texto)


def _ler_json(caminho: Path) -> list:
    texto = caminho.read_text(encoding="utf-8").strip()
    # O corretor costuma devolver o JSON dentro de um bloco ```json ... ```.
    if bloco := re.search(r"```(?:json)?\s*(.*?)```", texto, re.DOTALL):
        texto = bloco[1]
    dados = json.loads(texto)
    if isinstance(dados, dict) and isinstance(dados.get("itens"), list):
        dados = dados["itens"]
    if not isinstance(dados, list) or not all(isinstance(i, dict) for i in dados):
        raise ValueError("o retorno deve ser uma lista de objetos, um por código")
    return dados


def _corrigir_precisao(item: dict, enviado: dict, codigo: str, invalidas: list[str]) -> tuple[bool, bool]:
    """(certa depois de conferir os trechos, aprovada pelo corretor nas marcações dele)."""
    pontos = {p.get("numero"): p for p in item.get("pontos") or [] if isinstance(p, dict)}
    esperados = range(1, len(enviado["pontos_obrigatorios"]) + 1)
    aprovada = all(pontos.get(n, {}).get("presente") is True for n in esperados) and item.get("contradiz") is False
    certa = item.get("contradiz") is False
    for n in esperados:
        ponto = pontos.get(n)
        if ponto is None:
            invalidas.append(f"{codigo}: ponto {n} sem marcação")
            certa = False
        elif ponto.get("presente") is True and not _contido(ponto.get("trecho"), enviado["resposta"]):
            invalidas.append(f"{codigo}: trecho do ponto {n} não existe na resposta enviada")
            certa = False
        elif ponto.get("presente") is not True:
            certa = False
    if item.get("contradiz") is True and not _contido(item.get("trecho_contradicao"), enviado["resposta"]):
        # Contradição sem trecho continua contando contra a resposta.
        invalidas.append(f"{codigo}: trecho da contradição não existe na resposta enviada")
    return certa, aprovada


def _corrigir_fidelidade(item: dict, enviado: dict, codigo: str, invalidas: list[str]) -> tuple[dict, bool]:
    """(contagem de afirmações depois de conferir os trechos, aprovada pelo corretor)."""
    afirmacoes = [a for a in item.get("afirmacoes") or [] if isinstance(a, dict)]
    aprovada = all(a.get("suporte") == "sim" for a in afirmacoes)
    artigos = "\n".join(enviado["artigos"].values())
    contagem = {"sim": 0, "nao": 0, "fora_da_base": 0}
    for n, afirmacao in enumerate(afirmacoes, start=1):
        suporte = afirmacao.get("suporte")
        if suporte not in SUPORTES:
            invalidas.append(f"{codigo}: afirmação {n} com suporte inválido '{suporte}'")
            suporte = "nao"
        elif not _contido(afirmacao.get("afirmacao"), enviado["resposta"]):
            invalidas.append(f"{codigo}: afirmação {n} não existe na resposta enviada")
            suporte = "nao" if suporte == "sim" else suporte
        elif suporte == "sim" and not _contido(afirmacao.get("trecho_artigo"), artigos):
            invalidas.append(f"{codigo}: trecho do artigo da afirmação {n} não existe nos artigos enviados")
            suporte = "nao"
        contagem[suporte] += 1
    return contagem, aprovada


def _conferir_arquivo(nome: str, pasta: Path, enviados: dict, versoes: dict, registro: dict) -> tuple[dict, dict]:
    """Situação do retorno de um arquivo e a correção de cada código aceito."""
    situacao = {"aceito": False, "problemas": [], "faltando": [], "marcacoes_invalidas": [], "erradas_aprovadas": []}
    meta = registro.get(nome) or {}
    situacao["modelo"], situacao["data"] = meta.get("modelo"), str(meta.get("data") or "") or None
    for campo in ("modelo", "data"):
        if not situacao[campo]:
            situacao["problemas"].append(f"retornos/registro.yaml não traz '{campo}' de {nome}")

    caminho = pasta / f"{nome}.json"
    if not caminho.is_file():
        situacao["problemas"].append(f"falta {caminho.name}")
        return situacao, {}
    try:
        itens = _ler_json(caminho)
    except ValueError as erro:  # json.JSONDecodeError também é ValueError
        situacao["problemas"].append(f"{caminho.name} não é um JSON válido: {erro}")
        return situacao, {}

    recebidos: dict[str, dict] = {}
    for item in itens:
        codigo = str(item.get("codigo"))
        if codigo not in enviados:
            situacao["problemas"].append(f"código desconhecido no retorno: {codigo}")
        elif codigo in recebidos:
            situacao["problemas"].append(f"código repetido no retorno: {codigo}")
        else:
            recebidos[codigo] = item
    situacao["faltando"] = [c for c in enviados if c not in recebidos]
    if situacao["faltando"]:
        situacao["problemas"].append(f"faltam {len(situacao['faltando'])} linhas")

    tipo = nome.split("-")[1]
    correcoes = {}
    for codigo, item in recebidos.items():
        corrigir = _corrigir_precisao if tipo == "precisao" else _corrigir_fidelidade
        correcao, aprovada = corrigir(item, enviados[codigo], codigo, situacao["marcacoes_invalidas"])
        if versoes[codigo] == "errada":
            if aprovada:
                situacao["erradas_aprovadas"].append(codigo)
        else:
            correcoes[codigo] = correcao
    if situacao["erradas_aprovadas"]:
        situacao["problemas"].append("o corretor aprovou resposta errada de propósito: mude a rubrica ou o modelo")
    situacao["aceito"] = not situacao["problemas"]
    return situacao, correcoes if situacao["aceito"] else {}


def _percentual(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def conferir(pasta_rodada: Path) -> dict:
    """Confere os quatro retornos, calcula as métricas por versão e grava resultado.yaml."""
    pasta = pasta_rodada / "retornos"
    if not pasta.is_dir() or not any(pasta.glob("*.json")):
        raise ErroConferencia(f"Nenhum retorno em {pasta}: salve ali o JSON devolvido em cada envio.")
    conteudo = _ler(pasta_rodada / "envios" / "conteudo.yaml")
    mapa = _ler(pasta_rodada / "mapa.yaml")
    versoes = {i["codigo"]: i["versao"] for itens in mapa["arquivos"].values() for i in itens}
    registro_retornos = pasta / "registro.yaml"
    registro = (_ler(registro_retornos) or {}) if registro_retornos.is_file() else {}

    arquivos, correcoes = {}, {}
    for arquivo in ARQUIVOS:
        for tipo in TIPOS:
            nome = f"{arquivo}-{tipo}"
            arquivos[nome], correcoes[nome] = _conferir_arquivo(nome, pasta, conteudo[arquivo], versoes, registro)

    metricas = {}
    for versao in VERSOES:
        codigos = [(a, c) for a in ARQUIVOS for c in conteudo[a] if versoes[c] == versao]
        recusa = {c: conteudo[a][c]["resposta"].strip() == RECUSA for a, c in codigos}
        citada = {c: bool(extrair_referencias(conteudo[a][c]["resposta"], list(LEIS_JURIDICAS))) for a, c in codigos}
        precisao = {c: certa for a, c in codigos if (certa := correcoes[f"{a}-precisao"].get(c)) is not None}
        certas = sum(certa and not recusa[c] for c, certa in precisao.items())
        fidelidade = [contagem for a, c in codigos if (contagem := correcoes[f"{a}-fidelidade"].get(c))]
        com, sem = sum(f["sim"] for f in fidelidade), sum(f["nao"] for f in fidelidade)
        metricas[versao] = {
            "precisao": {
                "corrigidas": len(precisao),
                "certas": certas,
                "recusas": sum(recusa[c] for c in precisao),
                "percentual": _percentual(certas, len(precisao)),
            },
            "fidelidade": {
                "respostas": len(fidelidade),
                "afirmacoes": com + sem,
                "sem_suporte": sem,
                "percentual_sem_suporte": _percentual(sem, com + sem),
                "fora_da_base": sum(f["fora_da_base"] for f in fidelidade),
                "respostas_com_citacao_fora_da_base": sum(
                    bool(conteudo[a][c]["fora_da_base"]) for a, c in codigos
                ),
            },
            "recusas": sum(recusa.values()),
            "citacao": {
                "respostas": len(codigos),
                "com_citacao": sum(citada.values()),
                "percentual": _percentual(sum(citada.values()), len(codigos)),
            },
        }

    resultado = {"rodada": pasta_rodada.name, "arquivos": arquivos, "versoes": metricas}
    (pasta_rodada / "resultado.yaml").write_text(
        yaml.safe_dump(resultado, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8"
    )
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rodada", type=Path, help="pasta da rodada em avaliacao/rodadas/")
    args = parser.parse_args()
    try:
        resultado = conferir(args.rodada)
    except ErroConferencia as erro:
        print(erro)
        return 1
    for nome, situacao in resultado["arquivos"].items():
        print(f"{nome}: {'aceito' if situacao['aceito'] else 'NÃO ACEITO'}")
        for linha in situacao["problemas"] + situacao["marcacoes_invalidas"]:
            print(f"  - {linha}")
    for versao, m in resultado["versoes"].items():
        print(
            f"{versao}: precisão {m['precisao']['certas']}/{m['precisao']['corrigidas']}, "
            f"sem suporte {m['fidelidade']['sem_suporte']}/{m['fidelidade']['afirmacoes']}, "
            f"recusas {m['recusas']}, com citação {m['citacao']['com_citacao']}/{m['citacao']['respostas']}"
        )
    print(f"Resultado em {args.rodada / 'resultado.yaml'}")
    return 0 if all(s["aceito"] for s in resultado["arquivos"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
