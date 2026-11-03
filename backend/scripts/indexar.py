"""Indexa no Chroma a última versão processada de cada norma (só dispositivos vigentes).

Rode depois de revisar o relatório de scripts/ingerir.py.

Uso: python scripts/indexar.py [--norma lei-11340-2006]
"""
import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestao import versoes  # noqa: E402
from app.rag import indice  # noqa: E402

FONTES = Path(__file__).resolve().parents[1] / "config" / "fontes.yaml"
LOTE = 32
METADADOS = [
    "norma_id", "urn", "norma", "citacao", "artigo", "tipo", "rotulo",
    "status", "titulo", "capitulo", "secao", "url_fonte", "data_coleta", "hash_conteudo",
]  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--norma")
    args = parser.parse_args()

    normas = yaml.safe_load(FONTES.read_text(encoding="utf-8"))["normas"]
    ids = [n["id"] for n in normas if not args.norma or n["id"] == args.norma]
    colecao = indice.colecao()

    for norma_id in ids:
        processadas = versoes.versoes_processadas(norma_id)
        if not processadas:
            print(f"{norma_id}: sem versão processada, rode scripts/ingerir.py antes.")
            continue
        registros = [r for r in versoes.carregar(processadas[-1]) if r["status"] == "vigente"]

        # Reconstrói a norma inteira para não deixar dispositivo removido no índice.
        colecao.delete(where={"norma_id": norma_id})
        for i in range(0, len(registros), LOTE):
            lote = registros[i : i + LOTE]
            colecao.add(
                ids=[f"{r['norma_id']}:{r['id']}" for r in lote],
                embeddings=indice.embeddings([indice.texto_para_embedding(r) for r in lote]),
                documents=[r["texto"] for r in lote],
                metadatas=[{**{k: r[k] for k in METADADOS}, "notas": "; ".join(r["notas"])} for r in lote],
            )
        print(f"{norma_id}: {len(registros)} dispositivos indexados de {processadas[-1].name}")


if __name__ == "__main__":
    main()
