#!/usr/bin/env python3
"""Mede elegibilidade e risco alto da S4 com as regras locais em QuickJS."""

from __future__ import annotations

import json
from pathlib import Path

import quickjs
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def _ler_yaml(caminho: Path) -> dict:
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def _contexto(arquivo_js: str, arquivo_regras: str, preparar: str = "") -> quickjs.Context:
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / arquivo_js).read_text(encoding="utf-8"))
    regras = (RAIZ / "regras" / arquivo_regras).read_text(encoding="utf-8")
    contexto.eval(f"var REGRAS = {preparar}({regras});" if preparar else f"var REGRAS = {regras};")
    return contexto


def medir_elegibilidade(conjunto: dict, contexto: quickjs.Context) -> dict:
    beneficios = conjunto["beneficios"]
    divergencias = []
    total = acertos = 0
    por_beneficio = {beneficio: {"acertos": 0, "total": 0} for beneficio in beneficios}
    for caso in conjunto["casos"]:
        perfil = json.dumps(caso["perfil"], ensure_ascii=False)
        resultados = json.loads(contexto.eval(f"JSON.stringify(Beneficios.avaliar(REGRAS, {perfil}))"))
        por_id = {resultado["id"]: resultado["status"] for resultado in resultados}
        for beneficio in beneficios:
            esperado = caso["esperado"][beneficio]
            obtido = por_id.get(beneficio)
            total += 1
            por_beneficio[beneficio]["total"] += 1
            if obtido == esperado:
                acertos += 1
                por_beneficio[beneficio]["acertos"] += 1
            else:
                divergencias.append({"caso": caso["id"], "beneficio": beneficio, "esperado": esperado, "obtido": obtido})
    if not total:
        raise ValueError("Conjunto de elegibilidade sem pares perfil × benefício")
    return {"perfis": len(conjunto["casos"]), "pares": total, "acertos": acertos,
            "acuracia": acertos / total, "por_beneficio": por_beneficio, "divergencias": divergencias}


def medir_risco(conjunto: dict, frases: dict, triagem: quickjs.Context, risco: quickjs.Context) -> dict:
    divergencias_triagem = []
    falsos_negativos = []
    altos = 0
    for caso in conjunto["casos"]:
        respostas = json.dumps(caso["respostas"], ensure_ascii=False)
        estado = json.loads(triagem.eval(f"JSON.stringify(Triagem.avaliar(REGRAS, {respostas}))"))
        obtido = estado["nivel"]
        esperado = caso["nivel_esperado"]
        if esperado != obtido:
            divergencias_triagem.append({"caso": caso["id"], "esperado": esperado, "obtido": obtido})
        if esperado == "alto":
            altos += 1
            if obtido != "alto":
                falsos_negativos.append({"origem": "triagem", "caso": caso["id"], "obtido": obtido})
    falsos_positivos = []
    for indice, caso in enumerate(frases["risco"], start=1):
        frase = json.dumps(caso["frase"], ensure_ascii=False)
        if risco.eval(f"Risco.avaliar(REGRAS, {frase}) === null"):
            falsos_negativos.append({"origem": "risco_imediato", "caso": indice, "frase": caso["frase"]})
    for frase in frases["nao_risco"]:
        if not risco.eval(f"Risco.avaliar(REGRAS, {json.dumps(frase, ensure_ascii=False)}) === null"):
            falsos_positivos.append(frase)
    positivos = altos + len(frases["risco"])
    if not positivos:
        raise ValueError("Conjuntos sem casos positivos de risco alto")
    return {"casos_triagem": len(conjunto["casos"]), "casos_alto_triagem": altos,
            "frases_risco": len(frases["risco"]), "positivos": positivos,
            "sensibilidade": (positivos - len(falsos_negativos)) / positivos,
            "falsos_negativos": falsos_negativos, "falsos_positivos": falsos_positivos,
            "divergencias_triagem": divergencias_triagem}


def medir() -> dict:
    pasta = RAIZ / "avaliacao" / "conjuntos" / "s4"
    elegibilidade = _ler_yaml(pasta / "elegibilidade.yaml")
    triagem = _ler_yaml(pasta / "triagem.yaml")
    frases = _ler_yaml(RAIZ / "tests" / "casos_risco.yaml")
    return {
        "elegibilidade": medir_elegibilidade(elegibilidade, _contexto("beneficios.js", "beneficios.json")),
        "risco_alto": medir_risco(triagem, frases, _contexto("triagem.js", "triagem_fonar.json"),
                                 _contexto("risco.js", "risco_imediato.json", "Risco.compilar")),
        "conferencia_pendente": {
            nome: [caso["id"] for caso in dados["casos"] if caso.get("conferencia", {}).get("status") == "pendente"]
            for nome, dados in (("elegibilidade", elegibilidade), ("triagem", triagem))
        },
    }


def main() -> int:
    resultado = medir()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    elegibilidade = resultado["elegibilidade"]
    risco = resultado["risco_alto"]
    print(f"Acurácia de elegibilidade: {elegibilidade['acertos']}/{elegibilidade['pares']} "
          f"({elegibilidade['acuracia']:.1%}); meta ≥ 90%")
    print(f"Sensibilidade para risco alto: {risco['positivos'] - len(risco['falsos_negativos'])}/"
          f"{risco['positivos']} ({risco['sensibilidade']:.1%}); meta = 100%")
    return 1 if elegibilidade["acuracia"] < .9 or risco["falsos_negativos"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
