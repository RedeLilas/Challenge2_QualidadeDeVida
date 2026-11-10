# beneficios Specification

## Purpose
Mostrar à usuária quais benefícios federais e distritais provavelmente se aplicam ao caso dela, o que falta para acessá-los e onde pedir no DF, com regras auditáveis e sem criar falsas expectativas. Origem: RF03, RNF05.

## Requirements

### Requirement: Classificação de elegibilidade
Para cada benefício coberto, o sistema SHALL classificar o caso como "provável", "depende de decisão judicial" ou "não aplicável", usando regras determinísticas escritas a partir do texto legal.

#### Scenario: Auxílio-aluguel da persona Juliana
- **WHEN** a usuária informa que quer sair de casa com os filhos e não tem renda fixa
- **THEN** o sistema classifica o auxílio-aluguel (Lei 14.674/2023) como "depende de decisão judicial" e explica que ele é concedido pelo juiz junto à medida protetiva

#### Scenario: Benefício não aplicável
- **WHEN** as respostas da usuária não atendem a um requisito obrigatório de um benefício
- **THEN** o sistema classifica o benefício como "não aplicável" e diz qual requisito não foi atendido

### Requirement: O que falta e onde pedir
Para benefícios "prováveis" ou "dependentes de decisão judicial", o sistema SHALL listar os requisitos e documentos que faltam e o local de atendimento no DF (por exemplo, o CRAS da Região Administrativa informada).

#### Scenario: Falta inscrição no CadÚnico
- **WHEN** a usuária é provável beneficiária do Bolsa Família mas não está no CadÚnico
- **THEN** o sistema informa que o primeiro passo é a inscrição no CadÚnico e indica o CRAS da RA dela

### Requirement: Regras auditáveis com vigência
Cada regra de elegibilidade SHALL registrar a norma, o artigo, o início de vigência e a data da última verificação, e o sistema MUST exibir essa referência junto ao resultado.

#### Scenario: Consulta da fonte
- **WHEN** o sistema classifica um benefício
- **THEN** o resultado mostra a norma, o artigo e a data de verificação da regra usada

### Requirement: Distinção entre provável e confirmado
O sistema SHALL informar, em todo resultado, que a concessão depende da análise do órgão responsável e MUST NOT afirmar que a usuária "tem direito garantido".

#### Scenario: Resultado provável
- **WHEN** um benefício é classificado como "provável"
- **THEN** o texto exibido diz que a concessão depende do órgão e não usa a expressão "direito garantido"

### Requirement: Consulta sem documentos pessoais
O sistema SHALL avaliar a elegibilidade sem pedir nome, CPF ou número de documento, perguntando apenas o necessário para cada regra.

#### Scenario: Sem perfil preenchido
- **WHEN** a usuária não preencheu o perfil e pergunta sobre benefícios
- **THEN** o sistema faz apenas as perguntas exigidas pelas regras e não pede CPF
