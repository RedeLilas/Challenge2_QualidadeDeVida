"""Medição do roteamento da S4 (s4-orquestrador-agentes, tarefa 5.7): evidência, sem meta no ROADMAP.

Roda os casos de avaliacao/conjuntos/s4/roteamento.yaml pela orquestração (app.orquestrador.classificar):
a regra decide sem LLM; os demais casos vão ao modelo de produção, com temperatura 0. Grava em
avaliacao/rodadas/s4/<data>-roteamento/ o registro (modelo, raciocínio, changelog, data e hash dos
arquivos usados) e o resultado (taxa de acerto, por quem decidiu e por agente, e os erros).

Os textos são fictícios. Um texto com sinal de risco imediato nunca é enviado ao LLM (o validador já
recusa esses casos; a checagem aqui é uma segunda barreira).

    uv run --env-file .env python -m scripts.medir_roteamento --changelog "<versão do changelog>"
    uv run python -m scripts.medir_roteamento --sem-llm      # só a regra, sem chamar o modelo
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml

from app import config, llm, orquestrador, risco
from scripts.validar_conjuntos import validar_roteamento_s4

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CASOS = RAIZ / "avaliacao" / "conjuntos" / "s4" / "roteamento.yaml"
PASTA_RODADAS = RAIZ / "avaliacao" / "rodadas" / "s4"


class ErroMedicao(RuntimeError):
    """A medição não pode rodar (conjunto inválido ou dados da rodada faltando)."""


class _SemLLM:
    """Usado com --sem-llm: qualquer chamada ao modelo vira 'não medido', em vez de cair na reserva."""

    modelo = None

    def responder(self, mensagens, **_opcoes):
        raise _NaoMedido


class _NaoMedido(Exception):
    pass


def _agora() -> datetime:
    return datetime.now().astimezone()


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _medir_caso(caso: dict, cliente) -> dict:
    esperado = {"agente": caso["agente_esperado"], "tipo": caso.get("tipo_esperado")}
    base = {"id": caso["id"], "texto": caso["texto"], "esperado": esperado}
    if risco.avaliar(caso["texto"]):
        # Segunda barreira: texto com sinal de risco nunca vai ao LLM.
        return {**base, "situacao": "bloqueado_por_risco", "acerto": None}
    try:
        resultado = orquestrador.classificar(caso["texto"], cliente)
    except _NaoMedido:
        return {**base, "situacao": "nao_medido_sem_llm", "acerto": None}
    obtido = {"agente": resultado.decisao.agente, "tipo": resultado.decisao.tipo}
    return {
        **base,
        "situacao": "medido",
        "decidido_por": resultado.decidido_por,
        "obtido": obtido,
        "acerto_agente": obtido["agente"] == esperado["agente"],
        "acerto": obtido == esperado,
        "outras_perguntas": resultado.outras_perguntas,
    }


def _taxa(acertos: int, total: int) -> dict:
    return {"acertos": acertos, "total": total, "taxa": round(acertos / total, 4) if total else None}


def resumir(casos: list[dict]) -> dict:
    """Taxas de acerto (agente e tipo; só agente), por quem decidiu e por agente esperado, e os erros."""
    medidos = [c for c in casos if c["situacao"] == "medido"]
    por_quem = Counter(c["decidido_por"] for c in medidos)
    por_agente = Counter(c["esperado"]["agente"] for c in medidos)
    return {
        "casos": len(casos),
        "medidos": len(medidos),
        "nao_medidos": Counter(c["situacao"] for c in casos if c["situacao"] != "medido"),
        "acerto": _taxa(sum(c["acerto"] for c in medidos), len(medidos)),
        "acerto_so_agente": _taxa(sum(c["acerto_agente"] for c in medidos), len(medidos)),
        "por_quem_decidiu": {
            quem: _taxa(sum(c["acerto"] for c in medidos if c["decidido_por"] == quem), n)
            for quem, n in sorted(por_quem.items())
        },
        "por_agente_esperado": {
            agente: _taxa(sum(c["acerto"] for c in medidos if c["esperado"]["agente"] == agente), n)
            for agente, n in sorted(por_agente.items())
        },
        "erros": [
            {"id": c["id"], "texto": c["texto"], "esperado": c["esperado"], "obtido": c["obtido"],
             "decidido_por": c["decidido_por"]}
            for c in medidos if not c["acerto"]
        ],  # fmt: skip
    }


def medir(
    *,
    cliente,
    changelog: str | None,
    raciocinio: str | None = None,
    arquivo: Path = ARQUIVO_CASOS,
    pasta_rodadas: Path = PASTA_RODADAS,
    agora: Callable[[], datetime] = _agora,
) -> Path:
    """Roda todos os casos e grava registro.yaml e resultado.yaml numa pasta nova; devolve a pasta."""
    sem_llm = isinstance(cliente, _SemLLM)
    if not sem_llm and not (changelog or "").strip():
        raise ErroMedicao("Informe a versão do changelog do modelo (--changelog).")
    if erros := validar_roteamento_s4(arquivo):
        raise ErroMedicao("Conjunto de roteamento inválido:\n" + "\n".join(erros))
    casos = yaml.safe_load(arquivo.read_text(encoding="utf-8"))["casos"]

    inicio = agora()
    # Caso a caso; se o provedor falhar, a classificação cai na reserva (jurídico), como na rota.
    medidos = [_medir_caso(caso, cliente) for caso in casos]
    fim = agora()

    registro = {
        "conjunto": "s4/roteamento",
        "arquivo": arquivo.name,
        "sha256": _sha256(arquivo),
        "regras_roteamento_sha256": _sha256(orquestrador.ARQUIVO_ROTEAMENTO),
        "modelo": None if sem_llm else cliente.modelo,
        "raciocinio": None if sem_llm else raciocinio,
        "changelog": None if sem_llm else changelog.strip(),
        "temperatura_classificacao": 0,
        "so_regra": sem_llm,
        "data": inicio.date().isoformat(),
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "instrucoes_classificacao": orquestrador.INSTRUCOES_CLASSIFICACAO,
    }
    resultado = {"resumo": resumir(medidos), "casos": medidos}
    resultado["resumo"]["nao_medidos"] = dict(resultado["resumo"]["nao_medidos"])

    destino = _nova_pasta(pasta_rodadas, f"{registro['data']}-roteamento" + ("-so-regra" if sem_llm else ""))
    for nome, dados in (("registro.yaml", registro), ("resultado.yaml", resultado)):
        (destino / nome).write_text(
            yaml.safe_dump(dados, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8"
        )
    return destino


def exigir_modelo_de_producao(base_url: str, modelo: str) -> None:
    """A tarefa 5.7 mede com o modelo de produção: recusa um .env que aponte para um modelo local (Ollama)."""
    host = (urlparse(base_url).hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith(".local"):
        raise ErroMedicao(
            f"O .env aponta para um modelo local ({modelo} em {host}). A medição do roteamento usa o modelo de "
            "produção (DeepSeek): ajuste LLM_BASE_URL e LLM_MODEL, ou use --sem-llm para medir só a regra."
        )


def _nova_pasta(pasta: Path, nome: str) -> Path:
    destino, n = pasta / nome, 2
    while destino.exists():
        destino, n = pasta / f"{nome}-{n}", n + 1
    destino.mkdir(parents=True)
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--changelog", help="versão do changelog do modelo no dia da medição")
    parser.add_argument("--sem-llm", action="store_true", help="mede só a regra, sem chamar o modelo")
    args = parser.parse_args()
    try:
        if args.sem_llm:
            pasta = medir(cliente=_SemLLM(), changelog=None)
        else:
            cfg = config.carregar()
            exigir_modelo_de_producao(cfg.base_url, cfg.model)
            pasta = medir(cliente=llm.ClienteLLM(cfg), changelog=args.changelog, raciocinio=cfg.thinking)
    except (ErroMedicao, config.ConfigIncompleta) as erro:
        print(erro)
        return 1
    resumo = yaml.safe_load((pasta / "resultado.yaml").read_text(encoding="utf-8"))["resumo"]
    print(f"Medição gravada em {pasta}")
    print(f"Acerto (agente e tipo): {resumo['acerto']}")
    print(f"Por quem decidiu: {resumo['por_quem_decidiu']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
