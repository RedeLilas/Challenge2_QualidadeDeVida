# Proposal

## Why

A base jurídica só traz os arts. 129, 147, 147-A e 147-B do Código Penal e não tem Código Civil nem CPC. A avaliação da S3 tem 9 perguntas do tipo "isso é crime?" e 2 sobre guarda, e recusa dentro do tema conta como erro. Sem ampliar a base antes de escrever as perguntas, a versão com RAG perderia pontos por falta de texto legal, e a correção de fidelidade não teria os artigos para conferir.

Métricas do ROADMAP afetadas: precisão jurídica (≥ 90%) e fidelidade às fontes (100% citadas, ≤ 5% sem suporte), medidas na S3.

## What Changes

- Ampliar o Código Penal com os arts. 121-A, 138, 139, 140, 148, 163, 181, 182, 183, 213, 215-A e 218-C.
- Incluir guarda: Código Civil art. 1.584 e CPC art. 699-A (Lei 14.713/2023).
- Corrigir a leitura de artigos com separador de milhar, hoje lidos como "artigo 1", na coleta e na verificação de citação, com testes.
- Reconhecer as novas normas na verificação de citação.
- Rodar de novo o teste rápido e recalibrar o limite de similaridade (hoje 0,81) só com as perguntas de desenvolvimento.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `orientacao-juridica`: acrescenta a cobertura penal e de guarda da base legal e a citação correta de artigos com separador de milhar.

## Impact

- **Código:** `app/rag/planalto.py`, `app/rag/resposta.py`, `tests/test_ingestao.py`, `tests/test_juridico.py`, `tests/test_indice.py`.
- **Dados:** `dados/fontes/fontes.yaml`, `dados/fontes/raw/`, `dados/fontes/dispositivos/`, `dados/fontes/relatorios/`, `dados/leis/`.
- **Documentos:** `README.md` (quantidade de normas).
- **Depende de:** `s3-avaliacao-llm-vs-rag` para as perguntas de desenvolvimento usadas na recalibração.
- **Privacidade (LGPD):** só texto legal público entra na base. Nenhum dado pessoal é coletado ou enviado.
- **Segurança da usuária:** a checagem de risco continua antes do índice e do LLM. Uma base maior reduz recusas em perguntas sobre crimes, sem afrouxar a verificação de citação.
- **Fora desta mudança:** arts. 146 e 216-B do Código Penal (opcionais), correção do `/juridico` quando o alerta dispara (S4), a avaliação em si (`s3-avaliacao-llm-vs-rag`).
