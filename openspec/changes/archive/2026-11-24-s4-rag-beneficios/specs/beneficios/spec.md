# Spec Delta

## ADDED Requirements

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
