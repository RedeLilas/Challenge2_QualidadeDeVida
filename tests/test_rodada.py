"""Script da rodada LLM x RAG (s3-avaliacao-llm-vs-rag, tarefa 3.2).

Índice e LLM simulados: nada chama o DeepSeek nem carrega o modelo de embeddings.
"""
import hashlib
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from app.rag.resposta import INSTRUCOES, INSTRUCOES_SEM_RAG, K, LIMITE_SIMILARIDADE
from conjuntos_ficticios import dados_ficticios
from scripts import rodada
from scripts.rodada import ErroRodada, congelar, rodar

AGORA = datetime(2026, 11, 12, 9, 30, tzinfo=timezone(timedelta(hours=-3)))
RESPOSTA_CITADA = "Pela lei, isso é uma forma de violência (Lei 11.340/2006, art. 7º)."
TRECHO = {
    "lei": "Lei 11.340/2006",
    "artigo": "7",
    "texto": "Art. 7º Texto fictício do dispositivo.",
    "url": "https://www.planalto.gov.br/exemplo.htm#art7",
    "data_acesso": "2026-11-03",
}


class IndiceFalso:
    def buscar(self, pergunta, k=5, eixos=None):
        return [(TRECHO, 0.9)]


class LLMFalso:
    modelo = "modelo-de-teste"

    def __init__(self):
        self.chamadas = []

    def responder(self, mensagens):
        self.chamadas.append(mensagens)
        return RESPOSTA_CITADA


@pytest.fixture
def pastas(tmp_path):
    conjuntos, rodadas = tmp_path / "conjuntos", tmp_path / "rodadas"
    conjuntos.mkdir()
    for tipo in ("desenvolvimento", "oficial"):
        (conjuntos / f"{tipo}.yaml").write_text(
            yaml.safe_dump(dados_ficticios(tipo), allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    return conjuntos, rodadas


def executar(pastas, tipo="desenvolvimento", cliente=None, **extra):
    conjuntos, rodadas = pastas
    return rodar(
        tipo,
        cliente=cliente or LLMFalso(),
        indice=IndiceFalso(),
        changelog="versão fictícia do changelog",
        raciocinio="disabled",
        pasta_conjuntos=conjuntos,
        pasta_rodadas=rodadas,
        agora=lambda: AGORA,
        **extra,
    )


def ler(caminho):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def test_grava_o_registro_completo(pastas):
    pasta = executar(pastas)
    registro = ler(pasta / "registro.yaml")

    assert pasta.name == "2026-11-12-desenvolvimento"
    assert registro["conjunto"] == "desenvolvimento"
    assert registro["sha256"] == hashlib.sha256((pastas[0] / "desenvolvimento.yaml").read_bytes()).hexdigest()
    assert registro["modelo"] == "modelo-de-teste"
    assert registro["raciocinio"] == "disabled"
    assert registro["changelog"] == "versão fictícia do changelog"
    assert registro["data"] == "2026-11-12"
    assert registro["inicio"] == registro["fim"] == AGORA.isoformat()
    assert registro["instrucoes"] == {"rag": INSTRUCOES, "sem_rag": INSTRUCOES_SEM_RAG}
    assert registro["rag"] == {"k": K, "limite_similaridade": LIMITE_SIMILARIDADE}
    assert registro["total"] == {"perguntas": 15, "extras": 10}


def test_gera_as_duas_versoes_de_cada_pergunta(pastas):
    llm = LLMFalso()
    respostas = ler(executar(pastas, cliente=llm) / "respostas.yaml")

    assert len(respostas) == 25
    assert [r["tipo"] for r in respostas] == ["pergunta"] * 15 + ["extra"] * 10
    primeira = respostas[0]
    assert primeira["id"] == "q-001" and primeira["pergunta"].startswith("Pergunta fictícia 1")
    assert primeira["rag"] == {
        "resposta": RESPOSTA_CITADA,
        "recusada": False,
        "citacoes": ["Lei 11.340/2006, art. 7º"],
    }
    assert primeira["sem_rag"] == {"resposta": RESPOSTA_CITADA}
    # Uma chamada por versão, com as instruções de cada uma e o mesmo modelo.
    assert len(llm.chamadas) == 50
    assert {c[0]["content"] for c in llm.chamadas} == {INSTRUCOES, INSTRUCOES_SEM_RAG}


def test_nao_sobrescreve_rodada_do_mesmo_dia(pastas):
    primeira, segunda = executar(pastas), executar(pastas)
    assert segunda.name == "2026-11-12-desenvolvimento-2"
    assert (primeira / "registro.yaml").is_file()


def test_exige_a_versao_do_changelog(pastas):
    with pytest.raises(ErroRodada, match="changelog"):
        rodar("desenvolvimento", cliente=LLMFalso(), indice=IndiceFalso(), changelog="  ",
              pasta_conjuntos=pastas[0], pasta_rodadas=pastas[1])  # fmt: skip


def test_conjunto_invalido_nao_roda(pastas):
    arquivo = pastas[0] / "desenvolvimento.yaml"
    dados = ler(arquivo)
    dados["perguntas"].pop()
    arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    llm = LLMFalso()

    with pytest.raises(ErroRodada, match="esperadas 15"):
        executar(pastas, cliente=llm)
    assert llm.chamadas == [] and not pastas[1].exists()


def test_oficial_sem_congelamento_nao_roda(pastas):
    with pytest.raises(ErroRodada, match="congel"):
        executar(pastas, "oficial")


def test_oficial_congelado_roda_e_registra_o_congelamento(pastas):
    congelamento = ler(congelar(pastas[0], agora=lambda: AGORA))
    registro = ler(executar(pastas, "oficial") / "registro.yaml")

    assert congelamento["sha256"] == registro["sha256"]
    assert registro["congelamento"] == congelamento
    assert registro["total"] == {"perguntas": 30, "extras": 10}


def test_oficial_com_hash_divergente_nao_roda(pastas):
    congelar(pastas[0], agora=lambda: AGORA)
    arquivo = pastas[0] / "oficial.yaml"
    arquivo.write_text(arquivo.read_text(encoding="utf-8").replace("fictícia 1 ", "fictícia 1, ajustada, "),
                       encoding="utf-8")  # fmt: skip
    llm = LLMFalso()

    with pytest.raises(ErroRodada, match="diverge"):
        executar(pastas, "oficial", cliente=llm)
    assert llm.chamadas == [] and not pastas[1].exists()


def test_congelar_exige_conjunto_oficial_valido(pastas):
    arquivo = pastas[0] / "oficial.yaml"
    dados = ler(arquivo)
    del dados["perguntas"][0]["conferencia"]
    arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ErroRodada, match="conferencia"):
        congelar(pastas[0], agora=lambda: AGORA)
    assert not (pastas[0] / rodada.ARQUIVO_CONGELAMENTO).exists()
