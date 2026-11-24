"""Rota POST /transcrever e contrato de app/transcricao.py (s5-entrada-audio, tarefa 2.1).

Transcritor, LLM e índice são falsos. Os "áudios" são bytes fictícios: nenhuma voz real.
"""
import logging
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app import main, transcricao
from app.main import app

AUDIO = b"\x1aE\xdf\xa3 audio ficticio"
TEXTO = "Ele pode tirar meus filhos de mim?"  # caso A1 do design, fictício


class TranscritorFalso:
    def __init__(self, texto=TEXTO, erro=None):
        self.texto, self.erro, self.recebido = texto, erro, []

    def transcrever(self, audio, tipo):
        # A trava de uma transcrição por vez está fechada durante a chamada.
        assert transcricao._trava_uso.locked()
        self.recebido.append((audio, tipo))
        if self.erro:
            raise self.erro
        return self.texto


def nao_pode_ser_chamado(nome):
    def falhar(*_args, **_kwargs):
        raise AssertionError(f"/transcrever não pode chamar {nome}")

    return falhar


@pytest.fixture
def cliente():
    originais = main.transcritor, main.cliente_llm, main.indice_juridico
    # A rota só transcreve: nem o LLM nem o índice podem ser usados.
    main.cliente_llm = nao_pode_ser_chamado("o LLM")
    main.indice_juridico = nao_pode_ser_chamado("o índice")
    yield TestClient(app)
    main.transcritor, main.cliente_llm, main.indice_juridico = originais


@pytest.fixture
def estado_limpo():
    originais = transcricao._transcritor, transcricao._estado, transcricao.carregar
    transcricao._transcritor, transcricao._estado = None, "parado"
    yield
    transcricao._transcritor, transcricao._estado, transcricao.carregar = originais


def usar(transcritor):
    main.transcritor = lambda: transcritor
    return transcritor


def enviar(cliente, corpo=AUDIO, tipo="audio/webm;codecs=opus"):
    return cliente.post("/transcrever", content=corpo, headers={"Content-Type": tipo})


def test_devolve_so_o_texto_sem_cache(cliente):
    falso = usar(TranscritorFalso(texto=f"  {TEXTO}\n"))
    resposta = enviar(cliente)
    assert resposta.status_code == 200
    assert resposta.json() == {"texto": TEXTO}
    assert resposta.headers["cache-control"] == "no-store"
    assert falso.recebido == [(AUDIO, "audio/webm;codecs=opus")]


def test_formato_do_iphone_chega_ao_transcritor(cliente):
    falso = usar(TranscritorFalso())
    assert enviar(cliente, tipo="audio/mp4").status_code == 200
    assert falso.recebido[0][1] == "audio/mp4"


def test_acima_de_1_mb_pelo_tamanho_declarado(cliente):
    falso = usar(TranscritorFalso())
    resposta = enviar(cliente, corpo=b"0" * (transcricao.LIMITE_BYTES + 1))
    assert resposta.status_code == 413
    assert resposta.json() == {"erro": transcricao.MENSAGENS["limite"]}
    assert resposta.headers["cache-control"] == "no-store"
    assert falso.recebido == []


def test_acima_de_1_mb_sem_tamanho_declarado(cliente):
    # Envio em partes (sem Content-Length): a leitura para ao passar de 1 MB.
    falso = usar(TranscritorFalso())

    def partes():
        for _ in range(11):
            yield b"0" * 100_000

    resposta = cliente.post("/transcrever", content=partes(), headers={"Content-Type": "audio/webm"})
    assert resposta.status_code == 413
    assert falso.recebido == []


def test_exatamente_1_mb_e_aceito(cliente):
    usar(TranscritorFalso())
    assert enviar(cliente, corpo=b"0" * transcricao.LIMITE_BYTES).status_code == 200


@pytest.mark.parametrize(
    "erro, chave",
    [
        (transcricao.AudioLongo(), "limite"),  # mais de 35 s
        (transcricao.AudioIlegivel(), "ilegivel"),  # arquivo corrompido ou que não é áudio
    ],
)
def test_audio_recusado_com_mensagem(cliente, erro, chave):
    usar(TranscritorFalso(erro=erro))
    resposta = enviar(cliente)
    assert resposta.status_code == 422
    assert resposta.json() == {"erro": transcricao.MENSAGENS[chave]}
    assert resposta.headers["cache-control"] == "no-store"


def test_corpo_vazio(cliente):
    falso = usar(TranscritorFalso())
    resposta = enviar(cliente, corpo=b"")
    assert resposta.status_code == 422
    assert resposta.json() == {"erro": transcricao.MENSAGENS["ilegivel"]}
    assert falso.recebido == []


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_sem_fala(cliente, texto):
    usar(TranscritorFalso(texto=texto))
    resposta = enviar(cliente)
    assert resposta.status_code == 422
    assert resposta.json() == {"erro": transcricao.MENSAGENS["sem_fala"]}


@pytest.mark.parametrize(
    "erro, chave",
    [(transcricao.TranscricaoIniciando(), "iniciando"), (transcricao.TranscricaoIndisponivel(), "indisponivel")],
)
def test_modelo_carregando_ou_indisponivel(cliente, erro, chave):
    def sem_modelo():
        raise erro

    main.transcritor = sem_modelo
    resposta = enviar(cliente)
    assert resposta.status_code == 503
    assert resposta.json() == {"erro": transcricao.MENSAGENS[chave]}
    assert resposta.headers["cache-control"] == "no-store"
    assert "180" in transcricao.MENSAGENS["indisponivel"]


def test_erro_do_modelo_nao_vaza_conteudo(cliente, caplog):
    usar(TranscritorFalso(erro=RuntimeError(f"falha com {TEXTO}")))
    with caplog.at_level(logging.DEBUG):
        resposta = enviar(cliente)
    assert resposta.status_code == 503
    assert resposta.json() == {"erro": transcricao.MENSAGENS["indisponivel"]}
    assert "RuntimeError" in caplog.text
    assert "filhos" not in caplog.text and "filhos" not in resposta.text


# --- Carga em segundo plano e estado do modelo ---


def test_antes_da_carga_responde_iniciando(estado_limpo):
    with pytest.raises(transcricao.TranscricaoIniciando):
        transcricao.transcritor_pronto()


def test_carga_bem_sucedida(estado_limpo):
    falso = TranscritorFalso()
    transcricao.carregar = lambda: falso
    transcricao.carregar_em_segundo_plano()
    assert transcricao._estado == "pronto"
    assert transcricao.transcritor_pronto() is falso


def test_carga_so_uma_vez(estado_limpo):
    chamadas = []

    def carregar():
        chamadas.append(1)
        return TranscritorFalso()

    transcricao.carregar = carregar
    threads = [threading.Thread(target=transcricao.carregar_em_segundo_plano) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert chamadas == [1]


def test_carga_com_falha_registra_so_o_tipo(estado_limpo, caplog):
    def falhar():
        raise OSError("/caminho/da/maquina/modelo")

    transcricao.carregar = falhar
    with caplog.at_level(logging.DEBUG):
        transcricao.carregar_em_segundo_plano()
    assert transcricao._estado == "falhou"
    assert "OSError" in caplog.text and "/caminho" not in caplog.text
    with pytest.raises(transcricao.TranscricaoIndisponivel):
        transcricao.transcritor_pronto()


def test_sem_whisper_a_rota_responde_indisponivel(estado_limpo):
    # Até a tarefa 1.3, carregar() não existe: a rota fica em 503, sem quebrar o servidor.
    transcricao.carregar_em_segundo_plano()
    assert transcricao._estado == "falhou"
    resposta = TestClient(app).post("/transcrever", content=AUDIO, headers={"Content-Type": "audio/webm"})
    assert resposta.status_code == 503
    assert resposta.json() == {"erro": transcricao.MENSAGENS["indisponivel"]}


def test_servidor_carrega_o_whisper_ao_subir(estado_limpo, monkeypatch):
    falso = TranscritorFalso()
    transcricao.carregar = lambda: falso
    monkeypatch.setattr(main, "indice_juridico", lambda: None)
    with TestClient(app):
        for _ in range(100):
            if transcricao._estado == "pronto":
                break
            time.sleep(0.05)
    assert transcricao.transcritor_pronto() is falso
