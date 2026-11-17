# Spec Delta

## ADDED Requirements

### Requirement: Casos fictícios da S4
A equipe SHALL manter, em arquivos próprios em `avaliacao/conjuntos/s4/`, três conjuntos de casos fictícios: elegibilidade (20 a 30 perfis, com a situação esperada por benefício), triagem (respostas ao Fonar, com o nível esperado) e roteamento (cerca de 30 mensagens, com o agente esperado). Os arquivos da S3 MUST NOT ser alterados.

#### Scenario: Conjuntos presentes
- **WHEN** a validação dos conjuntos da S4 roda
- **THEN** ela encontra os três arquivos, e o de elegibilidade tem de 20 a 30 perfis

#### Scenario: Conjuntos da S3 intactos
- **WHEN** os conjuntos da S4 são criados
- **THEN** `avaliacao/conjuntos/desenvolvimento.yaml` e `avaliacao/conjuntos/oficial.yaml` ficam sem alteração

### Requirement: Gabarito com fonte e conferência
Cada caso de elegibilidade e de triagem SHALL citar a norma e o artigo (ou a portaria e o item) de onde vem o gabarito. Todo caso MUST registrar o autor e a conferência por uma pessoa da equipe diferente de quem o escreveu.

#### Scenario: Caso sem fonte
- **WHEN** um caso de elegibilidade ou de triagem não cita a norma e o artigo do gabarito
- **THEN** a validação do conjunto falha e identifica o caso

#### Scenario: Conferência pela mesma pessoa
- **WHEN** o revisor de um caso é a mesma pessoa que o escreveu, ou o revisor está vazio
- **THEN** a validação do conjunto falha

### Requirement: Casos de limite na elegibilidade
O conjunto de elegibilidade SHALL incluir casos de limite: renda per capita exatamente no corte, um real acima do corte, "prefiro não informar" num dado necessário e perfil incompleto.

#### Scenario: Cobertura dos limites
- **WHEN** a validação do conjunto de elegibilidade roda
- **THEN** ela confirma que existe ao menos um caso de cada tipo de limite

### Requirement: Roteamento com os pares que confundem
O conjunto de roteamento SHALL incluir os dois tipos de pergunta de benefícios ("tenho direito?" e "o que é?"), o par auxílio-aluguel (jurídico) e Aluguel Social do DF (benefícios), mensagens com mais de uma pergunta e mensagens fora do tema.

#### Scenario: Par do auxílio-aluguel
- **WHEN** o conjunto de roteamento é validado
- **THEN** ele contém "como funciona o aluguel da Maria da Penha?" com o agente jurídico esperado e uma pergunta sobre o Aluguel Social do DF com o agente de benefícios esperado

### Requirement: Medição das metas da S4 por regra
A acurácia de elegibilidade SHALL ser medida rodando a regra de benefícios do aparelho sobre os perfis e comparando cada situação com o gabarito. A sensibilidade para risco alto SHALL ser medida pela triagem e pela suíte de risco imediato. As duas medições MUST rodar sem LLM e sem corretor externo.

#### Scenario: Elegibilidade abaixo da meta
- **WHEN** menos de 90% dos pares perfil e benefício concordam com o gabarito
- **THEN** a medição aponta os casos divergentes e o relatório registra o valor, a causa provável e a ação

#### Scenario: Falso negativo de risco alto
- **WHEN** um caso de triagem com nível esperado alto resulta em nível menor, ou uma frase de risco da suíte não dispara o alerta
- **THEN** a medição falha, e a S4 não é dada como pronta

### Requirement: Relatório da S4
O relatório da S4 SHALL trazer a acurácia de elegibilidade, a sensibilidade para risco alto e, como evidência sem meta, a taxa de acerto do roteamento. Ele MUST declarar que os casos foram escritos com o Claude e conferidos por uma pessoa da equipe e que não houve corretor externo na S4.

#### Scenario: Relatório entregue
- **WHEN** o relatório da S4 é entregue
- **THEN** ele traz as três medidas, o número de casos, a data, a declaração sobre a autoria e a conferência dos casos, e a ausência de corretor externo
