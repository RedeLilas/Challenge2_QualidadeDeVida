"""Limite de tamanho e remissões internas nas respostas da conversa (fechamento da S4, #84)."""
from app.orquestrador import INSTRUCOES_AJUDANDO, INSTRUCOES_JURIDICO_CONVERSA, LIMITE_TAMANHO
from app.rag.resposta import INSTRUCOES, INSTRUCOES_BENEFICIOS


def test_juridico_na_conversa_e_o_da_s3_mais_o_limite():
    # Nenhuma regra do jurídico sai; o /juridico continua com INSTRUCOES (tests/test_instrucoes_sem_rag.py).
    assert INSTRUCOES_JURIDICO_CONVERSA == INSTRUCOES + LIMITE_TAMANHO
    assert "no máximo 5 frases curtas" in LIMITE_TAMANHO
    assert "no máximo 5 frases curtas" not in INSTRUCOES


def test_modo_ajudando_tambem_tem_o_limite():
    assert INSTRUCOES_AJUDANDO.startswith(INSTRUCOES_JURIDICO_CONVERSA + "\n")


def test_beneficios_tem_o_limite_e_evita_remissoes_internas():
    assert "no máximo 5 frases curtas" in INSTRUCOES_BENEFICIOS
    assert "aparecem só dentro do texto de outro artigo" in INSTRUCOES_BENEFICIOS
    # O alerta de perigo continua sendo a última regra.
    assert INSTRUCOES_BENEFICIOS.rstrip().endswith("diga para ligar 190.")
