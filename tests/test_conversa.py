"""Testes em QuickJS de web/conversa.js e do cartão de benefício no chat (s4-orquestrador-agentes, tarefas 4.1 e 4.2)."""

import json
import re
from pathlib import Path

import pytest
import quickjs

from app.orquestrador import PedidoOrquestrar

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLOS = json.loads((Path(__file__).parent / "orquestrar_exemplos.json").read_text(encoding="utf-8"))["exemplos"]
POR_NOME = {e["nome"]: e for e in EXEMPLOS}
TEXTO_REGRAS_BENEFICIOS = (RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8")
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATA_BR = re.compile(r"^\d{2}/\d{2}/\d{4}$")

PERFIL_FICTICIO_COMPLETO = {
    "ra": "Ceilândia",
    "moradia": "Preciso sair de casa com urgência para me proteger",
    "renda": "Até R$ 600 por mês",
    "pessoas_casa": "3 pessoas",
    "filhos": "Sim, crianças de 0 a 6 anos",
    "idade": "65 anos ou mais",
    "estado_civil": "Separada recentemente / em processo de separação",
    "cadunico": "Sim, está atualizado (nos últimos 2 anos)",
    "inss": "Desempregada / sem renda própria",
    "medida_protetiva": "Sim, já tenho medida protetiva concedida pelo juiz",
}


def _coletar_textos(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _coletar_textos(v)
    elif isinstance(valor, list):
        for item in valor:
            yield from _coletar_textos(item)


@pytest.fixture(scope="module")
def js():
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "perfil.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "beneficios.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "conversa.js").read_text(encoding="utf-8"))
    contexto.eval(f"var REGRAS_BENEFICIOS = {TEXTO_REGRAS_BENEFICIOS};")
    return contexto


def montar_pedido(js, entrada, opcoes=None):
    if opcoes is None:
        expr = f"JSON.stringify(Conversa.montarPedido({json.dumps(entrada)}))"
    else:
        expr = f"JSON.stringify(Conversa.montarPedido({json.dumps(entrada)}, {json.dumps(opcoes)}))"
    return json.loads(js.eval(expr))


def para_blocos(js, resposta_servidor, opcoes=None):
    opcoes_js = json.dumps(opcoes or {})
    expr = (
        f"JSON.stringify(Conversa.paraBlocos({json.dumps(resposta_servidor)}, "
        f"Object.assign({{ regrasBeneficios: REGRAS_BENEFICIOS }}, {opcoes_js})))"
    )
    return json.loads(js.eval(expr))


# --- Tarefa 4.1: montarPedido e transformação das respostas de exemplo em blocos ----------


@pytest.mark.parametrize("exemplo", EXEMPLOS, ids=lambda e: e["nome"])
def test_montar_pedido_gera_apenas_os_tres_campos_do_contrato(js, exemplo):
    pedido_original = exemplo["pedido"]
    # Passa campos extras proibidos para garantir que montarPedido os descarte
    entrada_suja = {
        **pedido_original,
        "perfil": PERFIL_FICTICIO_COMPLETO,
        "historico": [{"papel": "usuaria", "texto": "oi"}],
        "respostasEspecificasBeneficios": {"deficiencia": "sim"},
        "respostasFonar": {"1": "sim_fogo"},
    }
    pedido = montar_pedido(js, entrada_suja)
    assert set(pedido.keys()) == {"texto", "alerta_visto", "ajudando"}
    assert pedido == pedido_original
    PedidoOrquestrar.model_validate(pedido)


def test_montar_pedido_com_argumentos_separados(js):
    pedido = montar_pedido(
        js,
        "  como peço medida protetiva?  ",
        {"alerta_visto": True, "ajudando": True, "perfil": {"ra": "Gama"}},
    )
    assert set(pedido.keys()) == {"texto", "alerta_visto", "ajudando"}
    assert pedido == {
        "texto": "como peço medida protetiva?",
        "alerta_visto": True,
        "ajudando": True,
    }


@pytest.mark.parametrize("exemplo", EXEMPLOS, ids=lambda e: e["nome"])
def test_para_blocos_cobre_todos_os_exemplos_do_contrato(js, exemplo):
    blocos = para_blocos(
        js,
        exemplo["resposta"],
        {"perfil": PERFIL_FICTICIO_COMPLETO, "ajudando": exemplo["pedido"]["ajudando"]},
    )
    assert isinstance(blocos, list) and len(blocos) >= 1
    for texto in _coletar_textos(blocos):
        assert "direito garantido" not in texto.lower()


def test_blocos_de_resposta_com_fontes_explicacao_e_fora_do_tema(js):
    # 1. Jurídico com citação
    blocos_jur = para_blocos(js, POR_NOME["juridico_por_regra"]["resposta"])
    assert len(blocos_jur) == 1
    bloco = blocos_jur[0]
    assert bloco["tipo"] == "resposta_com_fontes"
    assert bloco["agente"] == "juridico"
    assert bloco["recusada"] is False
    assert "Lei 11.340/2006, art. 19" in bloco["texto"]
    assert len(bloco["citacoes"]) == 1
    assert bloco["citacoes"][0]["texto_fonte"] == "Lei 11.340/2006, art. 19 · texto verificado em 03/11/2026"

    # 2. Explicação de benefício com citação e aviso de data
    blocos_exp = para_blocos(js, POR_NOME["beneficios_explicacao"]["resposta"])
    assert len(blocos_exp) == 1
    exp = blocos_exp[0]
    assert exp["tipo"] == "explicacao_beneficio"
    assert exp["agente"] == "beneficios"
    assert exp["aviso"] == "Valores e regras podem mudar por decreto. Norma consultada em 03/11/2026."
    assert exp["citacoes"][0]["citacao"] == "Lei Distrital 6.938/2021, art. 1º"

    # 3. Fora do tema
    blocos_fora = para_blocos(js, POR_NOME["fora_do_tema"]["resposta"])
    assert len(blocos_fora) == 1
    fora = blocos_fora[0]
    assert fora["tipo"] == "fora_do_tema"
    assert fora["recusada"] is True
    assert "180" in fora["texto"] and "Defensoria Pública do DF" in fora["texto"]

    # 4. Erro 503 de LLM indisponível
    blocos_erro = para_blocos(js, POR_NOME["llm_indisponivel"]["resposta"])
    assert len(blocos_erro) == 1
    assert blocos_erro[0]["tipo"] == "erro"
    assert "180" in blocos_erro[0]["texto"]


def test_blocos_de_alerta_triagem_sugestoes_e_excesso(js):
    # Alerta sem alerta_visto: mostra apenas o alerta de 190 com o botão "Continuar com minha pergunta"
    sem_visto = para_blocos(js, POR_NOME["alerta_sem_alerta_visto"]["resposta"])
    assert [b["tipo"] for b in sem_visto] == ["alerta_190"]
    assert sem_visto[0]["botao_continuar"] == "Continuar com minha pergunta"
    assert sem_visto[0]["telefone_emergencia"] == "190"

    # Alerta com alerta_visto: mantém a linha de 190 acima da resposta do agente
    com_visto = para_blocos(js, POR_NOME["alerta_com_alerta_visto"]["resposta"])
    assert [b["tipo"] for b in com_visto] == ["linha_190", "resposta_com_fontes"]
    assert "190" in com_visto[0]["texto"]
    assert "Lei 11.340/2006, art. 19" in com_visto[1]["texto"]

    # Oferta de triagem + sugestão quando há várias perguntas (triagem antes da ordem escrita)
    triagem_multi = para_blocos(js, POR_NOME["triagem_antes_da_ordem_escrita"]["resposta"])
    assert [b["tipo"] for b in triagem_multi] == ["oferta_triagem", "sugestoes"]
    assert triagem_multi[0]["acao_destino"] == "fonar"
    assert triagem_multi[1]["perguntas"] == ["Tenho direito ao Bolsa Família?"]

    # Duas perguntas: resposta jurídica + sugestão
    varias = para_blocos(js, POR_NOME["varias_perguntas"]["resposta"])
    assert [b["tipo"] for b in varias] == ["resposta_com_fontes", "sugestoes"]
    assert varias[1]["perguntas"] == ["Onde posso pedir medida protetiva no DF?"]

    # Excesso de perguntas (> 3): resposta + 2 sugestões + aviso de excesso
    excesso = para_blocos(js, POR_NOME["excesso_de_perguntas"]["resposta"])
    assert [b["tipo"] for b in excesso] == ["resposta_com_fontes", "sugestoes", "excesso"]
    assert len(excesso[1]["perguntas"]) == 2
    assert "separadamente" in excesso[2]["texto"]


# --- Tarefa 4.2: cartão de benefício com Beneficios.avaliar e o perfil --------------------


def test_cartao_beneficio_sem_perfil_convida_ao_formulario_com_190_e_180(js):
    for perfil_vazio in (None, {}, {"ra": "Ceilândia"}):
        blocos = para_blocos(js, POR_NOME["beneficios_direito"]["resposta"], {"perfil": perfil_vazio})
        assert len(blocos) == 1
        bloco = blocos[0]
        assert bloco["tipo"] == "convite_perfil"
        assert bloco["acao_destino"] == "screening"
        assert bloco["telefone_emergencia"] == "190"
        assert bloco["telefone_orientacao"] == "180"
        assert "190" in bloco["texto"] and "180" in bloco["texto"]
        assert bloco["cartoes"] == []


def test_cartao_beneficio_outro_orienta_cras_e_informa_os_quatro_beneficios(js):
    blocos = para_blocos(js, POR_NOME["beneficios_direito_outro"]["resposta"], {"perfil": PERFIL_FICTICIO_COMPLETO})
    assert len(blocos) == 1
    bloco = blocos[0]
    assert bloco["tipo"] == "beneficio_outro"
    assert bloco["beneficio"] == "outro"
    assert "quatro benefícios" in bloco["texto"]
    assert "CRAS" in bloco["texto"]
    assert "180" in bloco["texto"]


def test_cartao_beneficio_filtrado_e_todos_os_beneficios_seguem_contrato_comum(js):
    # Com benefício citado ("bolsa_familia"): retorna apenas o cartão do Bolsa Família
    blocos_bf = para_blocos(
        js,
        POR_NOME["beneficios_direito"]["resposta"],
        {"perfil": PERFIL_FICTICIO_COMPLETO},
    )
    assert len(blocos_bf) == 1
    bloco_bf = blocos_bf[0]
    assert bloco_bf["tipo"] == "cartao_beneficio"
    assert len(bloco_bf["cartoes"]) == 1
    cartao_bf = bloco_bf["cartoes"][0]
    assert cartao_bf["id"] == "bolsa_familia"
    assert cartao_bf["status"] == "provavel"
    assert cartao_bf["situacao"] == "Provável"
    assert cartao_bf["norma"] == "Lei 14.601/2023"
    assert cartao_bf["artigo"] == "art. 5º, II"
    assert DATA_ISO.fullmatch(cartao_bf["data_verificacao"])
    assert DATA_BR.fullmatch(cartao_bf["data"])

    # Sem benefício citado (null): retorna os 4 benefícios avaliados
    blocos_todos = para_blocos(
        js,
        POR_NOME["beneficios_direito_sem_beneficio"]["resposta"],
        {"perfil": PERFIL_FICTICIO_COMPLETO},
    )
    assert len(blocos_todos) == 1
    cartoes = blocos_todos[0]["cartoes"]
    assert [c["id"] for c in cartoes] == [
        "bolsa_familia",
        "bpc",
        "auxilio_aluguel",
        "aluguel_social_df",
    ]

    por_id = {c["id"]: c for c in cartoes}
    for c in cartoes:
        # Campos obrigatórios do contrato comum: situação, motivos, o que falta, onde pedir, norma, artigo, data, aviso
        assert isinstance(c["situacao"], str) and c["situacao"].strip()
        assert isinstance(c["motivos"], list) and len(c["motivos"]) >= 1
        assert isinstance(c["falta"], list)
        assert isinstance(c["onde_pedir"], str) and c["onde_pedir"].strip()
        assert isinstance(c["norma"], str) and c["norma"].strip()
        assert isinstance(c["artigo"], str) and c["artigo"].strip()
        assert DATA_ISO.fullmatch(c["data_verificacao"])
        assert DATA_BR.fullmatch(c["data"])
        assert (
            isinstance(c["aviso"], str)
            and "a concessão depende" in c["aviso"].lower()
            and any(termo in c["aviso"].lower() for termo in ("órgão", "inss", "juiz", "secretaria"))
        )

    # Auxílio-aluguel da Lei Maria da Penha é sempre "depende de decisão judicial"
    aux = por_id["auxilio_aluguel"]
    assert aux["status"] == "depende_decisao_judicial"
    assert aux["situacao"] == "Depende de decisão judicial"
    assert aux["norma"] == "Lei 11.340/2006"
    assert aux["artigo"] == "art. 23, VI (incluído pela Lei 14.674/2023)"

    # Como as perguntas específicas (BO, acompanhamento psicossocial, necessidade de moradia) não foram
    # respondidas no chat, o Aluguel Social DF fica em "faltam_informacoes" e ativa o botão para a tela Benefícios
    aluguel_df = por_id["aluguel_social_df"]
    assert aluguel_df["status"] == "faltam_informacoes"
    assert blocos_todos[0]["precisa_especificas"] is True
    assert blocos_todos[0]["acao_destino"] == "benefits"

    # Nenhum texto usa "direito garantido"
    codigo_conversa = (RAIZ / "web" / "conversa.js").read_text(encoding="utf-8")
    assert "direito garantido" not in codigo_conversa.lower()
    for texto in _coletar_textos(blocos_todos):
        assert "direito garantido" not in texto.lower()
