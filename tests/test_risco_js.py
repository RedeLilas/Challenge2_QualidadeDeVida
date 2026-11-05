"""A PWA (web/risco.js) e o servidor (app/risco.py) dão o mesmo resultado (s2-alerta-risco-190, 2.2).

Roda o JavaScript de verdade no QuickJS, com o mesmo arquivo de regras.
"""
import json
from pathlib import Path

import pytest
import quickjs
import yaml

from app import risco

RAIZ = Path(__file__).resolve().parents[1]
CASOS = yaml.safe_load((Path(__file__).parent / "casos_risco.yaml").read_text(encoding="utf-8"))
FRASES = [c["frase"] for c in CASOS["risco"]] + CASOS["nao_risco"]
DIFICEIS = [
    "  ELE ESTÁ\n aqui   com uma FACA!  ",
    "ameaçou, pescoço, bebê, ÇÃO",
    "tabulação\taqui",
    "1º e 2ª vez",
    "Ele vai me MATÁ",
    "emoji 😢 no meio",
]


@pytest.fixture(scope="module")
def js():
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "risco.js").read_text(encoding="utf-8"))
    regras = (RAIZ / "regras" / "risco_imediato.json").read_text(encoding="utf-8")
    contexto.eval(f"var REGRAS = Risco.compilar({regras});")
    return contexto


@pytest.mark.parametrize("texto", DIFICEIS + FRASES[:10])
def test_normalizacao_igual(js, texto):
    assert js.eval(f"Risco.normalizar({json.dumps(texto)})") == risco.normalizar(texto)


@pytest.mark.parametrize("frase", FRASES)
def test_avaliacao_igual(js, frase):
    resultado_js = json.loads(js.eval(f"JSON.stringify(Risco.avaliar(REGRAS, {json.dumps(frase)}))"))
    assert resultado_js == risco.avaliar(frase)


@pytest.mark.parametrize("caso", CASOS["risco"], ids=lambda c: c["frase"][:40])
def test_pwa_sem_falso_negativo(js, caso):
    assert js.eval(f"Risco.avaliar(REGRAS, {json.dumps(caso['frase'])}) !== null")
