"""Índice de embeddings em memória sobre os trechos de dados/leis/.

O DeepSeek não oferece embeddings, então o modelo roda localmente, inclusive no deploy.
O multilingual-e5 exige os prefixos "query: " na pergunta e "passage: " no trecho.
"""
import json
from functools import cache
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODELO = "intfloat/multilingual-e5-base"
PASTA_LEIS = Path(__file__).resolve().parents[2] / "dados" / "leis"


@cache
def _modelo() -> SentenceTransformer:
    return SentenceTransformer(MODELO)


def _vetores(textos: list[str]) -> np.ndarray:
    return _modelo().encode(textos, normalize_embeddings=True, convert_to_numpy=True)


def carregar_trechos(pasta: Path = PASTA_LEIS) -> list[dict]:
    trechos = []
    for arquivo in sorted(pasta.glob("*.jsonl")):
        with arquivo.open(encoding="utf-8") as f:
            trechos += [json.loads(linha) for linha in f]
    return trechos


class Indice:
    def __init__(self, trechos: list[dict]):
        self.trechos = trechos
        # O capítulo dá contexto a incisos curtos ("I - pela autoridade judicial;").
        self.matriz = _vetores(
            [f"passage: {t['citacao']}\n{t['capitulo']}\n{t['texto']}" for t in trechos]
        )

    def buscar(self, pergunta: str, k: int = 5) -> list[tuple[dict, float]]:
        # Vetores normalizados: o produto interno é a similaridade de cosseno.
        similaridades = self.matriz @ _vetores([f"query: {pergunta}"])[0]
        melhores = np.argsort(-similaridades)[:k]
        return [(self.trechos[i], float(similaridades[i])) for i in melhores]
