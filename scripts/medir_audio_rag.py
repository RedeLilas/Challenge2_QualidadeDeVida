"""Mede memória e tempos do RAG com o Whisper carregados juntos (s5-entrada-audio, tarefa 5.1).

Entrada da decisão de plataforma da s5-deploy. Cada configuração roda num processo próprio, para o
pico de memória (ru_maxrss) não se misturar: todas as threads e 2 threads (como numa máquina de
2 vCPUs). O modelo de embeddings roda na CPU, como no deploy, mesmo num Mac com GPU (MPS).
Os modelos precisam estar no cache (rode a aplicação ou `uv run pytest -m whisper` uma vez antes):
a medição roda com HF_HUB_OFFLINE=1, sem download.

    uv run python scripts/medir_audio_rag.py            # as duas configurações e a tabela
    uv run python scripts/medir_audio_rag.py --threads 2  # só uma configuração (JSON)

Áudios: os casos fictícios de tests/audios/ (voz sintética), uma pergunta longa montada com A1 a A6 em sequência\ne a mesma pergunta com ruído forte, para medir as novas tentativas do Whisper em áudio difícil.
"""
import argparse
import io
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))  # o script roda de scripts/, e o pacote app/ fica na raiz
CASOS = ["a1.webm", "a2.mp4", "a3.webm", "a4.mp4", "a5.webm", "a6.mp4"]
TIPOS = {".webm": "audio/webm", ".mp4": "audio/mp4"}


def pico_mb() -> float:
    pico = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS informa em bytes; Linux, em KB.
    return pico / 2**20 if sys.platform == "darwin" else pico / 2**10


def _webm(sinal) -> bytes:
    import av

    saida = io.BytesIO()
    with av.open(saida, "w", format="webm") as container:
        stream = container.add_stream("libopus", rate=16_000)
        stream.layout = "mono"
        quadro = av.AudioFrame.from_ndarray(sinal.reshape(1, -1), format="flt", layout="mono")
        quadro.rate = 16_000
        for pacote in stream.encode(quadro):
            container.mux(pacote)
        for pacote in stream.encode(None):
            container.mux(pacote)
    return saida.getvalue()


def audios_longos() -> dict:
    """Pergunta longa (A1 a A6 em sequência, ~21 s, frases diferentes) e a mesma fala com ruído muito forte.

    Não use a mesma frase repetida: o Whisper descarta texto repetitivo como alucinação.
    """
    import numpy as np
    from faster_whisper.audio import decode_audio

    pausa = np.zeros(6_400, dtype=np.float32)
    fala = np.concatenate(
        [np.concatenate([decode_audio(str(RAIZ / "tests" / "audios" / n), sampling_rate=16_000), pausa]) for n in CASOS]
    ).astype(np.float32)
    ruido = np.random.default_rng(0).normal(0, 1, len(fala)).astype(np.float32)
    ruido *= np.sqrt(np.mean(fala**2) / 10 ** (-5 / 10))  # SNR de -5 dB: ruído mais forte que a voz
    return {"longo": _webm(fala), "longo_com_ruido": _webm(np.clip(fala + ruido, -1, 1).astype(np.float32)), "segundos": round(len(fala) / 16_000, 1)}


def medir(threads: int | None) -> dict:
    """Roda no processo filho: carrega o Whisper e o índice, transcreve e busca, e mede."""
    import torch

    if threads:
        torch.set_num_threads(threads)
    from sentence_transformers import SentenceTransformer

    from app import transcricao
    from app.rag import indice

    # Embeddings na CPU, como no servidor do deploy (sem GPU).
    indice._modelo.cache_clear()
    modelo_cpu = SentenceTransformer(indice.MODELO, device="cpu")
    indice._modelo = lambda: modelo_cpu

    r = {"threads": threads or os.cpu_count(), "inicio_mb": round(pico_mb())}
    t = time.perf_counter()
    whisper = transcricao.carregar()
    r["carga_whisper_s"] = round(time.perf_counter() - t, 1)
    r["pico_depois_do_whisper_mb"] = round(pico_mb())

    t = time.perf_counter()
    idx = indice.indice_padrao()
    r["carga_indice_s"] = round(time.perf_counter() - t, 1)
    r["trechos"] = len(idx.trechos)
    r["pico_depois_do_indice_mb"] = round(pico_mb())

    tempos = {}
    for nome in CASOS:
        dados = (RAIZ / "tests" / "audios" / nome).read_bytes()
        t = time.perf_counter()
        whisper.transcrever(dados, TIPOS[Path(nome).suffix])
        tempos[nome] = round(time.perf_counter() - t, 2)
    r["transcricao_s"] = tempos
    r["transcricao_media_s"] = round(statistics.mean(tempos.values()), 2)
    r["transcricao_max_s"] = max(tempos.values())

    longos = audios_longos()
    r["longo_duracao_s"] = longos["segundos"]
    for chave in ("longo", "longo_com_ruido"):
        t = time.perf_counter()
        texto = whisper.transcrever(longos[chave], "audio/webm")
        r[f"transcricao_{chave}_s"] = round(time.perf_counter() - t, 2)
        r[f"transcricao_{chave}_palavras"] = len(texto.split())

    t = time.perf_counter()
    idx.buscar("ele pode tirar meus filhos de mim?", k=5)
    r["busca_rag_s"] = round(time.perf_counter() - t, 2)
    r["pico_final_mb"] = round(pico_mb())
    return r


def maquina() -> str:
    partes = [platform.platform(), platform.machine(), f"{os.cpu_count()} núcleos lógicos"]
    if sys.platform == "darwin":
        try:
            modelo = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
            memoria = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 2**30
            partes[1:1] = [modelo, f"{memoria:.0f} GB"]
        except (OSError, ValueError):
            pass
    return ", ".join(partes)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threads", type=int, help="mede só esta configuração, num processo (saída em JSON)")
    args = parser.parse_args()
    if args.threads is not None:
        print(json.dumps(medir(args.threads or None)))
        return

    resultados = []
    for threads in (0, 2):  # 0 = todas as threads
        env = dict(os.environ, HF_HUB_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
        if threads:
            env.update(OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads), WHISPER_THREADS=str(threads))
        saida = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--threads", str(threads)],
            env=env, cwd=RAIZ, capture_output=True, text=True, check=True,
        )
        resultados.append(json.loads(saida.stdout.strip().splitlines()[-1]))

    print(f"Máquina: {maquina()}")
    print(f"Data: {time.strftime('%d/%m/%Y')}  |  comando: uv run python scripts/medir_audio_rag.py\n")
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    todas, duas = resultados
    print("\n| Medida | Todas as threads ({}) | 2 threads |".format(todas["threads"]))
    print("| :--- | :--- | :--- |")
    for rotulo, chave, unidade in [
        ("Pico de memória (RAG + Whisper)", "pico_final_mb", " MB"),
        ("Carga do Whisper", "carga_whisper_s", " s"),
        ("Carga do índice (montagem dos vetores)", "carga_indice_s", " s"),
        ("Transcrição A1 a A6, média", "transcricao_media_s", " s"),
        ("Transcrição A1 a A6, máximo", "transcricao_max_s", " s"),
        ("Transcrição da pergunta longa (A1 a A6, ~21 s)", "transcricao_longo_s", " s"),
        ("Transcrição da pergunta longa com ruído forte (SNR -5 dB)", "transcricao_longo_com_ruido_s", " s"),
        ("Busca no RAG", "busca_rag_s", " s"),
    ]:
        print(f"| {rotulo} | {todas[chave]}{unidade} | {duas[chave]}{unidade} |")


if __name__ == "__main__":
    main()
