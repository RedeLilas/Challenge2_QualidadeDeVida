#!/usr/bin/env python3
"""Rodada da comparação LLM x RAG da S3: as duas versões, no mesmo dia, com o mesmo modelo.

Congelar o conjunto oficial (grava o SHA-256 de oficial.yaml):
    uv run python -m scripts.rodada congelar

Rodar (a chave do DeepSeek fica só no .env local; use apenas perguntas fictícias):
    uv run --env-file .env python -m scripts.rodada rodar desenvolvimento --changelog "<versão>"
    uv run --env-file .env python -m scripts.rodada rodar oficial --changelog "<versão>"

A rodada oficial só executa se oficial.yaml tiver o mesmo hash do congelamento. Cada rodada
grava avaliacao/rodadas/<data>-<conjunto>/registro.yaml e respostas.yaml, sem sobrescrever
rodadas anteriores.
"""
from __future__ import annotations

import argparse
import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import yaml

from app import config, llm
from app.rag import resposta
from scripts.validar_conjuntos import PASTA_CONJUNTOS, RAIZ, validar_conjunto

PASTA_RODADAS = RAIZ / "avaliacao" / "rodadas"
ARQUIVO_CONGELAMENTO = "oficial.congelamento.yaml"
TIPOS = ("desenvolvimento", "oficial")


class ErroRodada(RuntimeError):
    """A rodada ou o congelamento não pode seguir; nada foi gravado nem enviado ao LLM."""


def _agora() -> datetime:
    return datetime.now().astimezone()


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _ler(caminho: Path):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def _gravar(caminho: Path, dados) -> None:
    caminho.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8"
    )


def _validar(caminho: Path, tipo: str) -> None:
    if erros := validar_conjunto(caminho, tipo):
        raise ErroRodada("Conjunto inválido; corrija antes de seguir:\n" + "\n".join(erros))


def congelar(pasta_conjuntos: Path = PASTA_CONJUNTOS, agora: Callable[[], datetime] = _agora) -> Path:
    """Valida oficial.yaml e grava o hash dele. Um novo congelamento substitui o anterior."""
    arquivo = pasta_conjuntos / "oficial.yaml"
    _validar(arquivo, "oficial")
    destino = pasta_conjuntos / ARQUIVO_CONGELAMENTO
    _gravar(destino, {"arquivo": arquivo.name, "sha256": _sha256(arquivo), "data": agora().isoformat()})
    return destino


def _conferir_congelamento(pasta_conjuntos: Path, sha256: str) -> dict:
    registro = pasta_conjuntos / ARQUIVO_CONGELAMENTO
    if not registro.is_file():
        raise ErroRodada("O conjunto oficial ainda não foi congelado: rode `python -m scripts.rodada congelar`.")
    congelamento = _ler(registro)
    if congelamento.get("sha256") != sha256:
        raise ErroRodada(
            "oficial.yaml diverge do congelamento. A rodada oficial não executa até um novo congelamento, "
            "e a nova rodada precisa ser declarada no relatório."
        )
    return congelamento


def _nova_pasta(pasta_rodadas: Path, nome: str) -> Path:
    destino, n = pasta_rodadas / nome, 1
    while destino.exists():
        n += 1
        destino = pasta_rodadas / f"{nome}-{n}"
    destino.mkdir(parents=True)
    return destino


def _responder(item: dict, tipo: str, indice, cliente) -> dict:
    com_rag = resposta.responder(item["pergunta"], indice, cliente)
    sem_rag = cliente.responder(resposta.montar_mensagens_sem_rag(item["pergunta"]))
    return {
        "id": item["id"],
        "tipo": tipo,
        "categoria": item["categoria"],
        "pergunta": item["pergunta"],
        "rag": {
            "resposta": com_rag["resposta"],
            "recusada": com_rag["recusada"],
            "citacoes": [c["citacao"] for c in com_rag["citacoes"]],
        },
        "sem_rag": {"resposta": sem_rag},
    }


def rodar(
    tipo: str,
    *,
    cliente,
    indice,
    changelog: str,
    raciocinio: str | None = None,
    pasta_conjuntos: Path = PASTA_CONJUNTOS,
    pasta_rodadas: Path = PASTA_RODADAS,
    agora: Callable[[], datetime] = _agora,
) -> Path:
    """Gera as respostas das duas versões para todo o conjunto e devolve a pasta da rodada."""
    if tipo not in TIPOS:
        raise ValueError(f"Conjunto desconhecido: {tipo}")
    if not changelog.strip():
        raise ErroRodada("Informe a versão do changelog do modelo (--changelog).")
    arquivo = pasta_conjuntos / f"{tipo}.yaml"
    _validar(arquivo, tipo)
    sha256 = _sha256(arquivo)
    congelamento = _conferir_congelamento(pasta_conjuntos, sha256) if tipo == "oficial" else None
    conjunto = _ler(arquivo)

    inicio = agora()
    # Pergunta a pergunta, as duas versões em seguida: o mesmo modelo, no mesmo dia.
    # Se o provedor falhar, a exceção interrompe a rodada antes de gravar qualquer arquivo.
    respostas = [_responder(item, "pergunta", indice, cliente) for item in conjunto["perguntas"]]
    respostas += [_responder(item, "extra", indice, cliente) for item in conjunto["extras"]]
    fim = agora()

    registro = {
        "conjunto": tipo,
        "arquivo": arquivo.name,
        "sha256": sha256,
        **({"congelamento": congelamento} if congelamento else {}),
        "modelo": cliente.modelo,
        "raciocinio": raciocinio,
        "changelog": changelog.strip(),
        "data": inicio.date().isoformat(),
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "instrucoes": {"rag": resposta.INSTRUCOES, "sem_rag": resposta.INSTRUCOES_SEM_RAG},
        "rag": {"k": resposta.K, "limite_similaridade": resposta.LIMITE_SIMILARIDADE},
        "total": {"perguntas": len(conjunto["perguntas"]), "extras": len(conjunto["extras"])},
    }
    destino = _nova_pasta(pasta_rodadas, f"{registro['data']}-{tipo}")
    _gravar(destino / "registro.yaml", registro)
    _gravar(destino / "respostas.yaml", respostas)
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser("congelar", help="valida oficial.yaml e grava o hash dele")
    rodada = comandos.add_parser("rodar", help="gera as respostas das duas versões")
    rodada.add_argument("tipo", choices=TIPOS)
    rodada.add_argument("--changelog", required=True, help="versão do changelog do modelo no dia da rodada")
    args = parser.parse_args()

    try:
        if args.comando == "congelar":
            print(f"Congelado: {congelar()}")
            return 0
        # Import tardio: o modelo de embeddings (torch) só carrega na rodada.
        from app.rag.indice import indice_padrao

        cfg = config.carregar()
        pasta = rodar(
            args.tipo,
            cliente=llm.ClienteLLM(cfg),
            indice=indice_padrao(),
            changelog=args.changelog,
            raciocinio=cfg.thinking,
        )
    except (ErroRodada, config.ConfigIncompleta, llm.LLMIndisponivel) as erro:
        print(erro)
        return 1
    print(f"Rodada gravada em {pasta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
