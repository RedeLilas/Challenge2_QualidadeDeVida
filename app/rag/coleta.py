"""Coleta as normas de dados/fontes/fontes.yaml, segmenta por dispositivo e gera relatório de alterações.

Não altera os trechos do índice. Revise dados/fontes/relatorios/<data>.md e depois
rode app.rag.ingestao.

Uso: uv run python -m app.rag.coleta [--norma lei-11340-2006] [--arquivo pagina.htm]
"""
import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

from app.rag import planalto, versoes

FONTES = versoes.FONTES / "fontes.yaml"


def registros(norma: dict, resultado: planalto.ResultadoParse, data: str, hash_documento: str) -> list[dict]:
    saida = []
    for d in resultado.dispositivos:
        saida.append(
            {
                "id": d.id,
                "norma_id": norma["id"],
                "urn": norma["urn"],
                "norma": norma["titulo"],
                "citacao": f"{norma['citacao']}, {d.rotulo}",
                "artigo": d.artigo,
                "tipo": d.tipo,
                "rotulo": d.rotulo,
                "texto": d.texto,
                "contexto": d.contexto,
                "status": d.status,
                "notas": d.notas,
                "titulo": d.titulo,
                "capitulo": d.capitulo,
                "secao": d.secao,
                "url_fonte": f"{norma['url']}#{d.ancora}" if d.ancora else norma["url"],
                "data_coleta": data,
                "hash_conteudo": d.hash,
                "hash_documento": hash_documento,
            }
        )
    return saida


def secao_relatorio(norma: dict, novos: list[dict], anterior: Path | None, resultado: planalto.ResultadoParse) -> str:
    linhas = [f"## {norma['titulo']}", f"- URN: `{norma['urn']}`", f"- Dispositivos: {len(novos)}"]
    if resultado.duplicados:
        linhas.append(f"- **Atenção, IDs duplicados:** {', '.join(resultado.duplicados)}")

    if anterior is None:
        linhas.append("- Primeira coleta: sem versão anterior para comparar.")
    else:
        antigos = versoes.carregar(anterior)
        linhas.append(f"- Comparado com: `{anterior.name}`")
        if antigos and antigos[0]["hash_documento"] == novos[0]["hash_documento"]:
            linhas.append("- HTML idêntico à coleta anterior.")
        else:
            diff = versoes.comparar(antigos, novos)
            if not any(diff.values()):
                linhas.append("- HTML mudou, mas nenhum dispositivo mudou (provável mudança de formatação).")
            for chave, rotulo in [
                ("incluidos", "Incluídos"),
                ("removidos", "Removidos"),
                ("texto_alterado", "Texto alterado"),
                ("status_alterado", "Status alterado"),
            ]:
                if diff[chave]:
                    linhas.append(f"- **{rotulo}:** {', '.join(diff[chave])}")
            for i, notas in diff["notas_novas"].items():
                linhas.append(f"- **Nota nova em {i}:** {'; '.join(notas)}")

    linhas.append(f"\n### Parágrafos não reconhecidos ({len(resultado.ignorados)})")
    linhas += [f"- {t[:160]}" for t in resultado.ignorados]
    return "\n".join(linhas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--norma", help="id da norma em fontes.yaml; padrão: todas")
    parser.add_argument("--arquivo", type=Path, help="HTML já baixado, em vez de baixar (só com --norma)")
    args = parser.parse_args()

    normas = yaml.safe_load(FONTES.read_text(encoding="utf-8"))["normas"]
    if args.norma:
        normas = [n for n in normas if n["id"] == args.norma]
        if not normas:
            sys.exit(f"Norma não encontrada em fontes.yaml: {args.norma}")
    elif args.arquivo:
        sys.exit("--arquivo exige --norma")

    data = date.today().isoformat()
    secoes = []
    for norma in normas:
        print(f"Coletando {norma['id']}...")
        conteudo = args.arquivo.read_bytes() if args.arquivo else planalto.baixar(norma["url"])
        versoes.salvar_raw(norma["id"], data, conteudo)

        resultado = planalto.parse(planalto.decodificar(conteudo))
        if norma.get("artigos"):
            # Coleta parcial: os parágrafos não reconhecidos do resto da norma não interessam.
            resultado.dispositivos = [d for d in resultado.dispositivos if d.artigo in norma["artigos"]]
            resultado.duplicados = [i for i in resultado.duplicados if any(d.id == i for d in resultado.dispositivos)]
            resultado.ignorados = []
        if not resultado.dispositivos:
            sys.exit(f"Nenhum dispositivo extraído de {norma['id']}: verifique o HTML em dados/fontes/raw.")

        novos = registros(norma, resultado, data, versoes.hash_bytes(conteudo))
        anteriores = [v for v in versoes.versoes_processadas(norma["id"]) if v.stem != data]
        anterior = anteriores[-1] if anteriores else None

        caminho = versoes.salvar_processado(norma["id"], data, novos)
        secoes.append(secao_relatorio(norma, novos, anterior, resultado))
        print(f"  {len(novos)} dispositivos, {len(resultado.ignorados)} parágrafos ignorados -> {caminho}")

    relatorio = versoes.escrever_relatorio(data, secoes)
    print(f"Relatório: {relatorio}")


if __name__ == "__main__":
    main()
