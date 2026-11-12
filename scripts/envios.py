#!/usr/bin/env python3
"""Prepara os quatro envios ao corretor externo a partir de uma rodada (scripts/rodada.py).

    uv run python -m scripts.envios avaliacao/rodadas/<rodada> [--semente N]

Gera, dentro da pasta da rodada:
- envios/A-precisao.txt, A-fidelidade.txt, B-precisao.txt e B-fidelidade.txt: o que é colado
  no corretor. Cada pergunta do tema tem uma versão sorteada para A e a outra para B, com
  códigos neutros, ordem sorteada e 3 respostas erradas de propósito (uma perto do final).
- envios/conteudo.yaml: o texto enviado em cada código, para conferir o retorno.
- mapa.yaml: semente e versão de cada código. Nunca é enviado ao corretor.

As respostas erradas de propósito são escritas pela equipe em avaliacao/conjuntos/erradas.yaml,
a partir de perguntas de desenvolvimento, para não alterar o conjunto oficial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path

import yaml

from app.rag.resposta import extrair_referencias, rotulo
from app.rag.versoes import PROCESSADOS
from scripts.validar_conjuntos import PASTA_CONJUNTOS

ARQUIVO_ERRADAS = "erradas.yaml"
TOTAL_ERRADAS = 3
# A última errada entra entre as POSICOES_FINAIS últimas linhas, para pegar um corretor que
# afrouxa no fim de uma conversa longa.
POSICOES_FINAIS = 2
ARQUIVOS = ("A", "B")
VERSOES = ("rag", "sem_rag")


class ErroEnvio(RuntimeError):
    """Os envios não podem ser preparados; nada foi gravado."""


def _ler(caminho: Path):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def _gravar(caminho: Path, dados) -> None:
    caminho.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")


def _texto(valor) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def artigos_da_base(pasta: Path = PROCESSADOS) -> dict[tuple[str, str], str]:
    """Texto integral de cada artigo, da coleta mais recente de cada norma: {(lei, ARTIGO): texto}."""
    artigos: dict[tuple[str, str], list[str]] = {}
    for norma in sorted(p for p in pasta.iterdir() if p.is_dir()):
        coletas = sorted(norma.glob("*.jsonl"))
        if not coletas:
            continue
        with coletas[-1].open(encoding="utf-8") as f:
            for registro in map(json.loads, f):
                lei = registro["citacao"].rsplit(", art.", 1)[0]
                artigos.setdefault((lei, registro["artigo"].upper()), []).append(registro["texto"])
    return {chave: "\n".join(textos) for chave, textos in artigos.items()}


def _citados(texto: str, base: dict[tuple[str, str], str]) -> tuple[dict[str, str], list[str]]:
    """Artigos citados na resposta: os da base com o texto integral, e os de fora à parte."""
    artigos, fora = {}, []
    leis = sorted({lei for lei, _ in base})
    # Sem o ponto: o LLM pode escrever "art. 1584" para o art. 1.584 guardado na base.
    por_numero = {(lei, artigo.replace(".", "")): (lei, artigo) for lei, artigo in base}
    for lei, artigo in dict.fromkeys(extrair_referencias(texto, leis)):
        # A Lei 14.713/2023 vale para o Código Civil e para o CPC: lei vem como a tupla dos dois.
        candidatas = lei if isinstance(lei, tuple) else (lei,)
        numero = artigo.replace(".", "")
        chave = next((por_numero[c, numero] for c in candidatas if (c, numero) in por_numero), None)
        if lei is not None and chave:
            artigos[rotulo(*chave)] = base[chave]
        else:
            nome = " ou ".join(candidatas) if lei else None
            rotulo_fora = rotulo(nome, artigo) if nome else f"art. {artigo} (norma não identificada)"
            if rotulo_fora not in fora:
                fora.append(rotulo_fora)
    return artigos, fora


def _erradas(pasta_conjuntos: Path, perguntas_dev: dict[str, dict]) -> list[dict]:
    caminho = pasta_conjuntos / ARQUIVO_ERRADAS
    if not caminho.is_file():
        raise ErroEnvio(f"Falta {caminho}, com as {TOTAL_ERRADAS} respostas erradas de propósito.")
    erradas = (_ler(caminho) or {}).get("erradas")
    if not isinstance(erradas, list) or len(erradas) != TOTAL_ERRADAS:
        raise ErroEnvio(f"{caminho}: são necessárias {TOTAL_ERRADAS} respostas erradas de propósito.")
    erros = []
    for n, item in enumerate(erradas, start=1):
        if not isinstance(item, dict):
            erros.append(f"{caminho}:erradas[{n}]: registro deve ser um objeto")
            continue
        for campo in ("id", "pergunta_id", "autor", "resposta"):
            if not _texto(item.get(campo)):
                erros.append(f"{caminho}:erradas[{n}]: campo '{campo}' obrigatório e não vazio")
        if _texto(item.get("pergunta_id")) and item["pergunta_id"] not in perguntas_dev:
            erros.append(f"{caminho}:erradas[{n}]: pergunta '{item['pergunta_id']}' não está no desenvolvimento")
    if erros:
        raise ErroEnvio("\n".join(erros))
    return erradas


def _ordem(rng: random.Random, perguntas: list[tuple[str, str]], erradas: list[str]) -> list[tuple[str, str]]:
    """Perguntas e erradas embaralhadas, com a última errada entre as linhas finais."""
    itens = perguntas + [(e, "errada") for e in erradas[:-1]]
    rng.shuffle(itens)
    itens.insert(rng.randint(len(itens) - POSICOES_FINAIS + 1, len(itens)), (erradas[-1], "errada"))
    return itens


def _bloco_precisao(codigo: str, item: dict) -> str:
    pontos = "\n".join(f"{n}. {p}" for n, p in enumerate(item["pontos_obrigatorios"], start=1))
    return (
        f"=== {codigo} ===\nPERGUNTA:\n{item['pergunta']}\n\nGABARITO:\n{item['resposta_esperada']}\n\n"
        f"PONTOS OBRIGATÓRIOS:\n{pontos}\n\nRESPOSTA:\n{item['resposta']}\n"
    )


def _bloco_fidelidade(codigo: str, item: dict) -> str:
    artigos = "\n\n".join(f"[{r}]\n{t}" for r, t in item["artigos"].items()) or "(nenhum)"
    fora = "\n".join(f"- {r}" for r in item["fora_da_base"]) or "(nenhuma)"
    return (
        f"=== {codigo} ===\nRESPOSTA:\n{item['resposta']}\n\n"
        f"ARTIGOS CITADOS (texto integral):\n{artigos}\n\nCITAÇÕES FORA DA BASE:\n{fora}\n"
    )


def preparar(
    pasta_rodada: Path,
    *,
    semente: int,
    pasta_conjuntos: Path = PASTA_CONJUNTOS,
    pasta_dispositivos: Path = PROCESSADOS,
) -> Path:
    """Gera os quatro envios, o conteúdo por código e o mapa; devolve a pasta dos envios."""
    envios, arquivo_mapa = pasta_rodada / "envios", pasta_rodada / "mapa.yaml"
    if arquivo_mapa.exists() or (envios.exists() and any(envios.iterdir())):
        raise ErroEnvio(f"Os envios de {pasta_rodada.name} já foram preparados; um novo sorteio mudaria o mapa.")

    registro = _ler(pasta_rodada / "registro.yaml")
    arquivo_conjunto = pasta_conjuntos / registro["arquivo"]
    if hashlib.sha256(arquivo_conjunto.read_bytes()).hexdigest() != registro["sha256"]:
        raise ErroEnvio(f"{arquivo_conjunto.name} mudou depois da rodada; o gabarito não é o da rodada.")

    gabaritos = {p["id"]: p for p in _ler(arquivo_conjunto)["perguntas"]}
    perguntas_dev = {p["id"]: p for p in _ler(pasta_conjuntos / "desenvolvimento.yaml")["perguntas"]}
    erradas = {e["id"]: e for e in _erradas(pasta_conjuntos, perguntas_dev)}
    respostas = {r["id"]: r for r in _ler(pasta_rodada / "respostas.yaml") if r["tipo"] == "pergunta"}
    base = artigos_da_base(pasta_dispositivos)

    rng = random.Random(semente)
    # Cada pergunta: uma versão sorteada para A, a outra para B.
    sorteio = {q: rng.choice([VERSOES, VERSOES[::-1]]) for q in respostas}
    mapa = {"semente": semente, "rodada": pasta_rodada.name, "arquivos": {}}
    conteudo, textos = {}, {}
    for n, arquivo in enumerate(ARQUIVOS):
        perguntas = [(q, sorteio[q][n]) for q in respostas]
        ordem_erradas = list(erradas)
        rng.shuffle(ordem_erradas)
        mapa["arquivos"][arquivo], conteudo[arquivo] = [], {}
        for posicao, (ident, versao) in enumerate(_ordem(rng, perguntas, ordem_erradas), start=1):
            codigo = f"{arquivo}{posicao:02d}"
            if versao == "errada":
                gabarito, texto = perguntas_dev[erradas[ident]["pergunta_id"]], erradas[ident]["resposta"]
            else:
                gabarito, texto = gabaritos[ident], respostas[ident][versao]["resposta"]
            artigos, fora = _citados(texto, base)
            conteudo[arquivo][codigo] = {
                "pergunta": gabarito["pergunta"],
                "resposta_esperada": gabarito["resposta_esperada"],
                "pontos_obrigatorios": list(gabarito["pontos_obrigatorios"]),
                "resposta": texto,
                "artigos": artigos,
                "fora_da_base": fora,
            }
            mapa["arquivos"][arquivo].append({"codigo": codigo, "id": ident, "versao": versao})
        itens = conteudo[arquivo].items()
        textos[f"{arquivo}-precisao.txt"] = "\n".join(_bloco_precisao(c, i) for c, i in itens)
        textos[f"{arquivo}-fidelidade.txt"] = "\n".join(_bloco_fidelidade(c, i) for c, i in itens)

    envios.mkdir(exist_ok=True)
    for nome, texto in textos.items():
        (envios / nome).write_text(texto, encoding="utf-8")
    _gravar(envios / "conteudo.yaml", conteudo)
    _gravar(arquivo_mapa, mapa)
    return envios


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rodada", type=Path, help="pasta da rodada em avaliacao/rodadas/")
    parser.add_argument("--semente", type=int, help="semente do sorteio (padrão: aleatória, registrada no mapa)")
    args = parser.parse_args()
    semente = args.semente if args.semente is not None else secrets.randbelow(2**32)
    try:
        envios = preparar(args.rodada, semente=semente)
    except ErroEnvio as erro:
        print(erro)
        return 1
    print(f"Envios em {envios} (semente {semente}). Não abra nem envie o mapa.yaml antes do fim da correção.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
