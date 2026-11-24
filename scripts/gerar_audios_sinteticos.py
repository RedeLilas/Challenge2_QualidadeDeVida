#!/usr/bin/env python3
"""Gera os casos fictícios de áudio A1 a A7 (s5-entrada-audio, tarefa 1.2) com voz sintética offline.

Lê tests/audios/casos_audio.yaml e grava cada arquivo no formato pedido:
- webm/opus, como grava o Chrome no Android (MediaRecorder "audio/webm;codecs=opus"), com o PyAV;
- mp4/aac, como grava o Safari no iPhone (MediaRecorder "audio/mp4"), com o afconvert do macOS.

A voz é a do sintetizador do macOS (`say`), sem internet e sem voz de ninguém da equipe. Casos com
texto vazio (A7) viram silêncio com a duração pedida. O A8 (arquivo corrompido e acima do limite)
é gerado pelo próprio teste e não fica no repositório.

Uso (só no macOS): uv run python scripts/gerar_audios_sinteticos.py [--voz Luciana]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import av
import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "tests" / "audios"
CASOS = PASTA / "casos_audio.yaml"
TAXA_AIFF = 22050


def falar(texto: str, voz: str, destino: Path) -> None:
    subprocess.run(["say", "-v", voz, "-o", str(destino), texto], check=True)


def silencio(segundos: float, destino: Path) -> None:
    saida = av.open(str(destino), "w", format="aiff")
    estrutura = saida.add_stream("pcm_s16be", rate=TAXA_AIFF, layout="mono")
    amostras = int(segundos * TAXA_AIFF)
    quadro = av.AudioFrame(format="s16", layout="mono", samples=amostras)
    quadro.planes[0].update(bytes(amostras * 2))
    quadro.sample_rate = TAXA_AIFF
    for pacote in estrutura.encode(quadro):
        saida.mux(pacote)
    for pacote in estrutura.encode(None):
        saida.mux(pacote)
    saida.close()


def para_webm(origem: Path, destino: Path) -> None:
    entrada = av.open(str(origem))
    saida = av.open(str(destino), "w", format="webm")
    estrutura = saida.add_stream("libopus", rate=48000, layout="mono")
    conversor = av.AudioResampler(format="s16", layout="mono", rate=48000)
    for quadro in entrada.decode(audio=0):
        for convertido in conversor.resample(quadro):
            for pacote in estrutura.encode(convertido):
                saida.mux(pacote)
    for convertido in conversor.resample(None):
        for pacote in estrutura.encode(convertido):
            saida.mux(pacote)
    for pacote in estrutura.encode(None):
        saida.mux(pacote)
    saida.close()
    entrada.close()


def para_mp4(origem: Path, destino: Path) -> None:
    subprocess.run(["afconvert", "-f", "mp4f", "-d", "aac", "-b", "64000", str(origem), str(destino)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voz", default="Luciana", help="voz do `say` em pt_BR (padrão: Luciana)")
    args = parser.parse_args()
    if sys.platform != "darwin":
        sys.exit("Este script usa o `say` e o `afconvert` do macOS.")

    casos = yaml.safe_load(CASOS.read_text(encoding="utf-8"))["casos"]
    with tempfile.TemporaryDirectory() as pasta_temp:
        for caso in casos:
            bruto = Path(pasta_temp) / f"{caso['id']}.aiff"
            if caso["texto"]:
                falar(caso["texto"], args.voz, bruto)
            else:
                silencio(caso["duracao_silencio_s"], bruto)
            destino = PASTA / caso["arquivo"]
            (para_webm if caso["formato"] == "webm" else para_mp4)(bruto, destino)
            print(f"{caso['id']}: {destino.relative_to(RAIZ)} ({destino.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
