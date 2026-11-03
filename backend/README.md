# Backend — base jurídica (RAG)

Coleta das normas listadas em `config/fontes.yaml`, segmentação por dispositivo e índice vetorial no Chroma.

## O que fica no repositório e o que é gerado localmente

| Pasta | Versionada? | Conteúdo |
|---|---|---|
| `data/raw/` | sim | HTML original de cada coleta |
| `data/processed/` | sim | dispositivos extraídos (`.jsonl`), por norma e data |
| `data/relatorios/` | sim | relatório de alterações de cada coleta |
| `data/chroma/` | **não** | índice vetorial, gerado em cada máquina a partir de `data/processed/` |

O índice do Chroma é tratado como artefato local: cada pessoa (e o deploy) o monta com `scripts/indexar.py`. Não é preciso baixar as leis de novo para isso.

## Preparar o ambiente

Requisitos: Python 3.12+ e [Ollama](https://ollama.com) rodando em `http://localhost:11434`.

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull bge-m3
```

Variáveis opcionais: `OLLAMA_URL` (padrão `http://localhost:11434`) e `EMBEDDING_MODEL` (padrão `bge-m3`).

## Montar o índice

```bash
.venv/bin/python scripts/indexar.py                       # todas as normas
.venv/bin/python scripts/indexar.py --norma lei-11340-2006  # só uma
```

Indexa a versão processada mais recente de cada norma, apenas os dispositivos vigentes, em `data/chroma/` (coleção `leis`).

## Conferir a recuperação

```bash
.venv/bin/python scripts/buscar.py "ele quebrou minhas coisas, isso é violência?" -k 5
```

O primeiro resultado esperado é a Lei 11.340/2006, art. 7º, IV (violência patrimonial).

## Atualizar as normas

```bash
.venv/bin/python scripts/ingerir.py                 # baixa todas as normas de fontes.yaml
.venv/bin/python scripts/ingerir.py --norma <id> --arquivo pagina.html  # usa um HTML já baixado
```

A ingestão não altera o índice. Revise `data/relatorios/<data>.md` e depois rode `scripts/indexar.py`.
