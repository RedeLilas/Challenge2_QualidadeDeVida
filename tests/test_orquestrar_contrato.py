"""Contrato do POST /orquestrar e respostas de exemplo (s4-orquestrador-agentes, tarefa 1.2)."""
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app import main, risco
from app.orquestrador import (
    FORA_DO_TEMA,
    RAS_DO_SITE,
    ErroOrquestrar,
    PedidoOrquestrar,
    RespostaOrquestrar,
)
from app.rag import resposta

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLOS = json.loads((Path(__file__).parent / "orquestrar_exemplos.json").read_text(encoding="utf-8"))["exemplos"]
POR_NOME = {e["nome"]: e for e in EXEMPLOS}


@pytest.mark.parametrize("exemplo", EXEMPLOS, ids=lambda e: e["nome"])
def test_exemplo_segue_o_contrato(exemplo):
    PedidoOrquestrar.model_validate(exemplo["pedido"])
    modelo = RespostaOrquestrar if exemplo["status"] == 200 else ErroOrquestrar
    modelo.model_validate(exemplo["resposta"])


@pytest.mark.parametrize("exemplo", [e for e in EXEMPLOS if e["status"] == 200], ids=lambda e: e["nome"])
def test_risco_dos_exemplos_bate_com_a_regra(exemplo):
    # Os textos de exemplo passam pela regra real: o alerta aparece só onde ela dispara.
    resultado = risco.avaliar(exemplo["pedido"]["texto"])
    corpo = exemplo["resposta"]
    assert corpo["risco_imediato"] == (resultado is not None)
    if resultado:
        assert corpo["categoria_risco"] == resultado["categoria"]
        assert corpo["alerta"] == risco.ALERTA
        # Sem alerta_visto, só o alerta; com alerta_visto, o agente responde.
        assert (corpo["agente"] is None) == (not exemplo["pedido"]["alerta_visto"])


def test_exemplos_cobrem_o_que_a_tarefa_pede():
    corpos = [e["resposta"] for e in EXEMPLOS if e["status"] == 200]
    assert {c["agente"] for c in corpos} >= {"juridico", "beneficios", "triagem", "rede", "fora_do_tema"}
    assert {c["tipo"] for c in corpos if c["agente"] == "beneficios"} == {"direito", "explicacao"}
    assert {c["decidido_por"] for c in corpos} == {"regra", "llm", "reserva", None}
    assert POR_NOME["alerta_sem_alerta_visto"]["resposta"]["agente"] is None
    assert POR_NOME["alerta_com_alerta_visto"]["resposta"]["agente"] is not None
    assert POR_NOME["varias_perguntas"]["resposta"]["outras_perguntas"]
    assert POR_NOME["excesso_de_perguntas"]["resposta"]["excedeu"]
    assert any(e["status"] == 503 for e in EXEMPLOS)


def test_textos_fixos_dos_exemplos_sao_os_do_servidor():
    assert POR_NOME["fora_do_tema"]["resposta"]["resposta"]["resposta"] == FORA_DO_TEMA
    assert POR_NOME["reserva"]["resposta"]["resposta"]["resposta"] == resposta.RECUSA
    assert POR_NOME["llm_indisponivel"]["resposta"]["erro"] == main.INDISPONIVEL


def test_fora_do_tema_indica_180_e_defensoria():
    assert "180" in FORA_DO_TEMA and "Defensoria Pública do DF" in FORA_DO_TEMA


@pytest.mark.parametrize("campo", ["perfil", "historico"])
def test_pedido_com_campo_a_mais_e_recusado(campo):
    with pytest.raises(ValidationError):
        PedidoOrquestrar.model_validate({"texto": "como peço medida protetiva?", campo: []})


def test_ras_do_contrato_sao_as_do_site():
    dados = (RAIZ / "web" / "dados.js").read_text(encoding="utf-8")
    bloco = re.search(r"var RAS_DF = \[(.*?)\];", dados, re.S)[1]
    ras_df = re.findall(r'"([^"]+)"', bloco)
    assert tuple(r for r in ras_df if r not in ("Outra RA do DF", "Prefiro não informar")) == RAS_DO_SITE


def test_beneficios_do_contrato_sao_os_das_regras():
    regras = json.loads((RAIZ / "regras" / "beneficios.json").read_text(encoding="utf-8"))
    ids = {r["id"] for r in regras["regras"]}
    for id_ in ids | {"outro"}:
        RespostaOrquestrar.model_validate(_beneficios_direito(id_))
    with pytest.raises(ValidationError):
        RespostaOrquestrar.model_validate(_beneficios_direito("cartao_gas"))


def _beneficios_direito(beneficio):
    corpo = json.loads(json.dumps(POR_NOME["beneficios_direito"]["resposta"]))
    corpo["campos"]["beneficio"] = beneficio
    return corpo


def _alterado(nome, **mudancas):
    corpo = json.loads(json.dumps(POR_NOME[nome]["resposta"]))
    corpo.update(mudancas)
    return corpo


@pytest.mark.parametrize(
    "corpo",
    [
        # RA fora da lista do site
        {**POR_NOME["rede_com_ra"]["resposta"], "campos": {"beneficio": None, "ra": "Sol Nascente", "violencia_sexual_recente": None}},
        # agente fora da lista fechada
        _alterado("juridico_por_regra", agente="saude"),
        # tipo fora de benefícios, ou benefícios sem tipo
        _alterado("juridico_por_regra", tipo="direito"),
        _alterado("beneficios_direito", tipo=None),
        # resposta onde o agente roda no aparelho, e falta de resposta onde ele roda no servidor
        _alterado("triagem", resposta=POR_NOME["juridico_por_regra"]["resposta"]["resposta"]),
        _alterado("juridico_por_regra", resposta=None),
        # só alerta, mas com agente ou resposta junto
        _alterado("alerta_sem_alerta_visto", decidido_por="regra"),
        _alterado("alerta_sem_alerta_visto", outras_perguntas=["Como peço medida protetiva?"]),
        # risco sem alerta, ou alerta sem risco
        _alterado("alerta_com_alerta_visto", alerta=None),
        _alterado("juridico_por_regra", alerta=risco.ALERTA),
        # mais de duas sugestões, ou excesso sem as duas sugestões
        _alterado("excesso_de_perguntas", outras_perguntas=["a?", "b?", "c?"]),
        _alterado("excesso_de_perguntas", outras_perguntas=["a?"]),
        # agente sem quem decidiu
        _alterado("juridico_por_regra", decidido_por=None),
        # campo a mais
        _alterado("juridico_por_regra", perfil={}),
    ],
)
def test_resposta_fora_do_contrato_e_recusada(corpo):
    with pytest.raises(ValidationError):
        RespostaOrquestrar.model_validate(corpo)
