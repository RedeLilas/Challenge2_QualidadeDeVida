"""Classificação pelo LLM, reserva, separação e ordem (s4-orquestrador-agentes, tarefas 2.3 e 2.4).

Só LLM falso: nenhum teste chama um provedor de verdade.
"""
import json
from pathlib import Path

import pytest

from app.llm import LLMIndisponivel
from app.orquestrador import INSTRUCOES_CLASSIFICACAO, RAS_DO_SITE, classificar

EXEMPLOS = {
    e["nome"]: e
    for e in json.loads((Path(__file__).parent / "orquestrar_exemplos.json").read_text(encoding="utf-8"))["exemplos"]
}

# Nenhum destes textos é decidido pela regra (tests/test_roteamento_regra.py): todos chegam ao LLM.
SEM_REGRA = "ele fica olhando meu celular escondido, pode isso?"


class LLMFalso:
    def __init__(self, saida="", erro=None):
        self.saida, self.erro, self.chamadas = saida, erro, []

    def responder(self, mensagens, temperatura=0.2):
        self.chamadas.append({"mensagens": mensagens, "temperatura": temperatura})
        if self.erro:
            raise self.erro
        return self.saida


class LLMQueNaoPodeSerChamado:
    def responder(self, mensagens, temperatura=0.2):
        raise AssertionError("a regra decide sozinha: o LLM não deveria ser chamado")


def saida(*perguntas):
    itens = []
    for p in perguntas:
        item = {"agente": "juridico", "tipo": None, "pergunta": "?", "beneficio": None, "ra": None,
                "violencia_sexual_recente": None}  # fmt: skip
        item.update(p)
        itens.append(item)
    return json.dumps({"perguntas": itens}, ensure_ascii=False)


# --- 2.3: classificação pelo LLM e reserva ------------------------------------------------------


def test_llm_classifica_com_temperatura_zero_e_lista_fechada():
    llm = LLMFalso(saida({"agente": "juridico", "pergunta": "Ele pode olhar meu celular escondido?"}))
    resultado = classificar(SEM_REGRA, llm)

    assert resultado.decidido_por == "llm"
    assert resultado.decisao.agente == "juridico"
    [chamada] = llm.chamadas
    assert chamada["temperatura"] == 0
    sistema, usuaria = chamada["mensagens"]
    assert sistema == {"role": "system", "content": INSTRUCOES_CLASSIFICACAO}
    assert SEM_REGRA in usuaria["content"]
    for agente in ("juridico", "beneficios", "triagem", "rede", "fora_do_tema"):
        assert f"- {agente}:" in INSTRUCOES_CLASSIFICACAO
    for ra in RAS_DO_SITE:
        assert f'"{ra}"' in INSTRUCOES_CLASSIFICACAO


def test_regra_decide_sem_chamar_o_llm():
    resultado = classificar("onde fica a delegacia da mulher?", LLMQueNaoPodeSerChamado())
    assert (resultado.decidido_por, resultado.decisao.agente) == ("regra", "rede")
    assert resultado.pergunta == "onde fica a delegacia da mulher?"


def test_saida_com_cerca_de_codigo_e_aceita():
    llm = LLMFalso("```json\n" + saida({"agente": "fora_do_tema", "pergunta": "Vai chover amanhã?"}) + "\n```")
    assert classificar("vai chover amanha", llm).decisao.agente == "fora_do_tema"


@pytest.mark.parametrize(
    "saida_llm",
    [
        "não é JSON",
        '{"perguntas": [{"agente": "juridico", "pergunta": "?"',  # JSON quebrado
        '{"perguntas": []}',
        '{"resposta": "medida protetiva é..."}',
        saida({"agente": "saude"}),  # agente fora da lista fechada
        saida({"agente": "beneficios", "tipo": "talvez"}),  # tipo inválido
        saida({"agente": "beneficios", "tipo": None}),  # benefícios sem tipo
        saida({"agente": "juridico", "tipo": "direito"}),  # tipo fora de benefícios
        saida({"agente": "rede", "pergunta": ""}),  # pergunta vazia
    ],
)
def test_saida_invalida_vai_para_a_reserva_no_juridico(saida_llm):
    resultado = classificar(SEM_REGRA, LLMFalso(saida_llm))
    assert resultado.decidido_por == "reserva"
    assert resultado.decisao.agente == "juridico"
    assert resultado.pergunta == SEM_REGRA
    assert resultado.outras_perguntas == [] and not resultado.excedeu


def test_llm_indisponivel_vai_para_a_reserva_no_juridico():
    resultado = classificar(SEM_REGRA, LLMFalso(erro=LLMIndisponivel("APITimeoutError")))
    assert (resultado.decidido_por, resultado.decisao.agente) == ("reserva", "juridico")


def test_reserva_mantem_os_campos_do_texto():
    texto = "moro em ceilandia e ele fica olhando meu celular escondido, pode isso?"
    resultado = classificar(texto, LLMFalso("não é JSON"))
    assert resultado.decidido_por == "reserva"
    assert resultado.decisao.campos.ra == "Ceilândia"


def test_campos_fora_do_contrato_viram_nulos():
    llm = LLMFalso(saida({"agente": "rede", "pergunta": "Onde tem delegacia?", "ra": "Sol Nascente",
                          "beneficio": "cartao_gas", "violencia_sexual_recente": True}))  # fmt: skip
    resultado = classificar("aconteceu de novo ontem, moro no sol nascente, pra quem eu ligo?", llm)
    assert resultado.decidido_por == "llm"
    campos = resultado.decisao.campos
    assert (campos.ra, campos.beneficio, campos.violencia_sexual_recente) == (None, None, True)


# --- 2.4: separação e ordem ---------------------------------------------------------------------


def test_uma_pergunta_usa_o_texto_original():
    llm = LLMFalso(saida({"agente": "juridico", "pergunta": "O agressor pode olhar o celular dela escondido?"}))
    resultado = classificar(SEM_REGRA, llm)
    assert resultado.pergunta == SEM_REGRA
    assert resultado.outras_perguntas == [] and not resultado.excedeu


def test_duas_perguntas_responde_a_primeira_e_sugere_a_outra():
    texto = "o que é medida protetiva e onde eu peço ela?"
    llm = LLMFalso(saida(
        {"agente": "juridico", "pergunta": "O que é medida protetiva?"},
        {"agente": "juridico", "pergunta": "Onde posso pedir medida protetiva no DF?"},
    ))  # fmt: skip
    resultado = classificar(texto, llm)
    assert resultado.decidido_por == "llm"
    assert resultado.pergunta == "O que é medida protetiva?"
    assert resultado.outras_perguntas == ["Onde posso pedir medida protetiva no DF?"]
    assert not resultado.excedeu
    # Mesmo resultado do exemplo do contrato que o navegador usa.
    exemplo = EXEMPLOS["varias_perguntas"]["resposta"]
    assert (resultado.decisao.agente, resultado.outras_perguntas) == (exemplo["agente"], exemplo["outras_perguntas"])


def test_triagem_vem_antes_da_ordem_escrita():
    texto = "tenho direito ao bolsa família? e também queria saber se corro perigo"
    llm = LLMFalso(saida(
        {"agente": "beneficios", "tipo": "direito", "pergunta": "Tenho direito ao Bolsa Família?",
         "beneficio": "bolsa_familia"},
        {"agente": "triagem", "pergunta": "Eu corro perigo?"},
    ))  # fmt: skip
    resultado = classificar(texto, llm)
    assert resultado.decisao.agente == "triagem"
    # Os campos e o tipo são os da pergunta respondida, não os da sugerida.
    assert resultado.decisao.tipo is None and resultado.decisao.campos.beneficio is None
    assert resultado.outras_perguntas == ["Tenho direito ao Bolsa Família?"]
    exemplo = EXEMPLOS["triagem_antes_da_ordem_escrita"]["resposta"]
    assert (resultado.decisao.agente, resultado.outras_perguntas) == (exemplo["agente"], exemplo["outras_perguntas"])


def test_ordem_escrita_sem_triagem():
    llm = LLMFalso(saida(
        {"agente": "juridico", "pergunta": "Como peço medida protetiva?"},
        {"agente": "rede", "pergunta": "Onde fica a delegacia da mulher?"},
    ))  # fmt: skip
    resultado = classificar("como peço medida protetiva? onde fica a delegacia?", llm)
    assert resultado.decisao.agente == "juridico"
    assert resultado.outras_perguntas == ["Onde fica a delegacia da mulher?"]


def test_quatro_perguntas_excedem():
    texto = "como peço medida protetiva? tenho direito ao bpc? onde fica o cras? e o que é violência psicológica?"
    llm = LLMFalso(saida(
        {"agente": "juridico", "pergunta": "Como peço medida protetiva?"},
        {"agente": "beneficios", "tipo": "direito", "pergunta": "Tenho direito ao BPC?", "beneficio": "bpc"},
        {"agente": "rede", "pergunta": "Onde fica o CRAS?"},
        {"agente": "juridico", "pergunta": "O que é violência psicológica?"},
    ))  # fmt: skip
    resultado = classificar(texto, llm)
    assert resultado.excedeu
    assert resultado.pergunta == "Como peço medida protetiva?"
    assert resultado.outras_perguntas == ["Tenho direito ao BPC?", "Onde fica o CRAS?"]
    exemplo = EXEMPLOS["excesso_de_perguntas"]["resposta"]
    assert (resultado.outras_perguntas, resultado.excedeu) == (exemplo["outras_perguntas"], exemplo["excedeu"])


def test_triagem_no_fim_de_quatro_perguntas_vem_primeiro():
    llm = LLMFalso(saida(
        {"agente": "juridico", "pergunta": "Como peço medida protetiva?"},
        {"agente": "rede", "pergunta": "Onde fica o CRAS?"},
        {"agente": "juridico", "pergunta": "O que é violência psicológica?"},
        {"agente": "triagem", "pergunta": "Eu corro perigo?"},
    ))  # fmt: skip
    resultado = classificar("varias perguntas? sim? mais? e corro perigo?", llm)
    assert resultado.decisao.agente == "triagem"
    assert resultado.outras_perguntas == ["Como peço medida protetiva?", "Onde fica o CRAS?"]
    assert resultado.excedeu


# --- Fechamento da S4 (#84): "direito" só para benefício com regra ou com marca de "tenho direito?" -----


@pytest.mark.parametrize(
    "texto, beneficio",
    [
        ("o governo do df ajuda quando nasce um bebe?", None),
        ("tem ajuda pra pagar enterro?", "outro"),
    ],
)
def test_existe_ajuda_vira_explicacao(texto, beneficio):
    # O DeepSeek classificou estas perguntas como "direito" no teste manual de 19/11.
    llm = LLMFalso(saida({"agente": "beneficios", "tipo": "direito", "pergunta": texto, "beneficio": beneficio}))
    resultado = classificar(texto, llm)
    assert resultado.decidido_por == "llm"
    assert (resultado.decisao.agente, resultado.decisao.tipo) == ("beneficios", "explicacao")


@pytest.mark.parametrize(
    "texto, beneficio",
    [
        # Benefício com regra: os cartões respondem à pergunta, mesmo sem marca de "tenho direito?".
        ("minha mae tem 70 anos? como fica o bpc dela?", "bpc"),
        # Marca de "tenho direito?": os cartões de todos os benefícios respondem.
        ("moro com 2 filhos e a renda é baixa, recebo alguma coisa?", None),
        ("ganho pouco, sera que tenho direito a alguma ajuda?", None),
    ],
)
def test_direito_continua_quando_ha_regra_ou_marca(texto, beneficio):
    llm = LLMFalso(saida({"agente": "beneficios", "tipo": "direito", "pergunta": texto, "beneficio": beneficio}))
    resultado = classificar(texto, llm)
    assert resultado.decidido_por == "llm"
    assert (resultado.decisao.agente, resultado.decisao.tipo) == ("beneficios", "direito")


def test_instrucao_traz_exemplos_dos_dois_tipos():
    assert "\"tenho direito ao bolsa família?\" é direito" in INSTRUCOES_CLASSIFICACAO
    assert "\"o governo ajuda quando nasce um bebê?\"" in INSTRUCOES_CLASSIFICACAO
