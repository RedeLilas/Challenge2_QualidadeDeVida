from pathlib import Path

import pytest
import yaml

from app.rag import resposta

PERGUNTAS = Path(__file__).parent / "perguntas_juridicas.yaml"
DESENVOLVIMENTO = Path(__file__).parents[1] / "avaliacao" / "conjuntos" / "desenvolvimento.yaml"
DESENVOLVIMENTO_BENEFICIOS = (
    Path(__file__).parents[1] / "avaliacao" / "conjuntos" / "s4" / "desenvolvimento_beneficios.yaml"
)

NORMAS_POR_PROGRAMA = {
    "bolsa_familia": {"Lei 14.601/2023"},
    "bpc": {"Lei 8.742/1993 (LOAS)"},
    "prato_cheio": {"Lei Distrital 7.009/2021", "Decreto Distrital 42.873/2021"},
    "cartao_gas": {"Lei Distrital 6.938/2021", "Decreto Distrital 42.376/2021"},
    "aluguel_social_df": {
        "Lei Distrital 6.623/2020",
        "Decreto Distrital 45.989/2024",
        "Portaria SMDF 49/2026",
    },
    "beneficios_eventuais": {
        "Lei 8.742/1993 (LOAS)",
        "Lei Distrital 5.165/2013",
        "Decreto Distrital 35.191/2014",
    },
}


@pytest.fixture(scope="module")
def indice(indice_real):
    return indice_real


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


def test_perguntas_de_desenvolvimento_do_tema_passam_do_limite(indice):
    # Recalibração (s3-base-legal-ampliada, tarefa 3.2): o limite não pode recusar nenhuma das 15 perguntas
    # de desenvolvimento do tema antes de chegar ao LLM. O conjunto oficial nunca entra na calibração.
    perguntas = yaml.safe_load(DESENVOLVIMENTO.read_text(encoding="utf-8"))["perguntas"]
    assert len(perguntas) == 15
    recusadas = []
    for p in perguntas:
        _, similaridade = indice.buscar(p["pergunta"], k=1, eixos=resposta.EIXOS)[0]
        if similaridade < resposta.LIMITE_SIMILARIDADE:
            recusadas.append(f"{p['id']}: {similaridade:.4f}")
    assert recusadas == []


# --- s4-rag-beneficios, tarefa 3.2: recuperação por benefício no top 5 ---------------------------


def _conferir_recuperacao_beneficio(
    indice,
    programa: str,
    perguntas: list[str],
    normas_esperadas: set[str] | None = None,
) -> None:
    """Falha apontando o benefício e os trechos recuperados se a norma não vier no top 5."""
    esperadas = NORMAS_POR_PROGRAMA[programa] if normas_esperadas is None else normas_esperadas
    erros = []
    for pergunta in perguntas:
        consulta = resposta.expandir_siglas_beneficios(pergunta)
        resultados = indice.buscar(consulta, k=5, eixos=resposta.EIXOS_BENEFICIOS)
        leis_recuperadas = {t["lei"] for t, _ in resultados}
        if not leis_recuperadas & esperadas:
            trechos_recuperados = [t["citacao"] for t, _ in resultados]
            erros.append(
                f"benefício={programa!r} ({pergunta!r}): esperado {sorted(esperadas)}, "
                f"recuperado {trechos_recuperados}"
            )
    assert not erros, "\n".join(erros)


@pytest.mark.parametrize("programa", sorted(NORMAS_POR_PROGRAMA))
def test_recuperacao_por_beneficio_top5(indice, programa):
    dados = yaml.safe_load(DESENVOLVIMENTO_BENEFICIOS.read_text(encoding="utf-8"))
    assert set(dados["programas"]) == set(NORMAS_POR_PROGRAMA)
    itens = [p for p in dados["perguntas"] if p["programa"] == programa]
    assert itens, f"Nenhuma pergunta ativa para o programa {programa!r}"
    for item in itens:
        normas_do_item = {n.split(", art.")[0] for n in item["normas_aceitas"]}
        assert normas_do_item <= NORMAS_POR_PROGRAMA[programa]
        _conferir_recuperacao_beneficio(indice, programa, [item["pergunta"]], normas_do_item)


def test_aluguel_social_df_recupera_norma_no_top5(indice):
    # Cenário explícito da spec (s4-rag-beneficios/specs/beneficios/spec.md).
    _conferir_recuperacao_beneficio(
        indice,
        "aluguel_social_df",
        ["como funciona o aluguel social do DF?"],
    )


def test_beneficio_sem_norma_no_top5_falha_apontando_beneficio_e_trechos():
    class IndiceSemNormaDoBeneficio:
        def buscar(self, pergunta, k=5, eixos=None):
            return [
                ({"lei": "Lei 14.601/2023", "citacao": "Lei 14.601/2023, art. 5º"}, 0.85),
                ({"lei": "Decreto Distrital 42.376/2021", "citacao": "Decreto Distrital 42.376/2021, art. 2º"}, 0.84),
            ]

    with pytest.raises(AssertionError) as erro:
        _conferir_recuperacao_beneficio(
            IndiceSemNormaDoBeneficio(),
            "aluguel_social_df",
            ["como funciona o aluguel social do DF?"],
        )
    mensagem = str(erro.value)
    assert "aluguel_social_df" in mensagem
    assert "Lei 14.601/2023, art. 5º" in mensagem
    assert "Decreto Distrital 42.376/2021, art. 2º" in mensagem


def test_recuperacao_bpc_sigla_curta_bd_005(indice):
    # Com a expansão de siglas na busca de benefícios ("bpc" -> "benefício de prestação continuada (bpc)"),
    # bd-005 recupera a Lei 8.742/1993 (LOAS) no top 5 (s4-rag-beneficios, tarefa 3.3).
    _conferir_recuperacao_beneficio(indice, "bpc", ["o que é o bpc?"])


# --- s4-rag-beneficios, tarefa 3.3: calibração de LIMITE_BENEFICIOS e recusa das extras -----------


def test_perguntas_de_desenvolvimento_de_beneficios_passam_do_limite(indice):
    dados = yaml.safe_load(DESENVOLVIMENTO_BENEFICIOS.read_text(encoding="utf-8"))
    perguntas = dados["perguntas"]
    assert len(perguntas) == 22
    recusadas = []
    for p in perguntas:
        consulta = resposta.expandir_siglas_beneficios(p["pergunta"])
        _, similaridade = indice.buscar(consulta, k=1, eixos=resposta.EIXOS_BENEFICIOS)[0]
        if similaridade < resposta.LIMITE_BENEFICIOS:
            recusadas.append(f"{p['id']}: {similaridade:.4f}")
    assert recusadas == []


def test_extras_quase_do_tema_sao_recusadas_pelo_limite_ou_pela_citacao(indice):
    # As 8 extras quase do tema (imposto de renda, FGTS, seguro-desemprego e aposentadoria) têm
    # vocabulário próximo ao das normas de benefícios (0,8123 a 0,8629): bd-x04 fica abaixo de
    # LIMITE_BENEFICIOS (0,815) e é barrada antes do LLM; as demais são barradas pela verificação
    # de citação (sem citação, norma fora da base ou artigo sem norma em múltiplos diplomas).
    dados = yaml.safe_load(DESENVOLVIMENTO_BENEFICIOS.read_text(encoding="utf-8"))
    extras = dados["extras"]
    assert len(extras) == 8

    class LLMExtraForaDaBase:
        def __init__(self, texto: str):
            self.texto = texto
            self.chamado = False

        def responder(self, mensagens):
            self.chamado = True
            return self.texto

    respostas_llm = [
        "Não sei explicar esse benefício com segurança a partir das normas disponíveis.",
        "Essa regra está na legislação federal específica (Lei 8.036/1990, art. 20).",
        "O requisito está previsto no art. 3º.",
    ]

    barradas_pelo_limite = []
    for extra in extras:
        pergunta = extra["pergunta"]
        _, sim = indice.buscar(
            resposta.expandir_siglas_beneficios(pergunta), k=1, eixos=resposta.EIXOS_BENEFICIOS
        )[0]
        if sim < resposta.LIMITE_BENEFICIOS:
            barradas_pelo_limite.append(extra["id"])
            r = resposta.explicar_beneficio(pergunta, indice, LLMQueNaoPodeSerChamado())
            assert r == {
                "resposta": resposta.RECUSA_BENEFICIOS,
                "citacoes": [],
                "recusada": True,
                "aviso": None,
            }
        else:
            for saida in respostas_llm:
                llm_falso = LLMExtraForaDaBase(saida)
                r = resposta.explicar_beneficio(pergunta, indice, llm_falso)
                assert llm_falso.chamado is True
                assert r == {
                    "resposta": resposta.RECUSA_BENEFICIOS,
                    "citacoes": [],
                    "recusada": True,
                    "aviso": None,
                }

    assert barradas_pelo_limite == ["bd-x04"]


def test_pergunta_aluguel_maria_da_penha_contra_limite_juridico(indice):
    # bd-j01 ("como funciona o aluguel da maria da penha?"): confere no eixo jurídico contra o 0,81,
    # sem alterar LIMITE_SIMILARIDADE nem o /juridico.
    dados = yaml.safe_load(DESENVOLVIMENTO_BENEFICIOS.read_text(encoding="utf-8"))
    item = dados["juridico"][0]
    assert item["id"] == "bd-j01" and item["eixo_esperado"] == "juridico"
    resultados = indice.buscar(item["pergunta"], k=5, eixos=resposta.EIXOS)
    assert resultados[0][1] < resposta.LIMITE_SIMILARIDADE
    assert ("lei-11340-2006", "23") in [(t["norma_id"], t["artigo"]) for t, _ in resultados]
