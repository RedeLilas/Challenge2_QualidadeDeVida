"""Medição do roteamento (s4-orquestrador-agentes, tarefa 5.7). Só LLM falso: nenhum provedor real."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from app.llm import LLMIndisponivel
from app.orquestrador import por_regra
from scripts.medir_roteamento import ARQUIVO_CASOS, ErroMedicao, _SemLLM, exigir_modelo_de_producao, medir

CASOS = yaml.safe_load(ARQUIVO_CASOS.read_text(encoding="utf-8"))["casos"]
POR_TEXTO = {c["texto"]: c for c in CASOS}


class LLMQueAcerta:
    """Devolve o gabarito do caso: mede a montagem do resultado, não o modelo."""

    modelo = "modelo-falso"

    def __init__(self, errar=()):
        self.errar, self.chamadas = set(errar), []

    def responder(self, mensagens, temperatura=0.2):
        texto = mensagens[1]["content"].removeprefix("Mensagem: ")
        self.chamadas.append({"texto": texto, "temperatura": temperatura})
        caso = POR_TEXTO[texto]
        agente = "fora_do_tema" if caso["id"] in self.errar else caso["agente_esperado"]
        tipo = None if agente != "beneficios" else caso["tipo_esperado"]
        item = {"agente": agente, "tipo": tipo, "pergunta": texto, "beneficio": None, "ra": None,
                "violencia_sexual_recente": None}  # fmt: skip
        return json.dumps({"perguntas": [item]}, ensure_ascii=False)


def relogio():
    t = [datetime(2026, 11, 19, 9, 0, tzinfo=timezone(timedelta(hours=-3)))]

    def agora():
        t[0] += timedelta(seconds=1)
        return t[0]

    return agora


def ler(pasta: Path):
    registro = yaml.safe_load((pasta / "registro.yaml").read_text(encoding="utf-8"))
    resultado = yaml.safe_load((pasta / "resultado.yaml").read_text(encoding="utf-8"))
    return registro, resultado


def test_medicao_grava_registro_e_taxa(tmp_path):
    llm = LLMQueAcerta()
    pasta = medir(cliente=llm, changelog="Versão-falsa (2026-11-01)", raciocinio="disabled",
                  pasta_rodadas=tmp_path, agora=relogio())  # fmt: skip
    registro, resultado = ler(pasta)

    assert pasta.name == "2026-11-19-roteamento"
    assert registro["modelo"] == "modelo-falso" and registro["changelog"] == "Versão-falsa (2026-11-01)"
    assert registro["raciocinio"] == "disabled" and registro["temperatura_classificacao"] == 0
    assert len(registro["sha256"]) == 64 and len(registro["regras_roteamento_sha256"]) == 64
    resumo = resultado["resumo"]
    assert resumo["casos"] == resumo["medidos"] == len(CASOS)
    assert resumo["acerto"] == {"acertos": len(CASOS), "total": len(CASOS), "taxa": 1.0}
    assert resumo["erros"] == []
    # A regra decide os casos dela sem chamar o modelo; os demais vão ao LLM com temperatura 0.
    assert set(resumo["por_quem_decidiu"]) == {"regra", "llm"}
    assert len(llm.chamadas) == resumo["por_quem_decidiu"]["llm"]["total"]
    assert all(c["temperatura"] == 0 for c in llm.chamadas)


def test_erro_do_modelo_aparece_nos_erros(tmp_path):
    # Um caso que a regra não decide (vai ao modelo) e cujo gabarito não é fora_do_tema.
    caso = next(c for c in CASOS if por_regra(c["texto"]) is None and c["agente_esperado"] != "fora_do_tema")
    pasta = medir(cliente=LLMQueAcerta(errar={caso["id"]}), changelog="x", pasta_rodadas=tmp_path, agora=relogio())
    _, resultado = ler(pasta)
    resumo = resultado["resumo"]
    assert resumo["erros"] == [{
        "id": caso["id"], "texto": caso["texto"],
        "esperado": {"agente": caso["agente_esperado"], "tipo": caso["tipo_esperado"]},
        "obtido": {"agente": "fora_do_tema", "tipo": None}, "decidido_por": "llm",
    }]  # fmt: skip
    assert resumo["acerto"]["acertos"] == len(CASOS) - 1


def test_llm_fora_do_ar_cai_na_reserva_e_conta(tmp_path):
    class LLMForaDoAr:
        modelo = "modelo-falso"

        def responder(self, mensagens, temperatura=0.2):
            raise LLMIndisponivel("APITimeoutError")

    _, resultado = ler(medir(cliente=LLMForaDoAr(), changelog="x", pasta_rodadas=tmp_path, agora=relogio()))
    resumo = resultado["resumo"]
    assert "reserva" in resumo["por_quem_decidiu"]
    assert all(e["decidido_por"] == "reserva" and e["obtido"]["agente"] == "juridico" for e in resumo["erros"])


def test_so_regra_nao_chama_o_modelo_e_marca_nao_medidos(tmp_path):
    pasta = medir(cliente=_SemLLM(), changelog=None, pasta_rodadas=tmp_path, agora=relogio())
    registro, resultado = ler(pasta)
    resumo = resultado["resumo"]
    assert pasta.name == "2026-11-19-roteamento-so-regra" and registro["so_regra"] is True
    assert registro["modelo"] is None and registro["changelog"] is None
    assert set(resumo["por_quem_decidiu"]) == {"regra"}
    assert resumo["medidos"] + resumo["nao_medidos"]["nao_medido_sem_llm"] == len(CASOS)


def test_sem_changelog_nao_roda(tmp_path):
    with pytest.raises(ErroMedicao, match="changelog"):
        medir(cliente=LLMQueAcerta(), changelog="  ", pasta_rodadas=tmp_path)


def test_texto_com_risco_nunca_vai_ao_modelo(tmp_path):
    conjunto = yaml.safe_load(ARQUIVO_CASOS.read_text(encoding="utf-8"))
    conjunto["casos"][0]["texto"] = "ele está aqui em casa com uma faca"
    arquivo = tmp_path / "roteamento.yaml"
    arquivo.write_text(yaml.safe_dump(conjunto, allow_unicode=True), encoding="utf-8")
    # O validador recusa o conjunto antes de qualquer chamada (primeira barreira).
    with pytest.raises(ErroMedicao, match="risco"):
        medir(cliente=LLMQueAcerta(), changelog="x", arquivo=arquivo, pasta_rodadas=tmp_path)


@pytest.mark.parametrize("base_url", ["http://localhost:11434/v1", "http://127.0.0.1:11434/v1"])
def test_modelo_local_e_recusado(base_url):
    with pytest.raises(ErroMedicao, match="modelo local"):
        exigir_modelo_de_producao(base_url, "qwen2.5:7b-instruct")


def test_modelo_de_producao_e_aceito():
    exigir_modelo_de_producao("https://api.deepseek.com/v1", "deepseek-flash")
