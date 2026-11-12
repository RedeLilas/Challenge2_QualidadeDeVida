"""Testes das regras e da avaliação da triagem baseada no Fonar (s3-triagem-fonar, tarefas 1.1 a 2.3)."""

import json
import re
from pathlib import Path

import pytest
import quickjs

RAIZ = Path(__file__).resolve().parents[1]
TEXTO_NOTAS = (RAIZ / "dados" / "fonar" / "notas.md").read_text(encoding="utf-8")
TEXTO_REGRAS = (RAIZ / "regras" / "triagem_fonar.json").read_text(encoding="utf-8")
ARQUIVO = json.loads(TEXTO_REGRAS)
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ORDEM_ESPERADA = ("1", "2", "5", "5.1", "11", "3", "4", "6", "9", "12", "13", "15", "22")
GATILHOS = ("1", "2", "5.1", "11")
ITENS_ATENCAO = ("3", "4", "6", "9", "12", "13", "15", "22")
EFEITOS_VALIDOS = {"alto", "atencao", "nenhum", "indeterminado"}


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
    contexto.eval((RAIZ / "web" / "triagem.js").read_text(encoding="utf-8"))
    contexto.eval(f"var REGRAS = {TEXTO_REGRAS};")
    return contexto


def avaliar_js(js, respostas):
    expr = f"JSON.stringify(Triagem.avaliar(REGRAS, {json.dumps(respostas)}))"
    return json.loads(js.eval(expr))


def respostas_todas_negativas():
    return {p["id"]: "nao" for p in ARQUIVO["perguntas"]}


# --- 1.1: registro da conferência de níveis oficiais em dados/fonar/notas.md --------------


def test_notas_fonar_registra_conferencia_de_niveis_oficiais_com_data_e_resposta():
    assert "Conferência de Níveis Oficiais de Risco no PDF do Fonar" in TEXTO_NOTAS
    assert re.search(r"Data da conferência:\*\*\s*`\d{4}-\d{2}-\d{2}`", TEXTO_NOTAS)
    assert "**Não.**" in TEXTO_NOTAS


# --- 2.1: estrutura, ordem e limite de 13 perguntas em regras/triagem_fonar.json ----------


def test_arquivo_tem_versao_fonte_e_13_perguntas_na_ordem_correta():
    assert DATA_ISO.fullmatch(ARQUIVO["versao"])
    assert "14.149/2021" in ARQUIVO["fonte"]["referencia"]
    assert "6/2025" in ARQUIVO["fonte"]["referencia"]
    assert DATA_ISO.fullmatch(ARQUIVO["fonte"]["data_verificacao"])

    perguntas = ARQUIVO["perguntas"]
    assert len(perguntas) <= 13
    assert len(perguntas) == 13
    ids = tuple(p["id"] for p in perguntas)
    numeros = tuple(p["numero"] for p in perguntas)
    assert ids == ORDEM_ESPERADA
    assert numeros == ORDEM_ESPERADA

    # Os 5 primeiros itens são a etapa dos gatilhos (1, 2, 5, 5.1 e 11) e os 8 seguintes são de atenção.
    assert [p["tipo"] for p in perguntas[:5]] == ["gatilho"] * 5
    assert [p["tipo"] for p in perguntas[5:]] == ["atencao"] * 8

    # Todos os números devem existir em dados/fonar/notas.md.
    for numero in numeros:
        assert f"| **{numero}** |" in TEXTO_NOTAS


@pytest.mark.parametrize("pergunta", ARQUIVO["perguntas"], ids=lambda p: p["id"])
def test_opcoes_e_efeitos_de_cada_pergunta(pergunta):
    assert isinstance(pergunta.get("enunciado"), str) and pergunta["enunciado"].strip()
    opcoes = pergunta.get("opcoes")
    assert isinstance(opcoes, list) and len(opcoes) >= 3
    for op in opcoes:
        assert isinstance(op.get("id"), str) and op["id"].strip()
        assert isinstance(op.get("rotulo"), str) and op["rotulo"].strip()
        assert op.get("efeito") in EFEITOS_VALIDOS


# --- 2.2: avaliação como função pura em QuickJS -------------------------------------------


@pytest.mark.parametrize(
    "id_gatilho, resposta_alta",
    [
        ("1", "sim_arma_fogo"),
        ("1", "sim_faca"),
        ("2", "sim"),
        ("2", "enforcamento"),
        ("5.1", "sim"),
        ("11", "sim"),
    ],
)
def test_cada_gatilho_confirma_risco_alto_e_encerra_no_primeiro_gatilho(js, id_gatilho, resposta_alta):
    # Preenche com "nao" apenas as perguntas anteriores ao gatilho testado (no caso de 5.1, "5" abre o 5.1)
    respostas = {}
    for p in ARQUIVO["perguntas"]:
        if p["id"] == id_gatilho:
            respostas[p["id"]] = resposta_alta
            break
        respostas[p["id"]] = "sim_ocorrencia_e_medida" if p["id"] == "5" else "nao"

    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["encerrada_antecipadamente"] is True
    assert estado["gatilho_acionado"] == id_gatilho
    assert estado["proxima_pergunta"] is None
    assert estado["nivel"] == "alto"
    assert estado["resultado"]["nivel"] == "alto"
    assert "190" in estado["resultado"]["orientacao"]
    assert "medida protetiva" in estado["resultado"]["orientacao"].lower()


@pytest.mark.parametrize("id_gatilho", GATILHOS)
@pytest.mark.parametrize("resposta_incerta", ["pular", "nao_sei", "Não sei", "Prefiro não responder"])
def test_pulo_e_nao_sei_em_cada_gatilho_resulta_em_alto_nao_descartado(js, id_gatilho, resposta_incerta):
    respostas = respostas_todas_negativas()
    if id_gatilho == "5.1":
        respostas["5"] = "sim_ocorrencia_e_medida"
    respostas[id_gatilho] = resposta_incerta

    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["nivel"] == "alto_nao_descartado"
    assert estado["resultado"]["rotulo"] == "Não foi possível descartar risco alto"
    assert "190" in estado["resultado"]["orientacao"]
    assert "medida protetiva" in estado["resultado"]["orientacao"].lower()


def test_gatilho_confirmado_depois_de_pulo_ainda_resulta_em_alto(js):
    respostas = {"1": "pular", "2": "enforcamento"}
    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["encerrada_antecipadamente"] is True
    assert estado["gatilho_acionado"] == "2"
    assert estado["nivel"] == "alto"


def test_item_5_1_so_deixa_de_ser_perguntado_quando_nunca_registrou_nem_pediu_medida(js):
    # Quando responde "nao" no item 5, pula direto para o 11 sem perguntar 5.1
    passo_sem_5_1 = avaliar_js(js, {"1": "nao", "2": "nao", "5": "nao"})
    assert passo_sem_5_1["concluida"] is False
    assert passo_sem_5_1["proxima_pergunta"]["id"] == "11"

    # Se pular ou disser "nao_sei" no item 5, o 5.1 é perguntado
    for resp_5 in ("pular", "nao_sei", "sim_apenas_ocorrencia"):
        passo_com_5_1 = avaliar_js(js, {"1": "nao", "2": "nao", "5": resp_5})
        assert passo_com_5_1["concluida"] is False
        assert passo_com_5_1["proxima_pergunta"]["id"] == "5.1"


def test_ameaca_de_outra_forma_no_item_1_resulta_em_atencao(js):
    respostas = respostas_todas_negativas()
    respostas["1"] = "sim_outra_forma"
    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["nivel"] == "atencao"


@pytest.mark.parametrize(
    "id_atencao, resposta_afirmativa",
    [
        ("3", "sim"),
        ("4", "perseguicao"),
        ("4", ["proibiu_visitas", "bloqueio_patrimonial"]),
        ("6", "sim"),
        ("9", "sim_falou"),
        ("12", "sim_animais"),
        ("13", "sim_manifestei"),
        ("15", "sim_anterior"),
        ("22", "sim"),
    ],
)
def test_resposta_afirmativa_em_pergunta_de_atencao_resulta_em_atencao(js, id_atencao, resposta_afirmativa):
    respostas = respostas_todas_negativas()
    respostas[id_atencao] = resposta_afirmativa
    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["nivel"] == "atencao"
    assert estado["resultado"]["rotulo"] == "Atenção"


@pytest.mark.parametrize("id_atencao", ITENS_ATENCAO)
@pytest.mark.parametrize("resposta_incerta", ["pular", "nao_sei"])
def test_pulo_ou_nao_sei_em_pergunta_de_atencao_resulta_em_atencao(js, id_atencao, resposta_incerta):
    respostas = respostas_todas_negativas()
    respostas[id_atencao] = resposta_incerta
    estado = avaliar_js(js, respostas)
    assert estado["concluida"] is True
    assert estado["nivel"] == "atencao"


def test_todas_negativas_resulta_em_sem_sinais_graves(js):
    estado = avaliar_js(js, respostas_todas_negativas())
    assert estado["concluida"] is True
    assert estado["nivel"] == "sem_sinais_graves"
    assert estado["resultado"]["rotulo"] == "Sem sinais graves"


# --- 2.3: ausência de "risco baixo", aviso de limite e Ligue 180 em todo resultado --------


@pytest.mark.parametrize("chave", ("alto", "alto_nao_descartado", "atencao", "sem_sinais_graves"))
def test_todos_os_resultados_tem_aviso_de_limite_e_180_e_nenhum_usa_risco_baixo(chave):
    res = ARQUIVO["resultados"][chave]
    assert "profissional" in res["aviso_limite"].lower()
    assert "não substitui" in res["aviso_limite"].lower()
    assert "180" in res["telefone_orientacao"] or "180" in res["orientacao"]


def test_nenhum_texto_do_arquivo_ou_do_js_usa_risco_baixo(js):
    for texto in _coletar_textos(ARQUIVO):
        assert "risco baixo" not in texto.lower(), f"Expressão proibida em: {texto!r}"
        assert "baixo risco" not in texto.lower(), f"Expressão proibida em: {texto!r}"

    codigo_js = (RAIZ / "web" / "triagem.js").read_text(encoding="utf-8").lower()
    assert "risco baixo" not in codigo_js
    assert "baixo risco" not in codigo_js

