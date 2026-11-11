"""Comparação LLM x RAG (S3): as duas versões só podem diferir nas frases sobre os trechos."""
import hashlib

from app.rag.resposta import INSTRUCOES, INSTRUCOES_SEM_RAG, montar_mensagens, montar_mensagens_sem_rag

# SHA-256 das instruções da versão com RAG antes da separação. Se mudar, a resposta da
# versão com RAG mudou junto, e a comparação deixa de medir o mesmo sistema.
HASH_INSTRUCOES_RAG = "3b5227cf843ce371481706a164de5f233e17111462dc9b2abc0c0be378976397"


def test_instrucoes_da_versao_com_rag_nao_mudaram():
    assert hashlib.sha256(INSTRUCOES.encode()).hexdigest() == HASH_INSTRUCOES_RAG


def test_so_as_frases_sobre_trechos_diferem():
    com_rag = INSTRUCOES.split("\n")
    sem_rag = INSTRUCOES_SEM_RAG.split("\n")
    so_com_rag = [linha for linha in com_rag if linha not in sem_rag]
    so_sem_rag = [linha for linha in sem_rag if linha not in com_rag]

    # Toda frase que sai ou muda fala dos trechos; nenhuma outra regra é tocada.
    assert so_com_rag and all("trecho" in linha for linha in so_com_rag)
    assert all("trecho" not in linha for linha in sem_rag)
    # As regras comuns ficam na mesma ordem.
    assert [l for l in com_rag if l in sem_rag] == [l for l in sem_rag if l in com_rag]
    # Sai a regra de usar só os trechos; as outras duas são adaptadas, não removidas.
    assert len(so_com_rag) == 3 and len(so_sem_rag) == 2


def test_versao_sem_rag_mantem_formato_de_citacao_e_dizer_que_nao_sabe():
    assert "(Lei 11.340/2006, art. 7º)" in INSTRUCOES_SEM_RAG
    assert "não sabe responder com segurança" in INSTRUCOES_SEM_RAG
    assert "apenas os trechos" not in INSTRUCOES_SEM_RAG


def test_mensagens_sem_rag_levam_so_a_pergunta():
    mensagens = montar_mensagens_sem_rag("Pergunta fictícia de teste?")
    assert mensagens == [
        {"role": "system", "content": INSTRUCOES_SEM_RAG},
        {"role": "user", "content": "Pergunta: Pergunta fictícia de teste?"},
    ]


def test_mensagens_com_rag_terminam_igual_as_sem_rag():
    # A pergunta chega ao modelo do mesmo jeito; só os trechos antes dela mudam.
    trecho = {"lei": "Lei 11.340/2006", "artigo": "7", "texto": "Texto fictício."}
    com_rag = montar_mensagens("Pergunta fictícia?", [trecho])[1]["content"]
    sem_rag = montar_mensagens_sem_rag("Pergunta fictícia?")[1]["content"]
    assert com_rag.endswith("\n\n" + sem_rag)
