# Rede Lilás

Apoio a mulheres em situação ou risco de violência doméstica no Distrito Federal: reconhecer violações de direitos, avaliar o risco e encontrar benefícios e serviços de acolhimento. Definições em `docs/`, plano semanal em `ROADMAP.md` e mudanças em `openspec/changes/`.

## Preparar o ambiente

Requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

Na primeira execução, o modelo de embeddings `intfloat/multilingual-e5-base` (cerca de 1,1 GB) é baixado do Hugging Face para o cache local. Os embeddings rodam no próprio processo, sem serviço externo.

## Base jurídica (RAG)

16 normas federais e distritais, listadas em `dados/fontes/fontes.yaml`, cada uma com um eixo: `juridico`, `beneficios`, `saude` ou `df`.

| Pasta | Conteúdo |
|---|---|
| `dados/fontes/raw/` | HTML original de cada coleta, guardado byte a byte |
| `dados/fontes/dispositivos/` | dispositivos extraídos (`.jsonl`), por norma e data da coleta |
| `dados/fontes/relatorios/` | relatório de alterações de cada coleta |
| `dados/leis/` | trechos que alimentam o índice, um arquivo por norma |

Tudo é versionado. O índice não é gravado em disco: é montado em memória a partir de `dados/leis/` quando a aplicação inicia.

### Consultar

```bash
uv run python -m app.rag.buscar "ele quebrou minhas coisas, isso é violência?"
uv run python -m app.rag.buscar "tenho direito a auxílio-aluguel?" --eixo df --eixo beneficios -k 3
```

O número entre colchetes é a similaridade de cosseno (quanto maior, mais parecido). A orientação jurídica busca só no eixo `juridico`.

### Atualizar as normas

```bash
uv run python -m app.rag.coleta                      # baixa todas as normas de fontes.yaml
uv run python -m app.rag.coleta --norma <id> --arquivo pagina.html   # usa um HTML já baixado
uv run python -m app.rag.coleta --reprocessar        # relê o HTML salvo com o leitor atual, sem baixar
uv run python -m app.rag.ingestao                    # gera os trechos em dados/leis/
uv run pytest
```

A coleta não altera os trechos: revise `dados/fontes/relatorios/<data>.md` antes de rodar a ingestão. Para incluir uma norma, adicione-a a `fontes.yaml` (com `eixo`) e rode a coleta e a ingestão.
