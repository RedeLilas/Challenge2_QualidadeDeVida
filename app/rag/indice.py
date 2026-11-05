"""Índice de embeddings em memória sobre os trechos de dados/leis/.

O DeepSeek não oferece embeddings, então o modelo roda localmente, inclusive no deploy.
O multilingual-e5 exige os prefixos "query: " na pergunta e "passage: " no trecho.
"""
import json
import threading
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
        self.eixos = np.array([t["eixo"] for t in trechos])
        # O capítulo dá contexto a incisos curtos ("I - pela autoridade judicial;").
        self.matriz = _vetores(
            [f"passage: {t['citacao']}\n{t['capitulo']}\n{t['texto']}" for t in trechos]
        )

    def buscar(self, pergunta: str, k: int = 5, eixos: set[str] | None = None) -> list[tuple[dict, float]]:
        """Os k trechos mais similares; com `eixos`, só os desses temas (ex.: {"juridico"})."""
        candidatos = np.arange(len(self.trechos))
        if eixos is not None:
            desconhecidos = set(eixos) - set(self.eixos)
            if desconhecidos:
                raise ValueError(f"Eixo sem trechos no índice: {sorted(desconhecidos)}")
            candidatos = np.flatnonzero(np.isin(self.eixos, list(eixos)))
        # Vetores normalizados: o produto interno é a similaridade de cosseno.
        similaridades = self.matriz[candidatos] @ _vetores([f"query: {pergunta}"])[0]
        ordem = np.argsort(-similaridades)[:k]
        return [(self.trechos[candidatos[j]], float(similaridades[j])) for j in ordem]


_trava = threading.Lock()
_indice: Indice | None = None


def indice_padrao() -> Indice:
    """Índice de todas as normas de dados/leis/, montado uma única vez por processo."""
    global _indice
    # A trava garante uma só montagem quando o aquecimento e a primeira pergunta chegam juntos.
    with _trava:
        if _indice is None:
            _indice = Indice(carregar_trechos())
        return _indice
