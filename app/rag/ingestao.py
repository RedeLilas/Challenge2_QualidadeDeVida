"""Gera os trechos do índice em dados/leis/<norma_id>.jsonl a partir dos dispositivos coletados.

Lê a versão mais recente de cada norma em dados/fontes/dispositivos/ (gerada por
app.rag.coleta) e não baixa nada. Um trecho por artigo. Artigos longos (ex.: art. 22
da Lei Maria da Penha) são divididos por inciso ou parágrafo, e cada parte repete o
caput para manter a referência ao artigo. Só entram dispositivos vigentes: revogados
e vetados ficam de fora.

Uso: uv run python -m app.rag.ingestao [--norma lei-11340-2006]
"""
import argparse
import json
import sys
from itertools import groupby
from pathlib import Path

import yaml

from app.rag import planalto, versoes

PASTA_LEIS = Path(__file__).resolve().parents[2] / "dados" / "leis"
FONTES = versoes.FONTES / "fontes.yaml"
EIXOS = {"juridico", "beneficios", "saude", "df"}
LIMITE_CARACTERES = 1500


def _trecho(
    norma: dict,
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
        "id": f"{norma['id']}:{(unidade or caput).id}",
        "norma_id": norma["id"],
        "eixo": norma["eixo"],
        "lei": norma["citacao"],
        "urn": norma["urn"],
        "artigo": caput.artigo,
        "inciso": unidade.rotulo.rsplit(", ", 1)[1] if unidade and unidade.tipo == "inciso" else None,
        "paragrafo": unidade.rotulo.rsplit(", ", 1)[1] if unidade and unidade.tipo == "paragrafo" else None,
        "citacao": f"{norma['citacao']}, {rotulo}",
        "texto": "\n".join(linhas),
        "titulo": caput.titulo,
        "capitulo": caput.capitulo,
        "secao": caput.secao,
        "notas": notas,
        "url": f"{norma['url']}#{ancora}" if ancora else norma["url"],
        "data_acesso": data_acesso,
    }


def trechos(norma: dict, dispositivos: list[planalto.Dispositivo], data_acesso: str) -> list[dict]:
    saida = []
    for _, grupo in groupby(dispositivos, key=lambda d: d.artigo):
        grupo = list(grupo)
        caput, vigentes = grupo[0], [d for d in grupo if d.status == "vigente"]
        if not vigentes:
            continue
        if sum(len(d.texto) for d in vigentes) <= LIMITE_CARACTERES:
            saida.append(_trecho(norma, vigentes, caput, None, data_acesso))
            continue
        # Divide pelos filhos diretos do caput: "art22.inc_iii" agrupa "art22.inc_iii.ali_a".
        filhos = [d for d in vigentes if d is not caput]
        for _, unidade in groupby(filhos, key=lambda d: ".".join(d.id.split(".")[:2])):
            unidade = list(unidade)
            saida.append(_trecho(norma, unidade, caput, unidade[0], data_acesso))
    return saida


def dispositivo(registro: dict) -> planalto.Dispositivo:
    """Reconstrói o dispositivo a partir do registro gravado pela coleta."""
    _, _, ancora = registro["url_fonte"].partition("#")
    campos = planalto.Dispositivo.__dataclass_fields__.keys() - {"ancora"}
    return planalto.Dispositivo(**{c: registro[c] for c in campos}, ancora=ancora)


def carregar_normas(caminho: Path = FONTES) -> list[dict]:
    normas = yaml.safe_load(caminho.read_text(encoding="utf-8"))["normas"]
    for n in normas:
        if n.get("eixo") not in EIXOS:
            raise ValueError(f"{n['id']}: eixo {n.get('eixo')!r} inválido em fontes.yaml; use {sorted(EIXOS)}")
    return normas


def gerar(norma: dict) -> Path:
    processadas = versoes.versoes_processadas(norma["id"])
    if not processadas:
        raise FileNotFoundError(f"{norma['id']}: sem dispositivos coletados; rode app.rag.coleta antes.")
    registros = versoes.carregar(processadas[-1])
    saida = trechos(norma, [dispositivo(r) for r in registros], registros[0]["data_coleta"])

    PASTA_LEIS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_LEIS / f"{norma['id']}.jsonl"
    with caminho.open("w", encoding="utf-8", newline="\n") as f:
        for t in saida:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"{norma['id']}: {len(saida)} trechos de {len({t['artigo'] for t in saida})} artigos ({processadas[-1].name})")
    return caminho


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--norma", help="id da norma em fontes.yaml; padrão: todas")
    args = parser.parse_args()

    normas = carregar_normas()
    if args.norma:
        normas = [n for n in normas if n["id"] == args.norma]
        if not normas:
            sys.exit(f"Norma não encontrada em fontes.yaml: {args.norma}")
    for norma in normas:
        gerar(norma)

    if not args.norma:
        # Arquivos de normas que saíram de fontes.yaml não podem continuar no índice.
        esperados = {f"{n['id']}.jsonl" for n in normas}
        for sobra in sorted(p for p in PASTA_LEIS.glob("*.jsonl") if p.name not in esperados):
            print(f"Removendo {sobra.name}: a norma não está em fontes.yaml")
            sobra.unlink()


if __name__ == "__main__":
    main()
