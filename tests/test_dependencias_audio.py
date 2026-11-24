"""O faster-whisper consegue decodificar os formatos do navegador com o PyAV do lock (s5-entrada-audio).

Com o av 19, `faster_whisper.decode_audio` quebrava com `TypeError: open() got an unexpected
keyword argument 'metadata_errors'`, e a verificação da tarefa 1.1 (#121) só tinha testado o import.
Este teste decodifica de verdade, em memória e sem o modelo: 1 s de tom gerado aqui, sem voz.
"""
import io

import av
import numpy as np
import pytest
from faster_whisper.audio import decode_audio

TAXA = 48_000


def tom(formato: str, codec: str) -> io.BytesIO:
    """1 s de tom de 440 Hz no formato pedido, gerado em memória."""
    saida = io.BytesIO()
    with av.open(saida, "w", format=formato) as container:
        stream = container.add_stream(codec, rate=TAXA)
        stream.layout = "mono"
        amostras = (0.2 * np.sin(2 * np.pi * 440 * np.arange(TAXA) / TAXA)).astype(np.float32)
        quadro = av.AudioFrame.from_ndarray(amostras.reshape(1, -1), format="flt", layout="mono")
        quadro.rate = TAXA
        for pacote in stream.encode(quadro):
            container.mux(pacote)
        for pacote in stream.encode(None):
            container.mux(pacote)
    saida.seek(0)
    return saida


@pytest.mark.parametrize(
    "formato, codec",
    [
        ("webm", "libopus"),  # MediaRecorder do Chrome/Android
        ("mp4", "aac"),  # MediaRecorder do Safari/iPhone
    ],
)
def test_faster_whisper_decodifica_em_memoria(formato, codec):
    audio = decode_audio(tom(formato, codec))  # 16 kHz, mono, float32
    assert audio.dtype == np.float32
    assert 0.9 * 16_000 <= len(audio) <= 1.1 * 16_000
    assert np.abs(audio).max() > 0.05  # o tom chegou, não só silêncio
