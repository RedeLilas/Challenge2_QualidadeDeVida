"""Verificação de citações nas normas de benefícios (s4-rag-beneficios, tarefas 2.1, 2.2 e 2.3).

Cobre:
- 2.1: Configurações JURIDICO e BENEFICIOS da verificação.
- 2.2: Apelidos das 11 normas de benefícios (com e sem ano, com e sem "Distrital"/"SMDF", nomes de programas),
  testados nos dois sentidos (citação correta aceita e citação de outra norma recusada).
- 2.3: Artigo sem norma reconhecida recusado em BENEFICIOS quando há mais de uma norma nos trechos recuperados,
  aceito com uma norma só, e mantido sem mudança em JURIDICO.
"""
import pytest

from app.rag.resposta import (
    APELIDOS,
    APELIDOS_BENEFICIOS,
    BENEFICIOS,
    JURIDICO,
    LEIS_BENEFICIOS,
    LEIS_JURIDICAS,
    RECUSA,
    responder,
    verificar_citacoes,
)
from tests.test_juridico import PERGUNTA, IndiceFalso, LLMFalso, trecho


def trecho_beneficio(lei: str, artigo: str, eixo: str = "df", norma_id: str = "norma-ficticia") -> dict:
    t = trecho(lei, artigo, norma_id=norma_id)
    t["eixo"] = eixo
    return t


# --- 2.1: configurações JURIDICO e BENEFICIOS ---------------------------------------------


def test_configuracoes_juridico_e_beneficios():
    assert JURIDICO.leis == LEIS_JURIDICAS
    assert JURIDICO.apelidos == APELIDOS
    assert JURIDICO.recusar_artigo_sem_norma_em_varias_leis is False

    assert len(LEIS_BENEFICIOS) == 11
    assert BENEFICIOS.leis == LEIS_BENEFICIOS
    assert BENEFICIOS.apelidos == APELIDOS_BENEFICIOS
    assert BENEFICIOS.recusar_artigo_sem_norma_em_varias_leis is True
    assert set(BENEFICIOS.apelidos) == set(LEIS_BENEFICIOS)


# --- 2.2: apelidos das 11 normas (citação correta aceita e outra norma recusada) ----------


CASOS_APELIDOS_ACEITOS = [
    # Lei 14.601/2023 (Bolsa Família)
    ("Lei 14.601/2023", "3", "(Lei 14.601/2023, art. 3º)"),
    ("Lei 14.601/2023", "3", "(Lei 14.601, art. 3º)"),
    ("Lei 14.601/2023", "3", "(Lei 14601, art. 3º)"),
    ("Lei 14.601/2023", "3", "Conforme a Lei do Bolsa Família, art. 3º, o programa atende famílias."),
    # Lei 8.742/1993 (LOAS)
    ("Lei 8.742/1993 (LOAS)", "20", "(Lei 8.742/1993 (LOAS), art. 20)"),
    ("Lei 8.742/1993 (LOAS)", "20", "(Lei 8.742/1993, art. 20)"),
    ("Lei 8.742/1993 (LOAS)", "20", "(Lei 8.742, art. 20)"),
    ("Lei 8.742/1993 (LOAS)", "20", "(Lei 8742, art. 20)"),
    ("Lei 8.742/1993 (LOAS)", "20", "(LOAS, art. 20)"),
    # Lei Distrital 6.623/2020 (Aluguel Social DF)
    ("Lei Distrital 6.623/2020", "1", "(Lei Distrital 6.623/2020, art. 1º)"),
    ("Lei Distrital 6.623/2020", "1", "(Lei Distrital 6.623, art. 1º)"),
    ("Lei Distrital 6.623/2020", "1", "(Lei 6.623/2020, art. 1º)"),
    ("Lei Distrital 6.623/2020", "1", "(Lei 6.623, art. 1º)"),
    ("Lei Distrital 6.623/2020", "1", "(Lei 6623, art. 1º)"),
    # Decreto Distrital 45.989/2024
    ("Decreto Distrital 45.989/2024", "2", "(Decreto Distrital 45.989/2024, art. 2º)"),
    ("Decreto Distrital 45.989/2024", "2", "(Decreto Distrital 45.989, art. 2º)"),
    ("Decreto Distrital 45.989/2024", "2", "(Decreto 45.989/2024, art. 2º)"),
    ("Decreto Distrital 45.989/2024", "2", "(Decreto 45.989, art. 2º)"),
    ("Decreto Distrital 45.989/2024", "2", "(Decreto 45989, art. 2º)"),
    # Portaria SMDF 49/2026
    ("Portaria SMDF 49/2026", "4", "(Portaria SMDF 49/2026, art. 4º)"),
    ("Portaria SMDF 49/2026", "4", "(Portaria SMDF 49, art. 4º)"),
    ("Portaria SMDF 49/2026", "4", "(Portaria SMDF n.º 49, art. 4º)"),
    ("Portaria SMDF 49/2026", "4", "(Portaria 49/2026, art. 4º)"),
    ("Portaria SMDF 49/2026", "4", "(Portaria 49, art. 4º)"),
    ("Portaria SMDF 49/2026", "4", "(Portaria n.º 49, art. 4º)"),
    # Lei Distrital 6.938/2021 (Cartão Gás)
    ("Lei Distrital 6.938/2021", "1", "(Lei Distrital 6.938/2021, art. 1º)"),
    ("Lei Distrital 6.938/2021", "1", "(Lei Distrital 6.938, art. 1º)"),
    ("Lei Distrital 6.938/2021", "1", "(Lei 6.938/2021, art. 1º)"),
    ("Lei Distrital 6.938/2021", "1", "(Lei 6.938, art. 1º)"),
    ("Lei Distrital 6.938/2021", "1", "Segundo a lei do Cartão Gás (art. 1º), o auxílio é bimestral."),
    # Decreto Distrital 42.376/2021
    ("Decreto Distrital 42.376/2021", "3", "(Decreto Distrital 42.376/2021, art. 3º)"),
    ("Decreto Distrital 42.376/2021", "3", "(Decreto Distrital 42.376, art. 3º)"),
    ("Decreto Distrital 42.376/2021", "3", "(Decreto 42.376/2021, art. 3º)"),
    ("Decreto Distrital 42.376/2021", "3", "(Decreto 42.376, art. 3º)"),
    ("Decreto Distrital 42.376/2021", "3", "(Decreto 42376, art. 3º)"),
    # Lei Distrital 7.009/2021 (Prato Cheio)
    ("Lei Distrital 7.009/2021", "2", "(Lei Distrital 7.009/2021, art. 2º)"),
    ("Lei Distrital 7.009/2021", "2", "(Lei Distrital 7.009, art. 2º)"),
    ("Lei Distrital 7.009/2021", "2", "(Lei 7.009/2021, art. 2º)"),
    ("Lei Distrital 7.009/2021", "2", "(Lei 7.009, art. 2º)"),
    ("Lei Distrital 7.009/2021", "2", "O programa Prato Cheio prevê o crédito no art. 2º."),
    # Decreto Distrital 42.873/2021
    ("Decreto Distrital 42.873/2021", "5", "(Decreto Distrital 42.873/2021, art. 5º)"),
    ("Decreto Distrital 42.873/2021", "5", "(Decreto Distrital 42.873, art. 5º)"),
    ("Decreto Distrital 42.873/2021", "5", "(Decreto 42.873/2021, art. 5º)"),
    ("Decreto Distrital 42.873/2021", "5", "(Decreto 42.873, art. 5º)"),
    # Lei Distrital 5.165/2013
    ("Lei Distrital 5.165/2013", "6", "(Lei Distrital 5.165/2013, art. 6º)"),
    ("Lei Distrital 5.165/2013", "6", "(Lei Distrital 5.165, art. 6º)"),
    ("Lei Distrital 5.165/2013", "6", "(Lei 5.165/2013, art. 6º)"),
    ("Lei Distrital 5.165/2013", "6", "(Lei 5.165, art. 6º)"),
    # Decreto Distrital 35.191/2014
    ("Decreto Distrital 35.191/2014", "7", "(Decreto Distrital 35.191/2014, art. 7º)"),
    ("Decreto Distrital 35.191/2014", "7", "(Decreto Distrital 35.191, art. 7º)"),
    ("Decreto Distrital 35.191/2014", "7", "(Decreto 35.191/2014, art. 7º)"),
    ("Decreto Distrital 35.191/2014", "7", "(Decreto 35.191, art. 7º)"),
]


@pytest.mark.parametrize("lei, artigo, texto", CASOS_APELIDOS_ACEITOS)
def test_apelido_de_beneficio_aceito_quando_artigo_foi_recuperado(lei, artigo, texto):
    recuperados = [
        trecho_beneficio(lei, artigo),
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "99", eixo="beneficios"),
    ]
    citacoes = verificar_citacoes(f"Informação fictícia {texto}.", recuperados, verificacao=BENEFICIOS)
    assert citacoes is not None
    assert [(c["lei"], c["artigo"]) for c in citacoes] == [(lei, artigo)]


CASOS_APELIDOS_OUTRA_NORMA_RECUSADOS = [
    # Casos explícitos da tarefa 2.2:
    ("Decreto Distrital 42.376/2021", "Lei 14.601/2023", "3", "(Decreto 42.376, art. 3º)"),
    ("Lei Distrital 6.623/2020", "Lei 14.601/2023", "1", "(Lei Distrital 6.623, art. 1º)"),
    ("Lei Distrital 6.623/2020", "Lei 14.601/2023", "1", "(Lei 6.623, art. 1º)"),
    # Demais normas das 11 (sentido inverso para cada uma):
    ("Lei 14.601/2023", "Lei 8.742/1993 (LOAS)", "20", "(Lei 14.601, art. 20)"),
    ("Lei 14.601/2023", "Lei 8.742/1993 (LOAS)", "20", "(Bolsa Família, art. 20)"),
    ("Lei 8.742/1993 (LOAS)", "Lei 14.601/2023", "3", "(Lei 8.742/1993, art. 3º)"),
    ("Lei 8.742/1993 (LOAS)", "Lei 14.601/2023", "3", "(LOAS, art. 3º)"),
    ("Decreto Distrital 45.989/2024", "Lei 14.601/2023", "2", "(Decreto 45.989, art. 2º)"),
    ("Portaria SMDF 49/2026", "Lei 14.601/2023", "4", "(Portaria 49, art. 4º)"),
    ("Portaria SMDF 49/2026", "Lei 14.601/2023", "4", "(Portaria SMDF n.º 49, art. 4º)"),
    ("Lei Distrital 6.938/2021", "Decreto Distrital 42.376/2021", "1", "(Lei 6.938, art. 1º)"),
    # Nome compartilhado ("Cartão Gás", "Prato Cheio") aponta só para a lei, não para o decreto:
    ("Lei Distrital 6.938/2021", "Decreto Distrital 42.376/2021", "1", "Pelo Cartão Gás (art. 1º), o auxílio é pago."),
    ("Lei Distrital 7.009/2021", "Decreto Distrital 42.873/2021", "2", "(Lei 7.009, art. 2º)"),
    ("Lei Distrital 7.009/2021", "Decreto Distrital 42.873/2021", "2", "No Prato Cheio (art. 2º), há crédito."),
    ("Decreto Distrital 42.873/2021", "Lei Distrital 7.009/2021", "5", "(Decreto 42.873, art. 5º)"),
    ("Lei Distrital 5.165/2013", "Decreto Distrital 35.191/2014", "6", "(Lei 5.165, art. 6º)"),
    ("Decreto Distrital 35.191/2014", "Lei Distrital 5.165/2013", "7", "(Decreto 35.191, art. 7º)"),
]


@pytest.mark.parametrize("lei_citada, lei_recuperada, artigo, texto", CASOS_APELIDOS_OUTRA_NORMA_RECUSADOS)
def test_apelido_de_beneficio_recusado_quando_artigo_e_de_outra_norma(lei_citada, lei_recuperada, artigo, texto):
    assert lei_citada != lei_recuperada
    recuperados = [trecho_beneficio(lei_recuperada, artigo)]
    assert verificar_citacoes(f"Informação fictícia {texto}.", recuperados, verificacao=BENEFICIOS) is None


# --- 2.3: artigo sem norma reconhecida (várias normas vs uma norma só vs jurídico) --------


def test_beneficios_recusa_artigo_sem_norma_quando_trechos_vem_de_varias_normas():
    recuperados = [
        trecho_beneficio("Lei 14.601/2023", "3", eixo="beneficios"),
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "20", eixo="beneficios"),
    ]
    texto = "O benefício atende famílias em situação de vulnerabilidade, conforme o art. 3º."
    assert verificar_citacoes(texto, recuperados, verificacao=BENEFICIOS) is None


def test_beneficios_aceita_artigo_sem_norma_quando_trechos_vem_de_uma_norma_so():
    recuperados = [
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "20", eixo="beneficios"),
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "21", eixo="beneficios"),
    ]
    texto = "O benefício de prestação continuada está previsto no art. 20."
    citacoes = verificar_citacoes(texto, recuperados, verificacao=BENEFICIOS)
    assert citacoes is not None
    assert [(c["lei"], c["artigo"]) for c in citacoes] == [("Lei 8.742/1993 (LOAS)", "20")]


def test_juridico_mantem_comportamento_anterior_para_artigo_sem_norma_com_varias_normas():
    recuperados = [
        trecho("Lei 11.340/2006", "7"),
        trecho("Código Penal", "147", norma_id="decreto-lei-2848-1940"),
    ]
    texto = "O benefício ou medida segue o art. 7º."
    citacoes_juridico = verificar_citacoes(texto, recuperados, verificacao=JURIDICO)
    assert citacoes_juridico is not None
    assert [(c["lei"], c["artigo"]) for c in citacoes_juridico] == [("Lei 11.340/2006", "7")]

    # O mesmo caso na configuração BENEFICIOS é recusado:
    assert verificar_citacoes(texto, recuperados, verificacao=BENEFICIOS) is None


def test_responder_usa_configuracao_beneficios():
    recuperados = [
        trecho_beneficio("Lei 14.601/2023", "3", eixo="beneficios"),
        trecho_beneficio("Lei Distrital 6.623/2020", "1", eixo="df"),
    ]
    indice = IndiceFalso(recuperados)

    # Citação correta sem "Distrital" é aceita com verificacao=BENEFICIOS
    ok = responder(
        PERGUNTA,
        indice,
        LLMFalso("O Aluguel Social atende mulheres em vulnerabilidade (Lei 6.623, art. 1º)."),
        eixos={"beneficios", "df"},
        verificacao=BENEFICIOS,
    )
    assert ok["recusada"] is False
    assert [(c["lei"], c["artigo"]) for c in ok["citacoes"]] == [("Lei Distrital 6.623/2020", "1")]

    # Citação de outra norma com o mesmo número de artigo é recusada
    recusado_outra = responder(
        PERGUNTA,
        indice,
        LLMFalso("O auxílio segue a regra do decreto (Decreto 42.376, art. 3º)."),
        eixos={"beneficios", "df"},
        verificacao=BENEFICIOS,
    )
    assert recusado_outra == {"resposta": RECUSA, "citacoes": [], "recusada": True}

    # Artigo sem norma reconhecida com trechos de mais de uma norma é recusado em BENEFICIOS
    recusado_sem_lei = responder(
        PERGUNTA,
        indice,
        LLMFalso("O benefício atende famílias conforme o art. 3º."),
        eixos={"beneficios", "df"},
        verificacao=BENEFICIOS,
    )
    assert recusado_sem_lei == {"resposta": RECUSA, "citacoes": [], "recusada": True}
