from pathlib import Path

import pytest
import yaml

from app.rag import resposta
from app.rag.indice import Indice, carregar_trechos

PERGUNTAS = Path(__file__).parent / "perguntas_juridicas.yaml"


@pytest.fixture(scope="module")
def indice():
    return Indice(carregar_trechos())


def test_violencia_patrimonial_recupera_art_7(indice):
    # Sem filtro: a busca cobre as 16 normas.
    recuperados = [(t["norma_id"], t["artigo"]) for t, _ in indice.buscar("violência patrimonial")]
    assert ("lei-11340-2006", "7") in recuperados


def test_filtro_por_eixo(indice):
    for eixos in ({"saude"}, {"beneficios", "df"}):
        resultados = indice.buscar("tenho direito a algum auxílio?", eixos=eixos)
        assert len(resultados) == 5
        assert {t["eixo"] for t, _ in resultados} <= eixos


def test_eixo_desconhecido_e_rejeitado(indice):
    with pytest.raises(ValueError, match="penal"):
        indice.buscar("ameaça", eixos={"penal"})


def test_perguntas_das_personas_top5(indice):
    # A orientação jurídica busca só no eixo jurídico (Lei 11.340/2006, Lei 14.149/2021 e Código Penal).
    perguntas = yaml.safe_load(PERGUNTAS.read_text(encoding="utf-8"))["perguntas"]
    erros = []
    for p in perguntas:
        resultados = indice.buscar(p["pergunta"], eixos={"juridico"})
        recuperados = [t["artigo"] for t, _ in resultados if t["norma_id"] == "lei-11340-2006"]
        if not set(p["artigos"]) & set(recuperados):
            erros.append(f"{p['pergunta']!r}: esperado {p['artigos']}, recuperado {[t['citacao'] for t, _ in resultados]}")
    acertos = len(perguntas) - len(erros)
    assert acertos >= 9, f"{acertos}/{len(perguntas)} no top 5:\n" + "\n".join(erros)


# Calibração do limite de recusa (s2-rag-juridico, tarefa 2.3), com o índice real.
FORA_DO_TEMA = [
    "qual a previsão do tempo para amanhã em Brasília?",
    "como faço um bolo de chocolate?",
    "quem ganhou o jogo do Flamengo ontem?",
]


class LLMQueNaoPodeSerChamado:
    def responder(self, mensagens):
        raise AssertionError("pergunta fora do tema não deveria chegar ao LLM")


@pytest.mark.parametrize("pergunta", FORA_DO_TEMA)
def test_pergunta_fora_do_tema_e_recusada_com_180_e_defensoria(indice, pergunta):
    r = resposta.responder(pergunta, indice, LLMQueNaoPodeSerChamado())
    assert r["recusada"] is True and r["citacoes"] == []
    assert "180" in r["resposta"] and "Defensoria Pública do DF" in r["resposta"]


def test_perguntas_das_personas_passam_do_limite(indice):
    # O limite não pode recusar as perguntas do teste rápido antes de chegar ao LLM.
    perguntas = [p["pergunta"] for p in yaml.safe_load(PERGUNTAS.read_text(encoding="utf-8"))["perguntas"]]
    for pergunta in perguntas:
        _, similaridade = indice.buscar(pergunta, k=1, eixos=resposta.EIXOS)[0]
        assert similaridade >= resposta.LIMITE_SIMILARIDADE, pergunta
