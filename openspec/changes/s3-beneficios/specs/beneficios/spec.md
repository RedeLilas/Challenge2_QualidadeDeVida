# Spec Delta

## MODIFIED Requirements

### Requirement: Classificação de elegibilidade
Para cada benefício coberto, o sistema SHALL classificar o caso como "provável", "depende de decisão judicial", "não aplicável" ou "faltam informações", usando regras determinísticas escritas a partir do texto legal.

#### Scenario: Auxílio-aluguel da persona Juliana
- **WHEN** a usuária informa que quer sair de casa com os filhos e não tem renda fixa
- **THEN** o sistema classifica o auxílio-aluguel (Lei 14.674/2023) como "depende de decisão judicial" e explica que ele é concedido pelo juiz junto à medida protetiva

#### Scenario: Benefício não aplicável
- **WHEN** as respostas da usuária não atendem a um requisito obrigatório de um benefício
- **THEN** o sistema classifica o benefício como "não aplicável" e diz qual requisito não foi atendido

#### Scenario: Informação necessária não dada
- **WHEN** a usuária marca "prefiro não informar" ou não responde a um dado necessário para a regra
- **THEN** o sistema classifica o benefício como "faltam informações" e diz qual dado falta

### Requirement: O que falta e onde pedir
Para benefícios "prováveis" ou "dependentes de decisão judicial", o sistema SHALL listar os requisitos e documentos que faltam e orientar onde pedir no DF. Até a lista de CRAS existir (S4), o sistema MUST orientar a procurar o CRAS mais próximo.

#### Scenario: Falta inscrição no CadÚnico
- **WHEN** a usuária é provável beneficiária do Bolsa Família mas não está no CadÚnico
- **THEN** o sistema informa que o primeiro passo é a inscrição no CadÚnico e orienta a procurar o CRAS mais próximo

### Requirement: Consulta sem documentos pessoais
O sistema SHALL avaliar a elegibilidade sem pedir nome, CPF ou número de documento, usando o perfil e perguntando apenas o necessário para cada regra.

#### Scenario: Sem perfil preenchido
- **WHEN** a usuária não preencheu o perfil e abre Benefícios
- **THEN** o sistema pede o formulário de perfil antes de avaliar e não pede CPF

## ADDED Requirements

### Requirement: Regra do Bolsa Família
O sistema SHALL classificar o Bolsa Família como "provável" quando a renda familiar per capita for de até R$ 218 (Lei 14.601/2023, art. 5º, II).

#### Scenario: Renda dentro do limite
- **WHEN** a renda total informada dividida pelo número de pessoas é de R$ 218 ou menos
- **THEN** o Bolsa Família é "provável"

#### Scenario: Renda acima do limite
- **WHEN** a renda per capita é maior que R$ 218
- **THEN** o Bolsa Família é "não aplicável", e o sistema diz qual requisito não foi atendido

### Requirement: Regra do BPC
O sistema SHALL classificar o BPC como "provável" para pessoa com deficiência ou com 65 anos ou mais e renda per capita de até 1/4 do salário mínimo (Lei 8.742/1993, art. 20, § 3º), avisando sobre a avaliação da deficiência.

#### Scenario: Pessoa com deficiência
- **WHEN** a usuária informa deficiência e renda per capita dentro do limite
- **THEN** o BPC é "provável", com aviso de que a concessão depende da avaliação da deficiência

#### Scenario: Sem deficiência e com menos de 65 anos
- **WHEN** a usuária não tem deficiência e tem menos de 65 anos
- **THEN** o BPC é "não aplicável", e o sistema diz qual requisito não foi atendido

### Requirement: Regra do auxílio-aluguel
O sistema SHALL classificar o auxílio-aluguel sempre como "depende de decisão judicial" (Lei 11.340/2006, art. 23, VI, incluído pela Lei 14.674/2023).

#### Scenario: Qualquer perfil
- **WHEN** o sistema avalia o auxílio-aluguel, com qualquer resposta
- **THEN** o resultado é "depende de decisão judicial"

### Requirement: Regra do Aluguel Social do DF
O sistema SHALL avaliar o Aluguel Social exigindo moradia no DF, renda per capita de até 1/2 salário mínimo ou familiar de até 2, acompanhamento psicossocial e necessidade de saída emergencial ou de permanecer no imóvel alugado (Portaria SMDF 49/2026, arts. 2º e 5º).

#### Scenario: Com medida protetiva
- **WHEN** a usuária atende aos requisitos e tem medida protetiva
- **THEN** o Aluguel Social é "provável"

#### Scenario: Só com boletim
- **WHEN** a usuária atende aos requisitos, não tem medida protetiva e tem boletim de ocorrência
- **THEN** o Aluguel Social é "provável", com aviso de que a lei garante o acesso desde o boletim (Lei Distrital 6.623/2020, art. 1º, § 2º), mas o órgão ainda pode pedir a medida

#### Scenario: Sem medida e sem boletim
- **WHEN** a usuária não tem medida protetiva nem boletim de ocorrência
- **THEN** o resultado exibido é "não aplicável por enquanto", com o que falta para passar a se aplicar

#### Scenario: Moradia fora do DF
- **WHEN** a localização informada está fora do DF
- **THEN** o Aluguel Social é "não aplicável", e o sistema diz qual requisito não foi atendido

### Requirement: Renda calculada no aparelho
O sistema SHALL pedir a renda total aproximada e o número de pessoas e calcular a renda per capita no aparelho, considerando a casa como ficará sem o agressor. O sistema MUST avisar que o CadÚnico precisa refletir essa mudança.

#### Scenario: Casa sem o agressor
- **WHEN** a usuária informa a renda da casa sem o agressor
- **THEN** o cálculo usa esse valor e o resultado avisa que o CadÚnico precisa refletir a mudança

#### Scenario: Número de pessoas inválido
- **WHEN** o número de pessoas não é informado ou é menor que 1
- **THEN** as regras que dependem da renda per capita resultam em "faltam informações"

### Requirement: Avaliação só no navegador
A avaliação de benefícios SHALL rodar só no navegador, com regras em arquivo versionado. As respostas específicas MUST ficar só em memória e MUST NOT ser enviadas ao servidor ou ao LLM.

#### Scenario: Nada enviado
- **WHEN** a usuária conclui a avaliação de benefícios
- **THEN** nenhuma requisição contém as respostas

### Requirement: Salário mínimo versionado
O valor do salário mínimo SHALL ficar no arquivo de regras, com fonte e data de verificação, e as regras que o usam MUST exibir essa referência.

#### Scenario: Regra que usa o salário mínimo
- **WHEN** o sistema avalia o BPC ou o Aluguel Social
- **THEN** o resultado mostra a fonte e a data do valor usado
