"""Snapshots das coletas e comparação entre versões.

Uma diferença de hash não prova alteração jurídica: mudança de HTML ou de
formatação também altera o hash. Por isso o relatório separa mudanças de
texto, de status e notas novas ("Redação dada pela Lei nº ..."), que são o
sinal mais forte de alteração legal. Toda mudança passa por revisão humana
antes de entrar no índice.
"""
import hashlib
import json
from pathlib import Path

FONTES = Path(__file__).resolve().parents[2] / "dados" / "fontes"
RAW = FONTES / "raw"
PROCESSADOS = FONTES / "dispositivos"
RELATORIOS = FONTES / "relatorios"


def hash_bytes(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def salvar_raw(norma_id: str, data: str, conteudo: bytes) -> Path:
    pasta = RAW / norma_id
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{data}_{hash_bytes(conteudo)[:12]}.html"
    caminho.write_bytes(conteudo)
    return caminho


def ultimo_raw(norma_id: str) -> Path | None:
    """HTML da coleta mais recente; o nome começa pela data da coleta (AAAA-MM-DD_hash.html)."""
    coletas = sorted((RAW / norma_id).glob("*.html"))
    return coletas[-1] if coletas else None


def versoes_processadas(norma_id: str) -> list[Path]:
    return sorted((PROCESSADOS / norma_id).glob("*.jsonl"))


def salvar_processado(norma_id: str, data: str, registros: list[dict]) -> Path:
    pasta = PROCESSADOS / norma_id
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{data}.jsonl"
    with caminho.open("w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return caminho


def carregar(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f]


def comparar(anteriores: list[dict], atuais: list[dict]) -> dict:
    antes = {r["id"]: r for r in anteriores}
    depois = {r["id"]: r for r in atuais}
    comuns = antes.keys() & depois.keys()
    return {
        "incluidos": sorted(depois.keys() - antes.keys()),
        "removidos": sorted(antes.keys() - depois.keys()),
        "texto_alterado": sorted(i for i in comuns if antes[i]["hash_conteudo"] != depois[i]["hash_conteudo"]),
        "status_alterado": sorted(i for i in comuns if antes[i]["status"] != depois[i]["status"]),
        "notas_novas": {
            i: sorted(set(depois[i]["notas"]) - set(antes[i]["notas"]))
            for i in comuns
            if set(depois[i]["notas"]) - set(antes[i]["notas"])
        },
    }


def escrever_relatorio(data: str, secoes: list[str]) -> Path:
    RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho = RELATORIOS / f"{data}.md"
    caminho.write_text(f"# Relatório de coleta — {data}\n\n" + "\n".join(secoes), encoding="utf-8", newline="\n")
    return caminho
