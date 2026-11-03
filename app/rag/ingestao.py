"""Gera dados/leis/lei_11340.jsonl a partir do texto compilado no Planalto.

Um trecho por artigo. Artigos longos (ex.: art. 22) são divididos por inciso ou
parágrafo, e cada parte repete o caput para manter a referência ao artigo.
Só entram dispositivos vigentes: revogados e vetados ficam de fora.

Uso: uv run python -m app.rag.ingestao [--arquivo pagina.htm]
"""
import argparse
import json
from datetime import date
from itertools import groupby
from pathlib import Path

from app.rag import planalto

LEI = {
    "lei": "Lei 11.340/2006",
    "urn": "urn:lex:br:federal:lei:2006-08-07;11340",
    "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm",
}
ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "leis" / "lei_11340.jsonl"
LIMITE_CARACTERES = 1500


def _trecho(
    partes: list[planalto.Dispositivo],
    caput: planalto.Dispositivo,
    unidade: planalto.Dispositivo | None,
    data_acesso: str,
) -> dict:
    rotulo = unidade.rotulo if unidade else caput.rotulo
    notas = list(dict.fromkeys(n for d in partes for n in d.notas))
    ancora = next((d.ancora for d in partes if d.ancora), "")
    # O caput entra mesmo quando vetado, para o trecho dizer de qual artigo é.
    linhas = [caput.texto] + [d.texto for d in partes if d is not caput]
    return {
        "id": f"lei_11340-{(unidade or caput).id}",
        "lei": LEI["lei"],
        "urn": LEI["urn"],
        "artigo": caput.artigo,
        "inciso": unidade.rotulo.rsplit(", ", 1)[1] if unidade and unidade.tipo == "inciso" else None,
        "paragrafo": unidade.rotulo.rsplit(", ", 1)[1] if unidade and unidade.tipo == "paragrafo" else None,
        "citacao": f"{LEI['lei']}, {rotulo}",
        "texto": "\n".join(linhas),
        "titulo": caput.titulo,
        "capitulo": caput.capitulo,
        "secao": caput.secao,
        "notas": notas,
        "url": f"{LEI['url']}#{ancora}" if ancora else LEI["url"],
        "data_acesso": data_acesso,
    }


def trechos(dispositivos: list[planalto.Dispositivo], data_acesso: str) -> list[dict]:
    saida = []
    for _, grupo in groupby(dispositivos, key=lambda d: d.artigo):
        grupo = list(grupo)
        caput, vigentes = grupo[0], [d for d in grupo if d.status == "vigente"]
        if not vigentes:
            continue
        if sum(len(d.texto) for d in vigentes) <= LIMITE_CARACTERES:
            saida.append(_trecho(vigentes, caput, None, data_acesso))
            continue
        # Divide pelos filhos diretos do caput: "art22.inc_iii" agrupa "art22.inc_iii.ali_a".
        filhos = [d for d in vigentes if d is not caput]
        for _, unidade in groupby(filhos, key=lambda d: ".".join(d.id.split(".")[:2])):
            unidade = list(unidade)
            saida.append(_trecho(unidade, caput, unidade[0], data_acesso))
    return saida


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arquivo", type=Path, help="HTML já baixado, em vez de baixar do Planalto")
    args = parser.parse_args()

    conteudo = args.arquivo.read_bytes() if args.arquivo else planalto.baixar(LEI["url"])
    resultado = planalto.parse(planalto.decodificar(conteudo))
    registros = trechos(resultado.dispositivos, date.today().isoformat())

    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO.open("w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(registros)} trechos de {len({r['artigo'] for r in registros})} artigos -> {ARQUIVO}")
    if resultado.duplicados:
        print(f"Atenção, dispositivos duplicados: {', '.join(resultado.duplicados)}")
    print(f"{len(resultado.ignorados)} parágrafos não reconhecidos (cabeçalho, ementa, textos de outras leis):")
    for texto in resultado.ignorados:
        print(f"  - {texto[:120]}")


if __name__ == "__main__":
    main()
