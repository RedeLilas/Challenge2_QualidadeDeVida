"""Consulta o índice para conferir a recuperação, sem LLM.

O número entre colchetes é a similaridade de cosseno: quanto maior, mais parecido.

Uso: uv run python -m app.rag.buscar "ele quebrou minhas coisas, isso é violência?" [-k 5] [--eixo juridico]
"""
import argparse

from app.rag.indice import Indice, carregar_trechos
from app.rag.ingestao import EIXOS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pergunta")
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument(
        "--eixo", action="append", choices=sorted(EIXOS), help="filtra por eixo; pode repetir; padrão: todos"
    )
    args = parser.parse_args()

    indice = Indice(carregar_trechos())
    for trecho, similaridade in indice.buscar(args.pergunta, args.k, set(args.eixo) if args.eixo else None):
        print(f"[{similaridade:.3f}] {trecho['citacao']}  ({trecho['url']})")
        print(f"    {trecho['texto'][:200]}\n")


if __name__ == "__main__":
    main()
