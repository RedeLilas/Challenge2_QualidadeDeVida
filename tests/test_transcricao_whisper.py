"""Whisper de verdade sobre os casos fictícios de áudio (s5-entrada-audio, tarefa 1.3).

Marca `whisper`: fica fora da suíte padrão, porque baixa o modelo (~0,5 GB) na primeira vez.
Rodar com `uv run pytest -m whisper`. Os áudios são de voz sintética offline (tests/audios/LEIAME.md).
"""
import re
from pathlib import Path

import pytest
import yaml

from app import risco, transcricao

pytestmark = pytest.mark.whisper

PASTA = Path(__file__).parent / "audios"
CASOS = yaml.safe_load((PASTA / "casos_audio.yaml").read_text(encoding="utf-8"))["casos"]
TIPOS = {"webm": "audio/webm;codecs=opus", "mp4": "audio/mp4"}


@pytest.fixture(scope="module")
def whisper():
    return transcricao.carregar()


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_transcricao_dos_casos(whisper, caso):
    texto = whisper.transcrever((PASTA / caso["arquivo"]).read_bytes(), TIPOS[caso["formato"]])
    if not caso["palavras_chave"]:  # A7: só silêncio
        assert texto == ""
        return
    normalizado = risco.normalizar(texto)
    for palavra in caso["palavras_chave"]:
        assert re.search(rf"\b{re.escape(palavra)}\b", normalizado), (palavra, texto)
    # A regra de risco sobre o texto transcrito dá o mesmo resultado que sobre o texto lido.
    assert bool(risco.avaliar(texto)) is caso["risco_esperado"], texto
