"""Testes das regras versionadas e da avaliação de benefícios em QuickJS (s3-beneficios, tarefas 1.1 a 2.2)."""

import json
import re
from pathlib import Path

import pytest
import quickjs

RAIZ = Path(__file__).resolve().parents[1]
TEXTO_REGRAS = (RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8")
ARQUIVO = json.loads(TEXTO_REGRAS)
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CAMPOS_REGRA = ("id", "nome", "norma", "artigo", "inicio_vigencia", "data_verificacao", "onde_pedir")
IDS_ESPERADOS = ("bolsa_familia", "bpc", "auxilio_aluguel", "aluguel_social_df")
STATUS_VALIDOS = {"provavel", "depende_decisao_judicial", "nao_aplicavel", "faltam_informacoes"}
CHAVES_CONTRATO = {"id", "status", "rotulo", "motivos", "falta", "onde_pedir", "fontes", "aviso"}


def _coletar_textos(valor):
    """Percorre recursivamente dicionários e listas extraindo todas as strings."""
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
    contexto.eval((RAIZ / "web" / "beneficios.js").read_text(encoding="utf-8"))
    contexto.eval(f"var REGRAS = {TEXTO_REGRAS};")
    return contexto


def avaliar_todos(js, dados, especificas=None):
    if especificas is None:
        expr = f"JSON.stringify(Beneficios.avaliar(REGRAS, {json.dumps(dados)}))"
    else:
        expr = f"JSON.stringify(Beneficios.avaliar(REGRAS, {json.dumps(dados)}, {json.dumps(especificas)}))"
    resultados = json.loads(js.eval(expr))
    return {item["id"]: item for item in resultados}


def avaliar_um(js, id_beneficio, dados, especificas=None):
    if especificas is None:
        expr = f"JSON.stringify(Beneficios.avaliarBeneficio(REGRAS, {json.dumps(id_beneficio)}, {json.dumps(dados)}))"
    else:
        expr = (
            f"JSON.stringify(Beneficios.avaliarBeneficio(REGRAS, {json.dumps(id_beneficio)}, "
            f"{json.dumps(dados)}, {json.dumps(especificas)}))"
        )
    return json.loads(js.eval(expr))


# --- 1.1 e 1.2: estrutura de regras/beneficios.json --------------------------------------


def test_arquivo_tem_versao_e_salario_minimo_verificado():
    assert DATA_ISO.fullmatch(ARQUIVO["versao"])

    sm = ARQUIVO["salario_minimo"]
    assert isinstance(sm["valor"], (int, float)) and sm["valor"] > 0
    assert isinstance(sm["norma"], str) and sm["norma"].strip()
    assert isinstance(sm["fonte"], str) and sm["fonte"].strip()
    assert isinstance(sm["fonte_url"], str) and sm["fonte_url"].startswith("https://")
    assert DATA_ISO.fullmatch(sm["inicio_vigencia"])
    assert DATA_ISO.fullmatch(sm["data_verificacao"])

    verificacao = ARQUIVO["verificacao_valores"]
    assert verificacao["salario_minimo"]["valor_vigente"] == sm["valor"]
    assert DATA_ISO.fullmatch(verificacao["salario_minimo"]["data_verificacao"])
    assert verificacao["bolsa_familia_limite_per_capita"]["valor_vigente"] == 218.0
    assert isinstance(verificacao["bolsa_familia_limite_per_capita"]["reajustado"], bool)
    assert DATA_ISO.fullmatch(verificacao["bolsa_familia_limite_per_capita"]["data_verificacao"])


def test_quatro_regras_na_ordem_esperada():
    ids = tuple(r["id"] for r in ARQUIVO["regras"])
    assert ids == IDS_ESPERADOS


@pytest.mark.parametrize("regra", ARQUIVO["regras"], ids=lambda r: r.get("id", "?"))
def test_toda_regra_tem_norma_artigo_vigencia_verificacao_requisitos_e_textos(regra):
    for campo in CAMPOS_REGRA:
        assert isinstance(regra.get(campo), str) and regra[campo].strip(), f"campo vazio ou ausente: {campo}"
    assert DATA_ISO.fullmatch(regra["inicio_vigencia"]), f"inicio_vigencia inválido em {regra['id']}"
    assert DATA_ISO.fullmatch(regra["data_verificacao"]), f"data_verificacao inválida em {regra['id']}"
    assert isinstance(regra.get("requisitos"), dict) and regra["requisitos"]
    assert isinstance(regra.get("textos"), dict) and regra["textos"]
    for chave, texto in regra["textos"].items():
        assert isinstance(texto, str) and texto.strip(), f"texto vazio: {regra['id']}.{chave}"


def test_nenhum_texto_usa_direito_garantido():
    for texto in _coletar_textos(ARQUIVO):
        assert "direito garantido" not in texto.lower(), f"Expressão proibida encontrada em: {texto!r}"


# --- 2.1: cálculo de renda per capita e contrato de avaliação em QuickJS -----------------


@pytest.mark.parametrize(
    "renda_total, numero_pessoas, esperado",
    [
        (0, 3, 0.0),
        (436, 2, 218.0),
        ("654,00", "3", 218.0),
        (810.5, 2, 405.25),
        (500, 0, None),
        (500, -2, None),
        (500, 1.5, None),
        (500, None, None),
        (500, "prefiro_nao_informar", None),
        (None, 2, None),
        ("", 2, None),
        ("prefiro_nao_informar", 2, None),
        (-10, 2, None),
    ],
)
def test_calculo_renda_per_capita_quickjs(js, renda_total, numero_pessoas, esperado):
    expr = f"Beneficios.calcularRendaPerCapita({json.dumps(renda_total)}, {json.dumps(numero_pessoas)})"
    resultado = js.eval(expr)
    if esperado is None:
        assert resultado is None
    else:
        assert resultado == pytest.approx(esperado)


def test_contrato_do_design_e_ausencia_de_direito_garantido(js):
    # Caso fictício completo (persona Juliana com filhos no DF)
    perfil = {
        "ra": "Ceilândia",
        "renda_total": 0,
        "numero_pessoas": 3,
        "cadunico": False,
        "idade": 34,
        "medida_protetiva": True,
    }
    especificas = {
        "deficiencia": False,
        "boletim_ocorrencia": True,
        "acompanhamento_psicossocial": True,
        "necessidade_moradia": True,
    }
    por_id = avaliar_todos(js, perfil, especificas)
    assert tuple(por_id.keys()) == IDS_ESPERADOS

    for item in por_id.values():
        assert set(item.keys()) == CHAVES_CONTRATO
        assert item["status"] in STATUS_VALIDOS
        assert isinstance(item["rotulo"], str) and item["rotulo"].strip()
        assert isinstance(item["motivos"], list) and item["motivos"]
        assert isinstance(item["falta"], list)
        assert isinstance(item["onde_pedir"], str) and "CRAS" in item["onde_pedir"]
        assert isinstance(item["aviso"], str) and item["aviso"].strip()
        assert isinstance(item["fontes"], list) and item["fontes"]
        for fonte in item["fontes"]:
            assert {"norma", "artigo", "inicio_vigencia", "data_verificacao"} <= set(fonte.keys())
            assert DATA_ISO.fullmatch(fonte["inicio_vigencia"])
            assert DATA_ISO.fullmatch(fonte["data_verificacao"])
        for texto in _coletar_textos(item):
            assert "direito garantido" not in texto.lower()


@pytest.mark.parametrize("numero_pessoas_invalido", [0, -1, None, "", "prefiro_nao_informar"])
def test_numero_de_pessoas_invalido_gera_faltam_informacoes_nas_regras_de_renda(js, numero_pessoas_invalido):
    dados = {
        "ra": "Taguatinga",
        "renda_total": 300,
        "numero_pessoas": numero_pessoas_invalido,
        "cadunico": True,
        "idade": 70,
        "deficiencia": True,
        "medida_protetiva": True,
        "boletim_ocorrencia": True,
        "acompanhamento_psicossocial": True,
        "necessidade_moradia": True,
    }
    por_id = avaliar_todos(js, dados)
    assert por_id["bolsa_familia"]["status"] == "faltam_informacoes"
    assert por_id["bpc"]["status"] == "faltam_informacoes"
    assert por_id["aluguel_social_df"]["status"] == "faltam_informacoes"
    assert por_id["auxilio_aluguel"]["status"] == "depende_decisao_judicial"


@pytest.mark.parametrize("renda_ausente", [None, "", "prefiro_nao_informar"])
def test_renda_nao_informada_gera_faltam_informacoes(js, renda_ausente):
    dados = {
        "ra": "Samambaia",
        "renda_total": renda_ausente,
        "numero_pessoas": 2,
        "cadunico": True,
        "idade": 68,
        "deficiencia": False,
        "medida_protetiva": True,
        "acompanhamento_psicossocial": True,
        "necessidade_moradia": True,
    }
    por_id = avaliar_todos(js, dados)
    assert por_id["bolsa_familia"]["status"] == "faltam_informacoes"
    assert por_id["bpc"]["status"] == "faltam_informacoes"
    assert por_id["aluguel_social_df"]["status"] == "faltam_informacoes"


# --- 2.2: cobertura dos resultados de cada benefício -------------------------------------


def test_bolsa_familia_no_limite_sem_cadunico_e_acima_do_limite(js):
    # No limite exato (436 / 2 = R$ 218,00) e sem CadÚnico
    sem_cadunico = avaliar_um(
        js,
        "bolsa_familia",
        {"renda_total": 436, "numero_pessoas": 2, "cadunico": False},
    )
    assert sem_cadunico["status"] == "provavel"
    assert sem_cadunico["rotulo"] == "Provável"
    assert any("CadÚnico" in f and "CRAS" in f for f in sem_cadunico["falta"])
    assert "CRAS" in sem_cadunico["onde_pedir"]
    assert "sem o agressor" in sem_cadunico["aviso"]

    # Acima do limite (438 / 2 = R$ 219,00)
    acima = avaliar_um(
        js,
        "bolsa_familia",
        {"renda_total": 438, "numero_pessoas": 2, "cadunico": True},
    )
    assert acima["status"] == "nao_aplicavel"
    assert acima["rotulo"] == "Não aplicável"
    assert any("218" in m for m in acima["motivos"])


def test_bpc_por_deficiencia_por_idade_nao_aplicavel_e_fonte_salario_minimo(js):
    sm = ARQUIVO["salario_minimo"]["valor"]
    limite_bpc_2_pessoas = (sm * 0.25) * 2  # R$ 810,50 para 2 pessoas (R$ 405,25 per capita)

    # Pessoa com deficiência no limite de 1/4 SM
    por_deficiencia = avaliar_um(
        js,
        "bpc",
        {"renda_total": limite_bpc_2_pessoas, "numero_pessoas": 2, "idade": 30, "cadunico": False},
        {"deficiencia": True},
    )
    assert por_deficiencia["status"] == "provavel"
    assert "avaliação da deficiência" in por_deficiencia["aviso"]
    assert any(f["norma"] == ARQUIVO["salario_minimo"]["norma"] for f in por_deficiencia["fontes"])

    # Pessoa idosa (65 anos) sem deficiência no limite de 1/4 SM
    por_idade = avaliar_um(
        js,
        "bpc",
        {"renda_total": limite_bpc_2_pessoas, "numero_pessoas": 2, "idade": 65, "cadunico": True},
        {"deficiencia": False},
    )
    assert por_idade["status"] == "provavel"
    assert any("65 anos" in m for m in por_idade["motivos"])
    assert any(f["norma"] == ARQUIVO["salario_minimo"]["norma"] for f in por_idade["fontes"])

    # Sem deficiência e com menos de 65 anos -> não aplicável
    sem_requisito_pessoal = avaliar_um(
        js,
        "bpc",
        {"renda_total": 200, "numero_pessoas": 2, "idade": 64},
        {"deficiencia": False},
    )
    assert sem_requisito_pessoal["status"] == "nao_aplicavel"
    assert any("deficiência" in m and "65 anos" in m for m in sem_requisito_pessoal["motivos"])

    # Com deficiência mas renda acima de 1/4 SM -> não aplicável
    renda_acima = avaliar_um(
        js,
        "bpc",
        {"renda_total": limite_bpc_2_pessoas + 2, "numero_pessoas": 2, "idade": 66},
        {"deficiencia": True},
    )
    assert renda_acima["status"] == "nao_aplicavel"
    assert any("1/4 do salário mínimo" in m for m in renda_acima["motivos"])


@pytest.mark.parametrize(
    "perfil",
    [
        {"renda_total": 0, "numero_pessoas": 3, "medida_protetiva": False},
        {"renda_total": 5000, "numero_pessoas": 1, "medida_protetiva": True},
        {"renda_total": "prefiro_nao_informar", "numero_pessoas": "prefiro_nao_informar"},
    ],
)
def test_auxilio_aluguel_sempre_depende_de_decisao_judicial(js, perfil):
    resultado = avaliar_um(js, "auxilio_aluguel", perfil)
    assert resultado["status"] == "depende_decisao_judicial"
    assert resultado["rotulo"] == "Depende de decisão judicial"
    assert any("juiz" in m and "medida protetiva" in m for m in resultado["motivos"])
    assert any(f["norma"] == "Lei 11.340/2006" for f in resultado["fontes"])


def test_aluguel_social_df_com_medida_so_com_boletim_sem_nenhum_fora_df_e_sem_moradia(js):
    sm = ARQUIVO["salario_minimo"]["valor"]
    base_perfil = {
        "ra": "Ceilândia",
        "renda_total": sm,  # 2 pessoas -> 1/2 SM per capita (no limite)
        "numero_pessoas": 2,
        "cadunico": True,
        "medida_protetiva": True,
    }
    base_especificas = {
        "boletim_ocorrencia": False,
        "acompanhamento_psicossocial": True,
        "necessidade_moradia": True,
    }

    # 1. Com medida protetiva
    com_medida = avaliar_um(js, "aluguel_social_df", base_perfil, base_especificas)
    assert com_medida["status"] == "provavel"
    assert com_medida["rotulo"] == "Provável"
    assert any(f["norma"] == ARQUIVO["salario_minimo"]["norma"] for f in com_medida["fontes"])

    # 2. Só com boletim de ocorrência (sem medida protetiva)
    so_boletim = avaliar_um(
        js,
        "aluguel_social_df",
        {**base_perfil, "medida_protetiva": False},
        {**base_especificas, "boletim_ocorrencia": True},
    )
    assert so_boletim["status"] == "provavel"
    assert so_boletim["rotulo"] == "Provável"
    assert "Lei Distrital 6.623/2020" in so_boletim["aviso"]
    assert "boletim de ocorrência" in so_boletim["aviso"]
    assert "medida protetiva" in so_boletim["aviso"]
    assert any(f["norma"] == "Lei Distrital 6.623/2020" for f in so_boletim["fontes"])

    # 3. Sem medida protetiva e sem boletim de ocorrência -> "Não aplicável por enquanto"
    sem_medida_nem_boletim = avaliar_um(
        js,
        "aluguel_social_df",
        {**base_perfil, "medida_protetiva": False},
        {**base_especificas, "boletim_ocorrencia": False},
    )
    assert sem_medida_nem_boletim["status"] == "nao_aplicavel"
    assert sem_medida_nem_boletim["rotulo"] == "Não aplicável por enquanto"
    assert sem_medida_nem_boletim["falta"]

    # 4. Moradia fora do DF -> "Não aplicável"
    fora_df = avaliar_um(
        js,
        "aluguel_social_df",
        {**base_perfil, "localizacao": "fora_df"},
        base_especificas,
    )
    assert fora_df["status"] == "nao_aplicavel"
    assert fora_df["rotulo"] == "Não aplicável"
    assert any("Distrito Federal" in m for m in fora_df["motivos"])

    # 5. Sem necessidade de saída emergencial ou permanência em imóvel alugado -> "Não aplicável"
    sem_necessidade_moradia = avaliar_um(
        js,
        "aluguel_social_df",
        base_perfil,
        {**base_especificas, "necessidade_moradia": False},
    )
    assert sem_necessidade_moradia["status"] == "nao_aplicavel"
    assert sem_necessidade_moradia["rotulo"] == "Não aplicável"
    assert any("saída emergencial" in m or "imóvel alugado" in m for m in sem_necessidade_moradia["motivos"])

    # 6. Renda familiar acima de 2 SM e per capita acima de 1/2 SM -> "Não aplicável"
    renda_acima = avaliar_um(
        js,
        "aluguel_social_df",
        {**base_perfil, "renda_total": sm * 2 + 10, "numero_pessoas": 2},
        base_especificas,
    )
    assert renda_acima["status"] == "nao_aplicavel"
    assert renda_acima["rotulo"] == "Não aplicável"
    assert any("1/2 salário mínimo" in m for m in renda_acima["motivos"])
