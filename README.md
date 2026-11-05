# Rede Lilás

Apoio a mulheres em situação ou risco de violência doméstica no Distrito Federal: reconhecer violações de direitos, avaliar o risco e encontrar benefícios e serviços de acolhimento. Definições em `docs/`, plano semanal em `ROADMAP.md` e mudanças em `openspec/changes/`.

## Preparar o ambiente

Requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

Na primeira execução, o modelo de embeddings `intfloat/multilingual-e5-base` (cerca de 1,1 GB) é baixado do Hugging Face para o cache local. Os embeddings rodam no próprio processo, sem serviço externo.

## Rodar o servidor

O LLM é configurado por `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`. Nos testes locais usamos o [Ollama](https://ollama.com):

```bash
cp .env.example .env                 # .env não é versionado
ollama pull qwen2.5:7b-instruct
uv run --env-file .env uvicorn app.main:app --reload --no-access-log
curl localhost:8000/saude            # {"status":"ok"}
```

Sempre use `--no-access-log`: o access log do uvicorn grava a query string e o IP de quem acessa. O log da aplicação (`app/logs.py`) registra só método, rota, status, duração e tipo de erro.

Para conferir o LLM sem subir o servidor (só com perguntas fictícias):

```bash
uv run --env-file .env python -m app.llm "O que é violência patrimonial?"
```

`LLM_TIMEOUT` (opcional, padrão 30) é quantos segundos o servidor espera o LLM antes de responder que não consegue agora, sem tentar de novo. Se mudar, ajuste `TEMPO_LIMITE_MS` em `web/app.js` para um pouco acima desse valor: a tela precisa esperar mais que o servidor.

Para usar o DeepSeek, troque as três variáveis no `.env`; nenhum código muda. Em produção, só depois da decisão de LGPD (tarefa 4.2 de `s2-plataforma-base`).

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
