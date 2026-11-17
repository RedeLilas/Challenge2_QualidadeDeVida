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


# --- Tarefa 4.6: modo "ajudando outra pessoa" em terceira pessoa nos agentes do navegador --


def test_modo_ajudando_envia_flag_no_pedido_e_usa_terceira_pessoa_nos_agentes_locais(js):
    pedido_ajudando = montar_pedido(js, "como posso ajudar minha amiga?", {"ajudando": True})
    assert pedido_ajudando == {"texto": "como posso ajudar minha amiga?", "alerta_visto": False, "ajudando": True}

    pedido_normal = montar_pedido(js, "como posso ajudar minha amiga?", {"ajudando": False})
    assert pedido_normal["ajudando"] is False

    # 1. Benefícios sem perfil: convite em 3ª pessoa vs 2ª pessoa
    sem_perfil_ajudando = para_blocos(
        js, POR_NOME["beneficios_direito"]["resposta"], {"perfil": {}, "ajudando": True}
    )[0]
    sem_perfil_normal = para_blocos(
        js, POR_NOME["beneficios_direito"]["resposta"], {"perfil": {}, "ajudando": False}
    )[0]
    assert sem_perfil_ajudando["ajudando"] is True
    assert "pessoa que você está ajudando" in sem_perfil_ajudando["texto"]
    assert "se ela estiver em perigo" in sem_perfil_ajudando["texto"].lower()
    assert "pessoa que você está ajudando" not in sem_perfil_normal["texto"]

    # 2. Benefícios com "outro": orientação ao CRAS em 3ª pessoa
    outro_ajudando = para_blocos(
        js, POR_NOME["beneficios_direito_outro"]["resposta"], {"perfil": PERFIL_FICTICIO_COMPLETO, "ajudando": True}
    )[0]
    assert "pessoa que você está ajudando" in outro_ajudando["texto"]
    assert "oriente-a" in outro_ajudando["texto"].lower()

    # 3. Benefícios com perfil preenchido: introdução em 3ª pessoa
    cartao_ajudando = para_blocos(
        js, POR_NOME["beneficios_direito"]["resposta"], {"perfil": PERFIL_FICTICIO_COMPLETO, "ajudando": True}
    )[0]
    assert "pessoa que você está ajudando" in cartao_ajudando["texto"]

    # 4. Triagem: oferta da avaliação de risco em 3ª pessoa
    triagem_ajudando = para_blocos(
        js, POR_NOME["triagem"]["resposta"], {"ajudando": True}
    )[0]
    triagem_normal = para_blocos(
        js, POR_NOME["triagem"]["resposta"], {"ajudando": False}
    )[0]
    assert "pessoa que está ajudando" in triagem_ajudando["texto"]
    assert "informe o endereço dela" in triagem_ajudando["texto"]
    assert "pessoa que está ajudando" not in triagem_normal["texto"]

    # 5. Rede (com violência sexual recente): texto de introdução e de saúde em 3ª pessoa
    rede_ajudando = para_blocos(
        js, POR_NOME["rede_violencia_sexual"]["resposta"], {"ajudando": True}
    )[0]
    assert "pessoa que você está ajudando" in rede_ajudando["texto"]
    assert "apoie-a" in rede_ajudando["texto_saude"].lower()


# --- Tarefa 4.3: lista curta de rede na conversa (com e sem Rede.ordenar e sem RA) --------

SERVICOS_FICTICIOS = [
    {
        "nome": "CEAM 102 Sul",
        "tipo": "CEAM",
        "ra": "Plano Piloto",
        "endereco": "Estação 102 Sul",
        "cep": "70330-000",
        "telefone": "(61) 3224-0943",
        "horario": "Segunda a sexta-feira, das 8h às 18h",
        "fonte_url": "https://www.mulher.df.gov.br/ceam",
        "data_verificacao": "2026-11-05",
    },
    {
        "nome": "DEAM I",
        "tipo": "DEAM",
        "ra": "Plano Piloto",
        "endereco": "EQS 204/205",
        "cep": "70234-400",
        "telefone": "(61) 3207-6172",
        "horario": "24 horas, todos os dias",
        "fonte_url": "https://www.pcdf.df.gov.br/deam",
        "data_verificacao": "2026-11-05",
    },
    {
        "nome": "CEAM Ceilândia",
        "tipo": "CEAM",
        "ra": "Ceilândia",
        "endereco": "QNM 02",
        "cep": "72210-020",
        "telefone": "(61) 3371-4923",
        "horario": "Segunda a sexta-feira, das 8h às 18h",
        "fonte_url": "https://www.mulher.df.gov.br/ceam",
        "data_verificacao": "2026-11-05",
    },
    {
        "nome": "Casa da Mulher Brasileira de Ceilândia",
        "tipo": "CMB",
        "ra": "Ceilândia",
        "endereco": "CNM 1, Bloco I, Lote 3",
        "cep": "72215-110",
        "telefone": "(61) 3181-1474",
        "horario": "24 horas, todos os dias",
        "fonte_url": "https://www.mulher.df.gov.br/cmb",
        "data_verificacao": "2026-11-05",
    },
    {
        "nome": "CRAS Sol Nascente",
        "tipo": "CRAS",
        "ra": "Sol Nascente/Pôr do Sol",
        "endereco": "Quadra 100",
        "cep": "72236-800",
        "telefone": "(61) 3773-7000",
        "horario": "Segunda a sexta-feira, das 8h às 18h",
        "fonte_url": "https://www.sedes.df.gov.br/unidades/",
        "data_verificacao": "2026-11-17",
    },
    {
        "nome": "CEPAV Ceilândia",
        "tipo": "Saúde",
        "ra": "Ceilândia",
        "endereco": "Hospital Regional de Ceilândia",
        "cep": "72220-901",
        "telefone": "(61) 2017-2000",
        "horario": "Segunda a sexta-feira, das 8h às 18h",
        "fonte_url": "https://cnes.datasus.gov.br/",
        "data_verificacao": "2026-11-17",
    },
]


def test_lista_curta_de_rede_sem_rede_js_ordena_por_mesma_ra_e_depois_24h_e_sem_ra(js):
    # O fixture `js` não carrega web/rede.js: testa o fallback interno de Conversa (mesma RA e depois plantões 24h)
    assert js.eval("typeof Rede") == "undefined"

    # 1. Com campos.ra = "Ceilândia" (rede_com_ra): prioriza Ceilândia (24h primeiro) e limita a 3 serviços
    bloco_ceilandia = para_blocos(
        js,
        POR_NOME["rede_com_ra"]["resposta"],
        {"servicos": SERVICOS_FICTICIOS, "perfil": {"ra": "Plano Piloto"}},
    )[0]
    assert bloco_ceilandia["tipo"] == "rede_atendimento"
    assert bloco_ceilandia["ra"] == "Ceilândia"
    assert bloco_ceilandia["acao_destino"] == "places"
    assert bloco_ceilandia["rotulo_acao"]
    assert len(bloco_ceilandia["servicos"]) == 3
    assert [s["nome"] for s in bloco_ceilandia["servicos"]] == [
        "Casa da Mulher Brasileira de Ceilândia",
        "CEAM Ceilândia",
        "CEPAV Ceilândia",
    ]
    for s in bloco_ceilandia["servicos"]:
        assert s["fonte"] and s["fonte_url"].startswith("https://")
        assert DATA_ISO.fullmatch(s["data_verificacao"])
        assert DATA_BR.fullmatch(s["data_formatada"])
        assert s["recomendacao"] == "Confirme por telefone antes de ir"

    # 2. Sem campos.ra, mas com RA no perfil ("Plano Piloto"): usa a RA do perfil e depois 24h de outra RA
    resposta_sem_ra = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    resposta_sem_ra["campos"]["ra"] = None
    bloco_perfil = para_blocos(
        js,
        resposta_sem_ra,
        {"servicos": SERVICOS_FICTICIOS, "perfil": {"ra": "Plano Piloto"}},
    )[0]
    assert bloco_perfil["ra"] == "Plano Piloto"
    assert [s["nome"] for s in bloco_perfil["servicos"]] == [
        "DEAM I",
        "CEAM 102 Sul",
        "Casa da Mulher Brasileira de Ceilândia",
    ]

    # 3. Ausência de RA (nem no texto nem no perfil): não exige perfil e traz os plantões 24h primeiro
    bloco_sem_ra = para_blocos(
        js,
        resposta_sem_ra,
        {"servicos": SERVICOS_FICTICIOS, "perfil": {}},
    )[0]
    assert bloco_sem_ra["ra"] is None
    assert len(bloco_sem_ra["servicos"]) == 3
    assert [s["nome"] for s in bloco_sem_ra["servicos"][:2]] == [
        "DEAM I",
        "Casa da Mulher Brasileira de Ceilândia",
    ]


def test_lista_curta_de_rede_usa_rede_ordenar_quando_web_rede_js_esta_presente():
    # Carrega web/rede.js junto com web/conversa.js para testar a delegação a Rede.ordenar e Rede.textoSaude
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "perfil.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "beneficios.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "rede.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "conversa.js").read_text(encoding="utf-8"))
    contexto.eval(f"var REGRAS_BENEFICIOS = {TEXTO_REGRAS_BENEFICIOS};")

    # 1. RA "Samambaia" (sem unidade direta em SERVICOS_FICTICIOS): Rede.ordenar traz a vizinha Ceilândia
    # (incluindo Sol Nascente/Pôr do Sol, que ordena como Ceilândia) antes de Plano Piloto
    resposta_samambaia = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    resposta_samambaia["campos"]["ra"] = "Samambaia"
    bloco_vizinha = para_blocos(
        contexto,
        resposta_samambaia,
        {"servicos": SERVICOS_FICTICIOS, "perfil": {}},
    )[0]
    assert bloco_vizinha["ra"] == "Samambaia"
    assert [s["nome"] for s in bloco_vizinha["servicos"]] == [
        "Casa da Mulher Brasileira de Ceilândia",
        "CEAM Ceilândia",
        "CRAS Sol Nascente",
    ]

    # 2. Com violencia_sexual_recente = true: Rede.ordenar coloca Saúde no topo e Rede.textoSaude cita a Lei 12.845/2013
    bloco_sexual = para_blocos(
        contexto,
        POR_NOME["rede_violencia_sexual"]["resposta"],
        {"servicos": SERVICOS_FICTICIOS, "perfil": {"ra": "Plano Piloto"}},
    )[0]
    assert bloco_sexual["violencia_sexual_recente"] is True
    assert "Lei 12.845/2013" in bloco_sexual["texto_saude"]
    assert bloco_sexual["servicos"][0]["nome"] == "CEPAV Ceilândia"
    assert bloco_sexual["servicos"][0]["tipo"] == "Saúde"

    # 3. Sem RA com Rede.ordenar presente: plantões 24h primeiro e botão para a lista completa
    resposta_sem_ra = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    resposta_sem_ra["campos"]["ra"] = None
    bloco_sem_ra = para_blocos(
        contexto,
        resposta_sem_ra,
        {"servicos": SERVICOS_FICTICIOS, "perfil": {"ra": "Prefiro não informar"}},
    )[0]
    assert bloco_sem_ra["ra"] is None
    assert bloco_sem_ra["acao_destino"] == "places"
    assert [s["nome"] for s in bloco_sem_ra["servicos"][:2]] == [
        "DEAM I",
        "Casa da Mulher Brasileira de Ceilândia",
    ]


def test_filtro_por_tipo_de_servico_na_pergunta():
    # Carrega web/rede.js junto com web/conversa.js
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "perfil.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "beneficios.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "rede.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "conversa.js").read_text(encoding="utf-8"))

    servicos_com_defensoria = SERVICOS_FICTICIOS + [
        {
            "nome": "Defensoria Pública de Ceilândia",
            "tipo": "Defensoria",
            "ra": "Ceilândia",
            "endereco": "Fórum de Ceilândia",
            "cep": "72210-000",
            "telefone": "(61) 3103-0000",
            "horario": "Segunda a sexta-feira, das 12h às 19h",
            "fonte_url": "https://www.defensoria.df.gov.br/",
            "data_verificacao": "2026-11-17",
        }
    ]

    # 1. Pergunta com "cras" filtra serviços do tipo CRAS
    resp_cras = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    bloco_cras = para_blocos(
        contexto,
        resp_cras,
        {"servicos": servicos_com_defensoria, "perfil": {}, "pergunta": "tem cras na ceilandia?"},
    )[0]
    assert bloco_cras["tipo_servico"] == "CRAS"
    assert len(bloco_cras["servicos"]) == 1
    assert bloco_cras["servicos"][0]["tipo"] == "CRAS"
    assert bloco_cras["servicos"][0]["nome"] == "CRAS Sol Nascente"

    # 2. Pergunta com "defensoria" sem RA
    resp_def = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    resp_def["campos"]["ra"] = None
    bloco_def = para_blocos(
        contexto,
        resp_def,
        {"servicos": servicos_com_defensoria, "perfil": {}, "pergunta": "onde acho a defensoria?"},
    )[0]
    assert bloco_def["tipo_servico"] == "Defensoria"
    assert len(bloco_def["servicos"]) == 1
    assert bloco_def["servicos"][0]["tipo"] == "Defensoria"
    assert bloco_def["servicos"][0]["nome"] == "Defensoria Pública de Ceilândia"

    # 3. Pergunta com "delegacia" ou "deam"
    bloco_deam = para_blocos(
        contexto,
        resp_cras,
        {"servicos": servicos_com_defensoria, "perfil": {}, "pergunta": "tem delegacia da mulher na ceilandia?"},
    )[0]
    assert bloco_deam["tipo_servico"] == "DEAM"
    assert all(s["tipo"] == "DEAM" for s in bloco_deam["servicos"])

    # 4. Tipo sem serviços disponíveis no alvo volta lista sem filtro (não exclui tudo)
    bloco_sem_especifico = para_blocos(
        contexto,
        resp_cras,
        {"servicos": servicos_com_defensoria, "perfil": {}, "pergunta": "tem hospital no gama?"},
    )[0]
    assert bloco_sem_especifico["tipo_servico"] == "Saúde"
    assert len(bloco_sem_especifico["servicos"]) > 0

    # 5. Texto legal de saúde não atribui à Lei 12.845/2013 dispensa de Boletim de Ocorrência
    t_saude = contexto.eval("Conversa.TEXTOS_FIXOS.saudeViolenciaSexual")
    t_saude_ajudando = contexto.eval("Conversa.TEXTOS_FIXOS.saudeViolenciaSexualAjudando")
    assert "Boletim de Ocorrência" not in t_saude
    assert "Boletim de Ocorrência" not in t_saude_ajudando
    assert "Lei 12.845/2013" in t_saude


def test_filtro_por_tipo_de_servico_no_fallback_sem_rede():
    js = carregar_conversa()
    resp = json.loads(json.dumps(POR_NOME["rede_com_ra"]["resposta"]))
    bloco = para_blocos(
        js,
        resp,
        {"servicos": SERVICOS_FICTICIOS, "perfil": {}, "pergunta": "onde fica a delegacia?"},
    )[0]
    assert bloco["tipo_servico"] == "DEAM"
    assert all(s["tipo"] == "DEAM" for s in bloco["servicos"])



