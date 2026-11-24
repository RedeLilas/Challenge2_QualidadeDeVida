"""Transcrição da pergunta por áudio no servidor da própria aplicação (s5-entrada-audio).

O áudio nunca vai a serviço externo e nunca é guardado: chega no corpo da requisição, é
transcrito em memória e descartado. Nada do áudio nem da transcrição vai para os logs.

Contrato da rota POST /transcrever (limites, mensagens, erros, carga em segundo plano e uma
transcrição por vez) e o Whisper local: faster-whisper, modelo de `WHISPER_MODELO` (padrão
`small`) em int8 na CPU, português fixo e filtro de silêncio. `WHISPER_THREADS` (opcional)
limita as threads, por exemplo para medir como numa máquina de 2 vCPUs.
"""
import io
import logging
import os
import threading
from typing import Protocol

# O onnxruntime (filtro de silêncio do faster-whisper) traz a telemetria da Microsoft (1DS): com ela
# ligada, a primeira transcrição do processo grava um arquivo de sessão (.ses) no diretório temporário,
# e o pacote inclui um cliente HTTP para enviar eventos. Desligada antes de o onnxruntime ser importado
# (os imports do faster-whisper são tardios), nenhum arquivo é criado. Achado de 24/11, tarefa 2.2.
os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")

logger = logging.getLogger("rede_lilas.transcricao")

# 1 MB e 30 s de gravação, com 5 s de tolerância para o cabeçalho e o fim da gravação.
LIMITE_BYTES = 1_000_000
LIMITE_SEGUNDOS = 35

MODELO_PADRAO = "small"
TAXA = 16_000  # o Whisper trabalha com áudio mono de 16 kHz

MENSAGENS = {
    "limite": "O áudio pode ter até 30 segundos. Grave de novo, em partes, ou digite sua pergunta.",
    "ilegivel": "Não consegui ler o áudio. Grave de novo ou digite sua pergunta.",
    "sem_fala": "Não entendi o áudio. Tente de novo ou digite sua pergunta.",
    "iniciando": "A transcrição ainda está iniciando. Tente em alguns segundos ou digite sua pergunta.",
    "indisponivel": (
        "A transcrição não está disponível agora. Digite sua pergunta. "
        "Se precisar falar com alguém, ligue 180 (gratuito, 24 horas)."
    ),
}


class AudioLongo(Exception):
    """O áudio passa de LIMITE_SEGUNDOS."""


class AudioIlegivel(Exception):
    """O arquivo está corrompido ou não é áudio."""


class TranscricaoIniciando(Exception):
    """O modelo ainda está carregando."""


class TranscricaoIndisponivel(Exception):
    """A carga do modelo falhou."""


class Transcritor(Protocol):
    def transcrever(self, audio: bytes, tipo: str) -> str:
        """Texto falado no áudio ("" se não houver fala). Levanta AudioLongo ou AudioIlegivel."""


class Whisper:
    """Transcritor com o faster-whisper. O áudio é decodificado em memória, sem arquivo no disco."""

    def __init__(self, modelo):
        self._modelo = modelo

    def transcrever(self, audio: bytes, tipo: str) -> str:
        # Import tardio: os testes rápidos usam um transcritor falso e não carregam o faster-whisper.
        from faster_whisper.audio import decode_audio

        try:
            # PyAV lê webm/opus (Chrome/Android) e mp4/aac (Safari/iPhone) de um BytesIO.
            amostras = decode_audio(io.BytesIO(audio), sampling_rate=TAXA)
        except Exception:
            # A mensagem do PyAV pode citar o conteúdo; o erro sai sem ela.
            raise AudioIlegivel from None
        if len(amostras) == 0:
            raise AudioIlegivel
        if len(amostras) / TAXA > LIMITE_SEGUNDOS:
            raise AudioLongo
        # Português fixo (sem detectar o idioma, que custa tempo e erra em falas curtas), filtro de
        # silêncio antes de transcrever e busca gulosa (beam_size=1), a mais rápida em CPU.
        segmentos, _info = self._modelo.transcribe(amostras, language="pt", vad_filter=True, beam_size=1)
        return " ".join(segmento.text.strip() for segmento in segmentos).strip()


def _threads(env) -> int:
    valor = (env.get("WHISPER_THREADS") or "").strip()
    if valor.isdigit() and int(valor) > 0:
        return int(valor)
    return os.cpu_count() or 1


def carregar(env=None) -> Transcritor:
    """Carrega o Whisper (na primeira vez, baixa o modelo do Hugging Face; no deploy, vem do build)."""
    from faster_whisper import WhisperModel

    env = os.environ if env is None else env
    # No INFO, o faster-whisper registra a duração do áudio e o trecho cortado pelo filtro de silêncio.
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)
    nome = (env.get("WHISPER_MODELO") or "").strip() or MODELO_PADRAO
    modelo = WhisperModel(nome, device="cpu", compute_type="int8", cpu_threads=_threads(env))
    return Whisper(modelo)


_trava_carga = threading.Lock()
# Uma transcrição por vez: limita a memória e a CPU; um segundo pedido espera.
_trava_uso = threading.Lock()
_transcritor: Transcritor | None = None
_estado = "parado"  # parado, carregando, pronto ou falhou


def carregar_em_segundo_plano() -> None:
    """Chamada ao subir o servidor, numa thread, para o primeiro áudio não esperar a carga."""
    global _transcritor, _estado
    with _trava_carga:
        if _transcritor is not None:
            return
        _estado = "carregando"
        try:
            _transcritor = carregar()
        except Exception as erro:  # qualquer falha deixa a rota em "indisponível"
            _estado = "falhou"
            # Só o tipo: a mensagem pode trazer caminhos da máquina.
            logger.error("carga do Whisper falhou: %s", type(erro).__name__)
            return
        _estado = "pronto"


def transcritor_pronto() -> Transcritor:
    """O transcritor carregado, ou o erro que a rota transforma em 503."""
    if _transcritor is not None:
        return _transcritor
    if _estado == "falhou":
        raise TranscricaoIndisponivel
    raise TranscricaoIniciando


def transcrever(transcritor: Transcritor, audio: bytes, tipo: str) -> str:
    """Transcreve com a trava de uma transcrição por vez e devolve o texto sem espaços nas pontas."""
    with _trava_uso:
        return (transcritor.transcrever(audio, tipo) or "").strip()
