# avaliacao Specification

## Purpose
Medir objetivamente a qualidade da Rede Lilás sem entrevistas nem dados reais: casos fictícios com gabarito e fonte, LLM juiz com revisão humana em amostra e teste de usabilidade com colegas. Origem: seção 8 (métricas de sucesso) das definições da Semana 1.

## Requirements

### Requirement: Conjunto de casos fictícios com fonte
A equipe SHALL manter um conjunto versionado de casos fictícios, cada um com a pergunta, a resposta esperada e a norma/artigo que a sustenta. O conjunto MUST NOT conter relatos reais de vítimas.

#### Scenario: Caso sem fonte
- **WHEN** um caso é adicionado sem a norma ou o artigo que sustenta a resposta esperada
- **THEN** a validação do conjunto falha

### Requirement: Julgamento por LLM juiz com revisão em dupla
As respostas SHALL ser julgadas por um LLM juiz com rubrica escrita. Duas pessoas da equipe MUST revisar de forma independente uma amostra de 20% dos julgamentos, e a concordância entre o juiz e a equipe MUST ser reportada.

#### Scenario: Divergência entre juiz e equipe
- **WHEN** a equipe discorda do LLM juiz em um caso da amostra
- **THEN** prevalece o julgamento da equipe e a divergência entra no cálculo de concordância

### Requirement: Metas de qualidade
O relatório de avaliação SHALL medir e comparar com as metas:

| Métrica | Meta |
| :--- | :--- |
| Precisão jurídica | ≥ 90% corretas |
| Fidelidade às fontes | 100% com citação; ≤ 5% de afirmações sem suporte |
| Acurácia de elegibilidade | ≥ 90% de concordância com o gabarito |
| Sensibilidade para risco alto | 100% (nenhum falso negativo), verificada por regra |
| Tempo até o 190 | ≤ 2 s |
| Usabilidade (SUS) | ≥ 70 |

#### Scenario: Meta não atingida
- **WHEN** uma métrica fica abaixo da meta
- **THEN** o relatório registra o valor obtido, a causa provável e a ação tomada ou o motivo para não agir

### Requirement: Comparação LLM x RAG
A avaliação SHALL comparar, com o mesmo conjunto de perguntas e o mesmo modelo de produção, as respostas do LLM sem RAG e com RAG.

#### Scenario: Relatório da S3
- **WHEN** a comparação é executada
- **THEN** o relatório mostra precisão e fidelidade às fontes das duas versões lado a lado

### Requirement: Usabilidade com colegas
O teste de usabilidade SHALL ser feito com colegas do curso, seguindo roteiros com casos fictícios e o questionário SUS anônimo, e MUST NOT pedir relatos pessoais.

#### Scenario: Sessão de teste
- **WHEN** uma colega participa do teste
- **THEN** ela segue um roteiro fictício, responde o SUS sem se identificar e nenhum relato pessoal é coletado

### Requirement: Limitação declarada
O relatório final SHALL declarar que a solução não foi validada por especialistas da rede de atendimento nem por usuárias reais.

#### Scenario: Relatório final
- **WHEN** o relatório final é entregue
- **THEN** ele contém uma seção de limitações com essa declaração
