# Spec Delta

## ADDED Requirements

### Requirement: Perguntas de desenvolvimento de benefícios
A equipe SHALL manter um conjunto de desenvolvimento de benefícios em arquivo próprio, separado de `avaliacao/conjuntos/desenvolvimento.yaml`, com perguntas fictícias em linguagem leiga e gabarito com norma e artigo tirados do texto em `dados/leis/`. Cada pergunta MUST registrar o autor e a conferência por outra pessoa da equipe.

#### Scenario: Pergunta sem norma no gabarito
- **WHEN** uma pergunta do conjunto não tem a norma e o artigo do gabarito
- **THEN** a validação do conjunto falha e identifica a pergunta

#### Scenario: Base da S3 intacta
- **WHEN** o conjunto de desenvolvimento de benefícios é criado
- **THEN** `avaliacao/conjuntos/desenvolvimento.yaml` fica sem alteração

### Requirement: Linguagem leiga e extras quase do tema
O conjunto de desenvolvimento de benefícios SHALL ter perguntas com apelidos, frases incompletas e erros de digitação, parte delas sem o nome oficial do programa. MUST ter extras quase do tema (imposto de renda, FGTS, seguro-desemprego, aposentadoria) e a pergunta "como funciona o aluguel da Maria da Penha?", marcada para o eixo jurídico.

#### Scenario: Cobertura da linguagem
- **WHEN** a validação do conjunto roda
- **THEN** ela confirma que há perguntas marcadas como sem o nome oficial, extras quase do tema e a pergunta do aluguel da Maria da Penha

### Requirement: Conjunto de medição separado da calibração
Se o RAG de benefícios for medido depois da S4, o conjunto da medição SHALL ser diferente do usado para calibrar o limite e MUST ser congelado antes da rodada, como na S3.

#### Scenario: Pergunta repetida na medição
- **WHEN** uma pergunta do conjunto de medição de benefícios também está no conjunto de desenvolvimento de benefícios
- **THEN** a validação do conjunto de medição falha
