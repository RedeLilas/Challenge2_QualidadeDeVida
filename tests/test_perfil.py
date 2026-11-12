"""Testes do perfil local da usuária e integração com benefícios em QuickJS (s3-frontend-e-perfil, tarefa 2.1)."""

import json
import re
from pathlib import Path

import pytest
import quickjs

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS_OBRIGATORIOS_SPEC = {
    "ra",
    "renda",
    "pessoas_casa",
    "cadunico",
    "inss",
    "filhos",
    "medida_protetiva",
    "idade",
    "estado_civil",
}


@pytest.fixture
def js():
    contexto = quickjs.Context()
    # Mock simples de localStorage em memória para testar leitura, escrita e remoção
    contexto.eval(
        """
        var _banco = {};
        var localStorage = {
          getItem: function (k) { return Object.prototype.hasOwnProperty.call(_banco, k) ? _banco[k] : null; },
          setItem: function (k, v) { _banco[k] = String(v); },
          removeItem: function (k) { delete _banco[k]; },
          _chaves: function () { return Object.keys(_banco); }
        };
        """
    )
    contexto.eval((RAIZ / "web" / "perfil.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "dados.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "beneficios.js").read_text(encoding="utf-8"))
    regras_json = (RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8")
    contexto.eval(f"var REGRAS = {regras_json};")
    return contexto


def test_chave_de_armazenamento_eh_unica_e_neutra(js):
    chave = js.eval("Perfil.CHAVE")
    assert isinstance(chave, str) and chave.strip()
    for termo_sensivel in ("violencia", "violência", "mulher", "denuncia", "denúncia", "lilas", "lilás", "rede", "agressor"):
        assert termo_sensivel not in chave.lower()


def test_formulario_cobre_todos_os_campos_da_spec_com_prefiro_nao_informar_e_sem_documentos(js):
    campos_perfil = set(json.loads(js.eval("JSON.stringify(Perfil.CAMPOS)")))
    assert CAMPOS_OBRIGATORIOS_SPEC <= campos_perfil

    etapas = json.loads(js.eval("JSON.stringify(DadosRedeLilas.ETAPAS_PERFIL)"))
    campos_etapas = {etapa["campo"] for etapa in etapas}
    assert CAMPOS_OBRIGATORIOS_SPEC <= campos_etapas

    for etapa in etapas:
        opcoes_lower = [op.lower() for op in etapa["opcoes"]]
        assert "prefiro não informar" in opcoes_lower, f"Campo {etapa['campo']} sem opção 'Prefiro não informar'"
        pergunta_lower = etapa["pergunta"].lower()
        assert "cpf" not in pergunta_lower
        assert "seu nome" not in pergunta_lower
        # Palavra inteira: "urgência" contém "rg" e não pede documento.
        assert not re.search(r"\brg\b", pergunta_lower)


def test_salvar_ler_e_apagar_usa_uma_unica_chave(js):
    perfil_exemplo = {
        "ra": "Ceilândia",
        "moradia": "Preciso sair de casa com urgência para me proteger",
        "renda": "Até R$ 600 por mês",
        "pessoas_casa": "3 pessoas",
        "filhos": "Sim, crianças de 0 a 6 anos",
        "idade": "30 a 59 anos",
        "estado_civil": "Casada ou em união estável",
        "cadunico": "Sim, está atualizado (nos últimos 2 anos)",
        "inss": "Trabalho com carteira assinada (CLT)",
        "medida_protetiva": "Sim, já tenho medida protetiva concedida pelo juiz",
    }
    js.eval(f"Perfil.salvar({json.dumps(perfil_exemplo)});")

    chaves = json.loads(js.eval("JSON.stringify(localStorage._chaves())"))
    assert chaves == [js.eval("Perfil.CHAVE")]

    lido = json.loads(js.eval("JSON.stringify(Perfil.ler())"))
    for campo, valor in perfil_exemplo.items():
        assert lido[campo] == valor
    assert js.eval("Perfil.completo(Perfil.ler())") is True

    # Apagar remove apenas a chave do perfil
    js.eval("localStorage.setItem('outra_chave_qualquer', '1');")
    vazio = json.loads(js.eval("JSON.stringify(Perfil.apagar())"))
    assert all(v == "" for v in vazio.values())
    assert js.eval("Perfil.completo(Perfil.ler())") is False
    assert json.loads(js.eval("JSON.stringify(localStorage._chaves())")) == ["outra_chave_qualquer"]


def test_prefiro_nao_informar_conta_como_preenchido_sem_inventar_valor(js):
    respostas = {campo: "Prefiro não informar" for campo in CAMPOS_OBRIGATORIOS_SPEC}
    js.eval(f"var salvo = Perfil.salvar({json.dumps(respostas)});")

    assert js.eval("Perfil.completo(salvo)") is True
    for campo in CAMPOS_OBRIGATORIOS_SPEC:
        assert js.eval(f"Perfil.valorUtil(salvo, {json.dumps(campo)})") is None

    # Na conversão para Beneficios.avaliar, nenhum valor numérico ou booleano é inventado
    entrada = json.loads(js.eval("JSON.stringify(Perfil.paraAvaliacaoBeneficios(salvo))"))
    for chave, valor in entrada.items():
        assert valor == "prefiro_nao_informar", f"Valor inventado em {chave}: {valor!r}"

    avaliacao = json.loads(
        js.eval("JSON.stringify(Beneficios.avaliar(REGRAS, Perfil.paraAvaliacaoBeneficios(salvo)))")
    )
    por_id = {b["id"]: b for b in avaliacao}
    assert por_id["bolsa_familia"]["status"] == "faltam_informacoes"
    assert por_id["bpc"]["status"] == "faltam_informacoes"
    assert por_id["aluguel_social_df"]["status"] == "faltam_informacoes"
    assert por_id["auxilio_aluguel"]["status"] == "depende_decisao_judicial"


def test_acima_de_dois_salarios_minimos_com_cinco_pessoas_reprova_criterio_de_renda(js):
    respostas = {
        "ra": "Ceilândia",
        "moradia": "Preciso sair de casa com urgência para me proteger",
        "renda": "Acima de 2 salários mínimos",
        "pessoas_casa": "5 ou mais pessoas",
        "filhos": "Não tenho filhos ou dependentes",
        "idade": "30 a 59 anos",
        "estado_civil": "Casada ou em união estável",
        "cadunico": "Sim, está atualizado (nos últimos 2 anos)",
        "inss": "Trabalho com carteira assinada (CLT)",
        "medida_protetiva": "Sim, já tenho medida protetiva concedida pelo juiz",
    }
    js.eval(f"var salvoRendaAlta = Perfil.salvar({json.dumps(respostas)});")
    avaliacao = json.loads(
        js.eval("JSON.stringify(Beneficios.avaliar(REGRAS, Perfil.paraAvaliacaoBeneficios(salvoRendaAlta)))")
    )
    por_id = {b["id"]: b for b in avaliacao}
    assert por_id["bolsa_familia"]["status"] == "nao_aplicavel"
    assert por_id["bpc"]["status"] == "nao_aplicavel"
    assert por_id["aluguel_social_df"]["status"] == "nao_aplicavel"


def test_mapeamento_explicito_de_cadunico_e_medida_protetiva(js):
    desatualizado = json.loads(
        js.eval(
            'JSON.stringify(Perfil.paraAvaliacaoBeneficios({ cadunico: "Sim, mas está desatualizado ou inclui o agressor", medida_protetiva: "Já pedi medida protetiva ou fiz Boletim de Ocorrência" }))'
        )
    )
    assert desatualizado["cadunico"] is False
    assert desatualizado["medida_protetiva"] is False

    nao_sei = json.loads(
        js.eval('JSON.stringify(Perfil.paraAvaliacaoBeneficios({ cadunico: "Não sei se tenho" }))')
    )
    assert nao_sei["cadunico"] == "prefiro_nao_informar"

