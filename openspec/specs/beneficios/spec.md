# beneficios Specification

## Purpose
Mostrar à usuária quais benefícios federais e distritais provavelmente se aplicam ao caso dela, o que falta para acessá-los e onde pedir no DF, com regras auditáveis e sem criar falsas expectativas. Origem: RF03, RNF05.

## Requirements

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
O sistema SHALL avaliar a elegibilidade sem pedir nome, CPF ou número de documento, usando o perfil e perguntando apenas o necessário para cada regra.

#### Scenario: Sem perfil preenchido
- **WHEN** a usuária não preencheu o perfil e abre Benefícios
- **THEN** o sistema pede o formulário de perfil antes de avaliar e não pede CPF

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

### Requirement: Explicação de benefícios com citação
O sistema SHALL explicar o que é, como funciona e quem pode receber um benefício usando só trechos recuperados das normas de benefícios federais e distritais da base. Toda explicação MUST citar a norma e o artigo e mostrar a data da coleta da norma, com o aviso de que valores e regras podem mudar por decreto.

#### Scenario: Explicação do Cartão Gás
- **WHEN** a usuária pergunta "como funciona o auxílio do gás?"
- **THEN** a resposta explica o programa, cita a norma e o artigo usados e mostra a data da coleta da norma

#### Scenario: Valor citado
- **WHEN** a explicação menciona um valor em reais
- **THEN** a resposta mostra a data da coleta da norma e o aviso de que o valor pode ter mudado por decreto

### Requirement: Explicação nunca decide direito individual
A explicação de benefícios MUST NOT dizer se a usuária tem ou não direito a um benefício nem usar a expressão "direito garantido". Ela SHALL indicar a tela Benefícios para a avaliação com o perfil e o CRAS para o pedido.

#### Scenario: Explicação com requisitos
- **WHEN** a usuária pergunta "quem pode receber o bolsa família?"
- **THEN** a resposta descreve os requisitos da norma, sem dizer se ela atende a eles, e indica a tela Benefícios e o CRAS

### Requirement: Citação conferida nas normas de benefícios
Na explicação de benefícios, o sistema SHALL reconhecer cada norma de benefícios pelos nomes usuais, com e sem o ano, e aceitar a citação só quando o artigo citado for dessa norma entre os trechos recuperados. Se os trechos vierem de mais de uma norma, um artigo citado sem norma reconhecida MUST levar à recusa.

#### Scenario: LOAS citada sem o apelido do rótulo
- **WHEN** a resposta cita "(Lei 8.742/1993, art. 20)" e o art. 20 da LOAS está entre os trechos recuperados
- **THEN** a citação é aceita

#### Scenario: Lei distrital citada sem "Distrital"
- **WHEN** a resposta cita "(Lei 6.623, art. 1º)" e o art. 1º da Lei Distrital 6.623/2020 está entre os trechos recuperados
- **THEN** a citação é aceita

#### Scenario: Norma sem o ano com artigo de outra norma
- **WHEN** a resposta cita "(Decreto 42.376, art. 3º)" e o único art. 3º recuperado é da Lei 14.601/2023
- **THEN** a resposta é descartada e não é exibida

#### Scenario: Artigo sem norma com trechos de várias normas
- **WHEN** a resposta cita "art. 3º" sem nenhuma norma reconhecida perto e os trechos recuperados vêm de mais de uma norma
- **THEN** a resposta é descartada e não é exibida

#### Scenario: Jurídico sem mudança
- **WHEN** a mesma resposta com artigo sem norma é conferida pela orientação jurídica
- **THEN** o resultado é o mesmo de antes desta mudança

### Requirement: Recusa na explicação de benefícios
Quando os trechos recuperados não sustentarem a explicação, ou a pergunta for sobre benefício fora da base, o sistema SHALL dizer que não sabe explicar com segurança e indicar o CRAS e o Ligue 180, sem inventar conteúdo.

#### Scenario: Benefício fora da base
- **WHEN** a usuária pergunta "como saco meu fgts?"
- **THEN** o sistema recusa a explicação e indica o CRAS e o Ligue 180

#### Scenario: Similaridade abaixo do limite de benefícios
- **WHEN** o trecho mais parecido fica abaixo do limite calibrado para os eixos de benefícios
- **THEN** o sistema recusa sem chamar o LLM

### Requirement: Recuperação por benefício
Para cada benefício da base, a busca nos eixos de benefícios SHALL trazer a norma desse benefício entre os 5 primeiros trechos para as perguntas de teste dele.

#### Scenario: Aluguel Social do DF
- **WHEN** a pergunta de teste é "como funciona o aluguel social do DF?"
- **THEN** ao menos um dos 5 primeiros trechos é da Lei Distrital 6.623/2020, do Decreto Distrital 45.989/2024 ou da Portaria SMDF 49/2026

#### Scenario: Benefício sem a norma no top 5
- **WHEN** a pergunta de teste de um benefício não traz a norma dele entre os 5 primeiros
- **THEN** o teste de recuperação falha e aponta o benefício e os trechos recuperados
