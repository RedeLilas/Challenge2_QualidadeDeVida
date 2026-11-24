# Proposal

## Why

Em 03/11 o repositório ficou com duas bases jurídicas paralelas: a da raiz (`app/rag/` + `dados/leis/`), que segue `s2-rag-juridico` (só a Lei Maria da Penha, `multilingual-e5-base` em memória), e a de `backend/`, que coleta 16 normas federais e distritais mas indexa com `bge-m3` via Ollama e Chroma. A segunda não foi registrada em nenhum design e diverge da spec: usa banco vetorial (Non-Goal de `s2-rag-juridico`), exige o Ollama no deploy para embeddings (a stack prevê Ollama só como LLM de testes e um container único) e divide o texto por dispositivo, o que já tinha piorado o `e5-base` no teste rápido.

Medições de 04/11 com as 10 perguntas de `tests/perguntas_juridicas.yaml` (artigo esperado no top 5) mostram que o `bge-m3` não supera o `e5-base` em nenhum cenário. Esta mudança mantém o melhor de cada lado: a coleta das 16 normas do `backend/` e o índice da spec, numa estrutura só, e remove `backend/`.

Métricas do ROADMAP afetadas: precisão jurídica (≥ 90%) e fidelidade às fontes (100% citadas, ≤ 5% sem suporte), medidas na S3. A base ampliada é pré-requisito para os agentes de benefícios da S4.

## What Changes

- Move para a raiz a coleta versionada do `backend/` (HTML bruto, dispositivos por data, relatório de alterações) em `dados/fontes/` e `app/rag/`.
- Unifica o leitor do Planalto/SINJ-DF: junta a correção do `backend/` ("Art. 147 - Ameaçar" não é art. 147-A) com a da raiz ("(VETADO." sem parêntese).
- Generaliza a ingestão para todas as normas de `dados/fontes/fontes.yaml`, com a mesma divisão de `s2-rag-juridico` (até 1500 caracteres por artigo), gravando um arquivo por norma em `dados/leis/`.
- Acrescenta o campo `eixo` às normas e aos trechos, e um filtro opcional por eixo na busca.
- Porta a busca manual pelo terminal para o índice da raiz.
- **BREAKING (interno):** remove `backend/` (índice Chroma, `bge-m3` via Ollama, `requirements.txt`). O id dos trechos passa a ser `<norma_id>:<dispositivo>` e `dados/leis/lei_11340.jsonl` passa a se chamar `dados/leis/lei-11340-2006.jsonl`.

Requisitos implementados (specs da base): `orientacao-juridica` (Base legal versionada) e a parte de normas de `beneficios`, que passam a ter texto oficial na base.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. A mudança reorganiza a implementação de requisitos já definidos em `s1-definicoes-base`; o comportamento da rota jurídica continua o de `s2-rag-juridico`.

## Impact

- Código: `app/rag/` (planalto, ingestao, indice e os novos versoes, coleta, buscar), `tests/test_ingestao.py`, `tests/test_indice.py`.
- Dados: `dados/leis/` passa de 1 para 16 arquivos (cerca de 558 trechos); entra `dados/fontes/`.
- Dependências: nenhuma nova no `pyproject.toml`. O `chromadb` e o Ollama deixam de ser necessários para a base jurídica (o Ollama segue como LLM de testes).
- Memória do deploy: igual à de `s2-rag-juridico` (cerca de 1,4 GB do `e5-base`); a indexação na inicialização sobe para cerca de 20 s.
- `s2-rag-juridico`: a rota jurídica (tarefa 2.1) passa a buscar com o filtro do eixo jurídico.
- **Privacidade (LGPD):** só textos oficiais de normas públicas; nenhum dado pessoal. Os embeddings continuam locais, sem envio a serviço externo.
- **Segurança da usuária:** sem efeito direto. O filtro por eixo evita que a resposta jurídica seja fundamentada em normas de outro tema.
- **Fora desta mudança:** Lei 14.188/2021 (Sinal Vermelho), modelo atual do Fonar (PDF), o ID duplicado da Lei 14.601/2023, índice pré-calculado, roteamento automático de eixo pela pergunta (S4) e a avaliação com 50 perguntas (S3).
