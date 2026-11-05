"""Detecção de risco imediato por regra determinística, sem LLM (spec triagem-risco).

As regras ficam em regras/risco_imediato.json, o mesmo arquivo que a PWA usa offline
(web/risco.js). A normalização precisa ser idêntica nos dois lados: tests/test_risco_js.py
compara os resultados.
"""
import json
import re
import unicodedata
from functools import cache
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[1] / "regras" / "risco_imediato.json"

# Mesmo texto da tela de alerta da PWA (web/app.js), que também funciona sem conexão.
ALERTA = (
    "Você pode estar em perigo agora. Ligue 190 (Polícia Militar). "
    "Se a pessoa em perigo for outra, ligue 190 e informe o endereço dela. "
    "Para conversar com alguém, ligue 180 (gratuito, 24 horas)."
)

# Marcas de acento que a decomposição NFD separa da letra (mesma faixa usada no JavaScript).
ACENTOS = re.compile(r"[\u0300-\u036f]")
ESPACOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e com espaços colapsados."""
    sem_acento = ACENTOS.sub("", unicodedata.normalize("NFD", texto))
    return ESPACOS.sub(" ", sem_acento.lower()).strip()


@cache
def _regras() -> list[tuple[str, str, re.Pattern]]:
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    return [(r["id"], r["categoria"], re.compile(r["padrao"])) for r in dados["regras"]]


def avaliar(texto: str) -> dict | None:
    """A primeira regra que dispara ({"id", "categoria"}), ou None se não houver risco imediato."""
    normalizado = normalizar(texto)
    for id_, categoria, padrao in _regras():
        if padrao.search(normalizado):
            return {"id": id_, "categoria": categoria}
    return None
