"""Índice de embeddings em memória sobre os trechos de dados/leis/.

O DeepSeek não oferece embeddings, então o modelo roda localmente, inclusive no deploy.
O multilingual-e5 exige os prefixos "query: " na pergunta e "passage: " no trecho.

Os vetores dos trechos podem vir prontos de um arquivo gerado no build (s5-deploy, tarefa 2.3):
    uv run python -m app.rag.indice
Eles só são usados se os trechos e o modelo forem os mesmos de quando o arquivo foi gerado;
senão, o índice é montado na hora, como antes.
"""
import hashlib
import json
import logging
import threading
import time
from functools import cache
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODELO = "intfloat/multilingual-e5-base"
RAIZ = Path(__file__).resolve().parents[2]
PASTA_LEIS = RAIZ / "dados" / "leis"
# Gerado no build e fora do git (.gitignore): nunca é gravado pela aplicação em execução.
ARQUIVO_VETORES = RAIZ / "dados" / "indice" / "vetores.npz"
# Frase fixa codificada ao gerar e ao carregar: se o modelo mudar, o vetor dela muda junto.
SENTINELA = "query: o que é violência patrimonial?"

logger = logging.getLogger("rede_lilas.indice")


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


def _passagens(trechos: list[dict]) -> list[str]:
    # O capítulo dá contexto a incisos curtos ("I - pela autoridade judicial;").
    return [f"passage: {t['citacao']}\n{t['capitulo']}\n{t['texto']}" for t in trechos]


def _resumo(passagens: list[str]) -> str:
    """Resumo do modelo e do texto exato que vira vetor: qualquer mudança nos trechos o altera."""
    conteudo = json.dumps([MODELO, passagens], ensure_ascii=False)
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _vetores_prontos(arquivo: Path | None, passagens: list[str]) -> np.ndarray | None:
    """A matriz do arquivo, se ele existir e bater com os trechos e com o modelo; senão, None."""
    if arquivo is None or not Path(arquivo).exists():
        return None
    with np.load(arquivo) as dados:
        if str(dados["resumo"]) != _resumo(passagens):
            return None
        if not np.allclose(dados["sentinela"], _vetores([SENTINELA])[0], atol=1e-4):
            return None
        return dados["matriz"]


class Indice:
    def __init__(self, trechos: list[dict], vetores: Path | None = None):
        self.trechos = trechos
        self.eixos = np.array([t["eixo"] for t in trechos])
        passagens = _passagens(trechos)
        self.resumo = _resumo(passagens)
        matriz = _vetores_prontos(vetores, passagens)
        self.origem = "arquivo" if matriz is not None else "calculado"
        self.matriz = matriz if matriz is not None else _vetores(passagens)

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
            inicio = time.monotonic()
            _indice = Indice(carregar_trechos(), vetores=ARQUIVO_VETORES)
            # Mede a partida a frio na plataforma (s5-deploy, tarefa 3.2): só a origem e o tempo.
            logger.info("índice pronto: origem=%s em %.1f s", _indice.origem, time.monotonic() - inicio)
        return _indice


def salvar_vetores(indice: Indice, arquivo: Path = ARQUIVO_VETORES) -> None:
    """Grava a matriz com o resumo dos trechos e a sentinela do modelo (só no build, nunca em execução)."""
    arquivo = Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    np.savez(arquivo, matriz=indice.matriz, resumo=indice.resumo, sentinela=_vetores([SENTINELA])[0])


if __name__ == "__main__":
    salvar_vetores(Indice(carregar_trechos()))
    print(f"Vetores gravados em {ARQUIVO_VETORES}")
