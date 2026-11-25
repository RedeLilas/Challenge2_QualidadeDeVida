"""O áudio não deixa rastro: nada no disco e nada nos logs (s5-entrada-audio, tarefas 2.2 e 2.3).

Os pedidos passam pela rota POST /transcrever de verdade, com a decodificação de verdade (PyAV).
Na suíte padrão, o modelo é falso; com a marca `whisper`, é o Whisper de verdade sobre o caso A1.
Os áudios são tons gerados aqui ou voz sintética offline (tests/audios/LEIAME.md): nenhuma voz real.
"""
import io
import logging
import os
import tempfile
from pathlib import Path

import av
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import main, risco, transcricao
from app.main import app

RAIZ = Path(__file__).resolve().parents[1]
A1 = (RAIZ / "tests" / "audios" / "a1.webm").read_bytes()
TEXTO_A1 = "Ele pode tirar meus filhos de mim?"  # caso fictício A1
IGNORAR = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}


def tom(segundos: float) -> bytes:
    """Tom de 440 Hz em webm/opus, gerado em memória (sem voz)."""
    taxa = 48_000
    saida = io.BytesIO()
    with av.open(saida, "w", format="webm") as container:
        stream = container.add_stream("libopus", rate=taxa)
        stream.layout = "mono"
        amostras = (0.2 * np.sin(2 * np.pi * 440 * np.arange(int(taxa * segundos)) / taxa)).astype(np.float32)
        quadro = av.AudioFrame.from_ndarray(amostras.reshape(1, -1), format="flt", layout="mono")
        quadro.rate = taxa
        for pacote in stream.encode(quadro):
            container.mux(pacote)
        for pacote in stream.encode(None):
            container.mux(pacote)
    return saida.getvalue()


class Segmento:
    def __init__(self, text):
        self.text = text


class ModeloFalso:
    """Faz o papel do WhisperModel: devolve o texto de A1, ou falha como um erro do modelo."""

    def __init__(self, erro=None):
        self.erro = erro

    def transcribe(self, _amostras, **_opcoes):
        if self.erro:
            raise self.erro
        return iter([Segmento(TEXTO_A1)]), None


def arquivos_do_repositorio() -> set[str]:
    # Poda as pastas ignoradas antes de entrar nelas: o rglob percorria o .venv e o .git inteiros
    # (dezenas de milhares de arquivos) só para descartá-los, cerca de 3 s por listagem.
    arquivos = set()
    for pasta, subpastas, nomes in os.walk(RAIZ):
        subpastas[:] = [nome for nome in subpastas if nome not in IGNORAR]
        relativa = Path(pasta).relative_to(RAIZ)
        arquivos.update(str(relativa / nome) for nome in nomes)
    return arquivos


@pytest.fixture
def disco_vigiado(tmp_path, monkeypatch):
    """Temporários e diretório de trabalho apontados para pastas vazias, e o repositório listado antes e depois."""
    temporarios, trabalho = tmp_path / "tmp", tmp_path / "trabalho"
    temporarios.mkdir()
    trabalho.mkdir()
    for variavel in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(variavel, str(temporarios))
    monkeypatch.setattr(tempfile, "tempdir", str(temporarios))
    monkeypatch.chdir(trabalho)
    antes = arquivos_do_repositorio()
    yield
    assert list(temporarios.rglob("*")) == [], "arquivo temporário deixado no disco"
    assert list(trabalho.rglob("*")) == [], "arquivo deixado no diretório de trabalho"
    assert arquivos_do_repositorio() == antes, "arquivo novo no repositório"


@pytest.fixture
def cliente():
    original = main.transcritor
    yield TestClient(app)
    main.transcritor = original


def usar(transcritor):
    main.transcritor = lambda: transcritor


def enviar(cliente, corpo, tipo="audio/webm;codecs=opus"):
    return cliente.post("/transcrever", content=corpo, headers={"Content-Type": tipo})


# --- 2.2: nada fica no disco, com sucesso ou com falha ---

CASOS_DO_DISCO = {
    "sucesso": (lambda: tom(2), None, 200),
    "corrompido": (lambda: b"\x1aE\xdf\xa3" + b"\x00" * 512, None, 422),
    "nao_e_audio": (lambda: b"isto nao e audio", None, 422),
    "acima_de_1_mb": (lambda: b"0" * (transcricao.LIMITE_BYTES + 1), None, 413),
    "acima_de_35_s": (lambda: tom(transcricao.LIMITE_SEGUNDOS + 3), None, 422),
    "erro_do_modelo": (lambda: tom(2), RuntimeError("falha fictícia do modelo"), 503),
}


@pytest.mark.parametrize("caso", CASOS_DO_DISCO, ids=str)
def test_nenhum_arquivo_fica_no_disco(cliente, disco_vigiado, caso):
    gerar, erro, status = CASOS_DO_DISCO[caso]
    usar(transcricao.Whisper(ModeloFalso(erro)))
    resposta = enviar(cliente, gerar())
    assert resposta.status_code == status
    if status == 200:
        assert resposta.json() == {"texto": TEXTO_A1}


def test_o_vigia_do_disco_pega_um_temporario_esquecido(tmp_path, monkeypatch):
    # Confere o próprio teste: um temporário que não é apagado é encontrado.
    temporarios = tmp_path / "tmp"
    temporarios.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temporarios))
    tempfile.NamedTemporaryFile(delete=False).close()
    assert len(list(temporarios.rglob("*"))) == 1


# --- 2.3: nada do áudio nem da transcrição nos logs ---


def palavras_da_transcricao(texto: str) -> list[str]:
    return [p for p in risco.normalizar(texto).replace("?", " ").split() if len(p) >= 4]


def conferir_logs(texto_dos_logs: str, audio: bytes, texto: str):
    normalizado = risco.normalizar(texto_dos_logs)
    for palavra in palavras_da_transcricao(texto):
        assert palavra not in normalizado, f"a palavra {palavra!r} da transcrição apareceu no log"
    # Nem os bytes do áudio, em nenhuma das formas em que um log costuma mostrá-los.
    trecho = audio[100:132]
    for forma in (repr(trecho)[2:-1], trecho.hex(), trecho.decode("latin-1")):
        assert forma not in texto_dos_logs


@pytest.fixture
def todos_os_logs_em_debug(caplog):
    # Pior caso: todos os loggers em DEBUG, inclusive os das bibliotecas (faster-whisper, PyAV, uvicorn).
    caplog.set_level(logging.DEBUG)
    nomes = list(logging.root.manager.loggerDict) + ["faster_whisper", "rede_lilas.http", "rede_lilas.transcricao"]
    originais = {nome: logging.getLogger(nome).level for nome in nomes}
    for nome in nomes:
        logging.getLogger(nome).setLevel(logging.DEBUG)
    yield caplog
    for nome, nivel in originais.items():
        logging.getLogger(nome).setLevel(nivel)


def test_logs_sem_audio_nem_transcricao(cliente, todos_os_logs_em_debug, capfd):
    audio = tom(2)
    usar(transcricao.Whisper(ModeloFalso()))
    assert enviar(cliente, audio).json() == {"texto": TEXTO_A1}
    usar(transcricao.Whisper(ModeloFalso(RuntimeError(f"falha com {TEXTO_A1}"))))
    assert enviar(cliente, audio).status_code == 503
    assert enviar(cliente, b"\x1aE\xdf\xa3" + audio[4:200]).status_code == 422
    saida = capfd.readouterr()
    logs = todos_os_logs_em_debug.text
    assert "POST /transcrever 200" in logs  # o middleware registrou, só com dados técnicos
    conferir_logs(logs + saida.out + saida.err, audio, TEXTO_A1)


def test_conferencia_dos_logs_pega_um_vazamento():
    # Confere o próprio teste: um log com a transcrição ou com os bytes é encontrado.
    with pytest.raises(AssertionError):
        conferir_logs(f"texto={TEXTO_A1}", A1, TEXTO_A1)
    with pytest.raises(AssertionError):
        conferir_logs(f"corpo={A1[:300]!r}", A1, TEXTO_A1)


# --- Com o Whisper de verdade (uv run pytest -m whisper) ---


@pytest.fixture(scope="module")
def whisper():
    return transcricao.carregar()


@pytest.mark.whisper
@pytest.mark.parametrize("corpo, status", [(A1, 200), (b"\x1aE\xdf\xa3" + A1[4:300], 422)], ids=["a1", "corrompido"])
def test_whisper_de_verdade_sem_rastro(cliente, whisper, disco_vigiado, todos_os_logs_em_debug, capfd, corpo, status):
    usar(whisper)
    resposta = enviar(cliente, corpo)
    assert resposta.status_code == status
    if status == 200:
        assert risco.normalizar(resposta.json()["texto"]).startswith("ele pode tirar meus filhos")
    saida = capfd.readouterr()
    conferir_logs(todos_os_logs_em_debug.text + saida.out + saida.err, corpo, TEXTO_A1)


def test_telemetria_do_onnxruntime_desligada():
    # Com ela ligada, a primeira transcrição do processo grava um .ses no diretório temporário (24/11).
    import os

    assert os.environ.get("ORT_DISABLE_TELEMETRY") == "1"
