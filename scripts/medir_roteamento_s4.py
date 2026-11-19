#!/usr/bin/env python3
"""Mede o roteamento S4 com a regra local e o modelo configurado no ambiente."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from app import config, llm, orquestrador

RAIZ = Path(__file__).resolve().parents[1]


class ClienteComVersao:
    """Usa o cliente oficial do projeto e registra o model id devolvido pela API."""

    def __init__(self, cliente: llm.ClienteLLM):
        self.cliente = cliente
        self.modelos_efetivos: set[str] = set()
        self.falhas: list[str] = []

    def responder(self, mensagens: list[dict], temperatura: float = 0.2) -> str:
        try:
            resposta = self.cliente._cliente.chat.completions.create(
                model=self.cliente.modelo,
                messages=mensagens,
                temperature=temperatura,
                **self.cliente._extra,
            )
        except llm.openai.APIError as erro:
            self.falhas.append(type(erro).__name__)
            raise llm.LLMIndisponivel(type(erro).__name__) from erro
        self.modelos_efetivos.add(resposta.model or self.cliente.modelo)
        texto = (resposta.choices[0].message.content or "").strip()
        if not texto:
            self.falhas.append("EmptyModelResponse")
            raise llm.LLMIndisponivel("resposta vazia")
        return texto


def medir() -> dict:
    conjunto = yaml.safe_load((RAIZ / "avaliacao/conjuntos/s4/roteamento.yaml").read_text(encoding="utf-8"))
    cfg = config.carregar()
    if cfg.base_url.rstrip("/") != "https://api.deepseek.com" or cfg.model != "deepseek-flash":
        raise ValueError("A rodada oficial exige LLM_BASE_URL=https://api.deepseek.com e LLM_MODEL=deepseek-flash")
    if cfg.thinking != "disabled":
        raise ValueError("A rodada oficial exige LLM_THINKING=disabled")
    cliente_base = llm.ClienteLLM(cfg)
    cliente = ClienteComVersao(cliente_base)
    resultados = []

    for caso in conjunto["casos"]:
        classificacao = orquestrador.classificar(caso["texto"], cliente)
        agente = classificacao.decisao.agente
        resultados.append({
            "id": caso["id"],
            "esperado": caso["agente_esperado"],
            "obtido": agente,
            "decidido_por": classificacao.decidido_por,
            "acertou": agente == caso["agente_esperado"],
            "tipo_esperado": caso.get("tipo_esperado"),
            "tipo_obtido": classificacao.decisao.tipo,
        })

    acertos = sum(item["acertou"] for item in resultados)
    por_etapa = {
        etapa: {
            "total": sum(item["decidido_por"] == etapa for item in resultados),
            "acertos": sum(item["acertou"] for item in resultados if item["decidido_por"] == etapa),
        }
        for etapa in ("regra", "llm", "reserva")
    }
    return {
        "data_hora_local": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
        "conjunto": "avaliacao/conjuntos/s4/roteamento.yaml",
        "modelo_solicitado": cliente_base.modelo,
        "modelos_efetivos": sorted(cliente.modelos_efetivos),
        "falhas_api": cliente.falhas,
        "temperatura": 0,
        "total": len(resultados),
        "acertos": acertos,
        "taxa_acerto": acertos / len(resultados) if resultados else 0,
        "erros": [item for item in resultados if not item["acertou"]],
        "por_etapa": por_etapa,
        "resultados": resultados,
    }


def main() -> int:
    resultado = medir()
    pasta = RAIZ / "avaliacao/rodadas/s4"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / "roteamento.yaml"
    arquivo.write_text(yaml.safe_dump(resultado, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Modelo solicitado: {resultado['modelo_solicitado']}")
    print(f"Modelos efetivos: {', '.join(resultado['modelos_efetivos']) or 'nenhuma resposta do modelo'}")
    print(f"Roteamento: {resultado['acertos']}/{resultado['total']} ({resultado['taxa_acerto']:.1%})")
    print(f"Resultados salvos em {arquivo.relative_to(RAIZ)}")
    if resultado["erros"]:
        print("Erros:")
        for erro in resultado["erros"]:
            print(f"  {erro['id']}: esperado={erro['esperado']}, obtido={erro['obtido']} ({erro['decidido_por']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
