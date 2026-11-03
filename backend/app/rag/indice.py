"""Embeddings via Ollama e índice vetorial no Chroma."""
import os
from pathlib import Path

import chromadb
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELO_EMBEDDING = os.getenv("EMBEDDING_MODEL", "bge-m3")
CAMINHO_CHROMA = Path(__file__).resolve().parents[2] / "data" / "chroma"
COLECAO = "leis"


def embeddings(textos: list[str]) -> list[list[float]]:
    resposta = requests.post(
        f"{OLLAMA_URL}/api/embed", json={"model": MODELO_EMBEDDING, "input": textos}, timeout=300
    )
    resposta.raise_for_status()
    return resposta.json()["embeddings"]


def colecao() -> chromadb.Collection:
    cliente = chromadb.PersistentClient(path=str(CAMINHO_CHROMA))
    return cliente.get_or_create_collection(
        COLECAO,
        metadata={"modelo_embedding": MODELO_EMBEDDING},
        configuration={"hnsw": {"space": "cosine"}},
    )


def texto_para_embedding(r: dict) -> str:
    # O caput e os dispositivos-pai dão sentido a incisos curtos como "I - pela autoridade judicial;".
    partes = [r["citacao"], r["capitulo"], r["contexto"], r["texto"]]
    return "\n".join(p for p in partes if p)


def buscar(pergunta: str, k: int = 5) -> list[dict]:
    resultado = colecao().query(query_embeddings=embeddings([pergunta]), n_results=k)
    return [
        {**meta, "texto": doc, "distancia": dist}
        for doc, meta, dist in zip(
            resultado["documents"][0], resultado["metadatas"][0], resultado["distances"][0]
        )
    ]
