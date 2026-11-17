"""Instruções, recusa e aviso com a data da coleta no RAG de benefícios (s4-rag-beneficios, tarefa 3.1).

O índice e o LLM são simulados. Textos fictícios.
"""
import json
from pathlib import Path

import pytest

from app import main, orquestrador, risco
from app.orquestrador import RespostaAgente
from app.rag.resposta import (
    AVISO_BENEFICIOS,
    EIXOS_BENEFICIOS,
    INSTRUCOES_BENEFICIOS,
    LIMITE_BENEFICIOS,
    RECUSA,
    RECUSA_BENEFICIOS,
    aviso_beneficios,
    expandir_siglas_beneficios,
    explicar_beneficio,
)
from tests.test_juridico import IndiceFalso, LLMFalso, trecho

PERGUNTA_BENEFICIO = "Pergunta fictícia: como funciona o auxílio do gás?"


def trecho_beneficio(
    lei: str,
    artigo: str,
    *,
    data_acesso: str = "2026-11-03",
    eixo: str = "df",
    norma_id: str = "norma-ficticia",
) -> dict:
    t = trecho(lei, artigo, norma_id=norma_id)
    t["eixo"] = eixo
    t["data_acesso"] = data_acesso
    return t


def test_instrucoes_beneficios_orienta_explicacao_sem_decidir_direito():
    assert "português do Brasil" in INSTRUCOES_BENEFICIOS
    assert "tela Benefícios" in INSTRUCOES_BENEFICIOS
    assert "CRAS" in INSTRUCOES_BENEFICIOS
    assert "190" in INSTRUCOES_BENEFICIOS
    assert "não sabe explicar com segurança" in INSTRUCOES_BENEFICIOS


def test_recusa_beneficios_indica_cras_e_180_sem_defensoria():
    assert "CRAS" in RECUSA_BENEFICIOS
    assert "180" in RECUSA_BENEFICIOS
    assert "Defensoria" not in RECUSA_BENEFICIOS


def test_explicar_beneficio_envia_instrucoes_beneficios_e_devolve_aviso():
    recuperados = [
        trecho_beneficio("Lei Distrital 6.938/2021", "1", data_acesso="2026-11-03"),
        trecho_beneficio("Decreto Distrital 42.376/2021", "3", data_acesso="2026-11-05"),
    ]
    indice = IndiceFalso(recuperados)
    llm_falso = LLMFalso(
        "O Cartão Gás apoia famílias de baixa renda na compra do botijão (Lei Distrital 6.938/2021, art. 1º). "
        "Consulte a tela Benefícios ou procure o CRAS."
    )

    resultado = explicar_beneficio(PERGUNTA_BENEFICIO, indice, llm_falso)
    RespostaAgente.model_validate(resultado)

    assert indice.chamadas == [{"pergunta": PERGUNTA_BENEFICIO, "k": 5, "eixos": EIXOS_BENEFICIOS}]
    assert llm_falso.recebido[0] == {"role": "system", "content": INSTRUCOES_BENEFICIOS}
    assert resultado["recusada"] is False
    assert [(c["lei"], c["artigo"]) for c in resultado["citacoes"]] == [("Lei Distrital 6.938/2021", "1")]
    assert resultado["aviso"] == "Valores e regras podem mudar por decreto. Norma consultada em 03/11/2026."


def test_aviso_usa_data_mais_antiga_entre_as_normas_citadas():
    recuperados = [
        trecho_beneficio("Lei Distrital 6.938/2021", "1", data_acesso="2026-11-10"),
        trecho_beneficio("Decreto Distrital 42.376/2021", "3", data_acesso="2026-11-02"),
        # Trecho recuperado com data ainda mais antiga, mas NÃO citado pelo LLM: não entra no aviso.
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "20", data_acesso="2026-10-01", eixo="beneficios"),
    ]
    indice = IndiceFalso(recuperados)
    llm_falso = LLMFalso(
        "O auxílio está previsto na lei (Lei Distrital 6.938/2021, art. 1º) e regulamentado "
        "pelo decreto (Decreto Distrital 42.376/2021, art. 3º)."
    )

    resultado = explicar_beneficio(PERGUNTA_BENEFICIO, indice, llm_falso)

    assert resultado["recusada"] is False
    assert len(resultado["citacoes"]) == 2
    assert resultado["aviso"] == "Valores e regras podem mudar por decreto. Norma consultada em 02/11/2026."


def test_aviso_beneficios_sem_citacoes_retorna_none():
    assert aviso_beneficios([]) is None


@pytest.mark.parametrize(
    "resposta_llm",
    [
        "Não sei explicar com segurança a partir dos trechos.",
        "O saque segue a regra do FGTS (Lei 8.036/1990, art. 20).",
        "O benefício está no decreto (Decreto 42.376, art. 1º).",
    ],
    ids=["sem-citacao", "lei-fora-da-base", "artigo-de-outra-norma"],
)
def test_explicar_beneficio_recusa_quando_citacao_nao_sustenta(resposta_llm):
    recuperados = [trecho_beneficio("Lei Distrital 6.938/2021", "1", data_acesso="2026-11-03")]
    resultado = explicar_beneficio(PERGUNTA_BENEFICIO, IndiceFalso(recuperados), LLMFalso(resposta_llm))
    RespostaAgente.model_validate(resultado)

    assert resultado == {"resposta": RECUSA_BENEFICIOS, "citacoes": [], "recusada": True, "aviso": None}


def test_explicar_beneficio_recusa_abaixo_do_limite_sem_chamar_llm():
    class IndiceDistante(IndiceFalso):
        def buscar(self, pergunta, k=5, eixos=None):
            return [(t, 0.70) for t in self.trechos[:k]]

    recuperados = [trecho_beneficio("Lei Distrital 6.938/2021", "1")]
    llm_falso = LLMFalso("Resposta (Lei Distrital 6.938/2021, art. 1º).")

    resultado = explicar_beneficio("como saco meu fgts?", IndiceDistante(recuperados), llm_falso, limite=0.80)

    assert resultado == {"resposta": RECUSA_BENEFICIOS, "citacoes": [], "recusada": True, "aviso": None}
    assert llm_falso.recebido is None


def test_nenhum_texto_fixo_usa_direito_garantido():
    regras_beneficios = Path(__file__).resolve().parents[1] / "regras" / "beneficios.json"
    textos_fixos = [
        INSTRUCOES_BENEFICIOS,
        RECUSA_BENEFICIOS,
        AVISO_BENEFICIOS,
        RECUSA,
        main.INDISPONIVEL,
        risco.ALERTA,
        orquestrador.FORA_DO_TEMA,
        regras_beneficios.read_text(encoding="utf-8"),
    ]
    for texto in textos_fixos:
        baixo = texto.lower()
        assert "direito garantido" not in baixo
        assert "você tem direito" not in baixo


def test_explicar_beneficio_expande_bpc_so_na_busca_e_mantem_pergunta_original_no_llm():
    recuperados = [
        trecho_beneficio("Lei 8.742/1993 (LOAS)", "20", data_acesso="2026-11-03", eixo="beneficios"),
    ]
    indice = IndiceFalso(recuperados)
    llm_falso = LLMFalso("O BPC é um salário mínimo mensal (Lei 8.742/1993, art. 20).")

    resultado = explicar_beneficio("o que é o bpc?", indice, llm_falso)

    assert expandir_siglas_beneficios("o que é o bpc?") == "o que é o benefício de prestação continuada (bpc)?"
    assert indice.chamadas == [
        {
            "pergunta": "o que é o benefício de prestação continuada (bpc)?",
            "k": 5,
            "eixos": EIXOS_BENEFICIOS,
        }
    ]
    assert llm_falso.recebido[1]["content"].endswith("Pergunta: o que é o bpc?")
    assert "benefício de prestação continuada (bpc)" not in llm_falso.recebido[1]["content"]
    assert resultado["recusada"] is False
    assert LIMITE_BENEFICIOS == 0.815
