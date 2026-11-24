"""Transcrição da pergunta por áudio no servidor da própria aplicação (s5-entrada-audio).

O áudio nunca vai a serviço externo e nunca é guardado: chega no corpo da requisição, é
transcrito em memória e descartado. Nada do áudio nem da transcrição vai para os logs.

Este módulo guarda o contrato usado pela rota POST /transcrever (limites, mensagens, erros,
carga em segundo plano e uma transcrição por vez). A carga do Whisper (faster-whisper,
`WHISPER_MODELO`, padrão `small` em int8) é a tarefa 1.3: até lá, `carregar()` não existe
e a rota responde que a transcrição está indisponível.
"""
import logging
import threading
from typing import Protocol

logger = logging.getLogger("rede_lilas.transcricao")

# 1 MB e 30 s de gravação, com 5 s de tolerância para o cabeçalho e o fim da gravação.
LIMITE_BYTES = 1_000_000
LIMITE_SEGUNDOS = 35

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


def carregar() -> Transcritor:
    """Carrega o Whisper. Implementada na tarefa 1.3 (#123)."""
    raise NotImplementedError("a carga do Whisper é a tarefa 1.3 da s5-entrada-audio (#123)")


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
