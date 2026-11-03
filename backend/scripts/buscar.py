"""Consulta o índice para conferir a recuperação, sem LLM.

Uso: python scripts/buscar.py "ele quebrou minhas coisas, isso é violência?" [-k 5]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag import indice  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pergunta")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    for r in indice.buscar(args.pergunta, args.k):
        print(f"[{r['distancia']:.3f}] {r['citacao']}  ({r['url_fonte']})")
        print(f"    {r['texto'][:200]}\n")


if __name__ == "__main__":
    main()
